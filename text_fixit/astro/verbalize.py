#!/usr/bin/env python
"""
Stage 3 of ASTRO (arXiv:2507.00417 sec.2.4, "Procedure Cloning in Language"): turn a linearized
node sequence into the assistant turns an SFT example is trained on.

ASTRO'S CONSTRUCTION
--------------------
For each node n_t in the sequence, conditioned on the text so far:
  Case 1, n_t is a CHILD of n_{t-1}  -- rewrite the step as a continuation.
  Case 2, n_t is an ANCESTOR of n_{t-1} -- emit the hard-coded self-reflection
        "But wait, are we solving the problem correctly so far? Hmm..."
    then "I'm not sure if we're solving the problem correctly so far.",
    then a backtrack sentence ("Let's go back to where we ...") or, at the root,
         a restart sentence ("Let's restart our solution from the beginning ...").
  And "between intermediate nodes with high Q-values and immediately after the final node" the same
  reflection followed by "Our solution seems to be correct so far." -- so that the model learns to
  judge correctness AFTER reflecting rather than before.

The phrases are kept, retargeted from "solving the problem" to "repairing the object". ASTRO
few-shot-prompts Llama to write each step's prose; we TEMPLATE it, because every sentence here is
arithmetic over two measured error values and templating makes it verifiable and free. The
reflection markers are hard-coded in ASTRO too -- only the connective prose was model-written, and
in a two-sentence <think> block there is almost none of it.

CONTINUOUS ADAPTATION
---------------------
Every number a turn states is DERIVED FROM THE OBSERVATIONS, by the arithmetic the prompt gives the
model: e = E/1000 for the first probe, the sign flip when the error rises, and V*A/(A-B) to close
the remaining gap. A is always the BROKEN object's error, because the batch contract applies each
action fresh (see tree.build_tree). Nothing here reads instance["gt_fix"].

FORMAT
------
Turns are emitted in the grammar `action_parser.parse` already accepts and
`agents/qwen_vl._normalize` already normalises to:

    <think>...</think>[<backtrack/>]<act>SIMULATE TRANSLATE(P1, X, -0.19847)</act>

`<backtrack/>` is the tag Fixit_RL sec.3.3 defines and the parser has carried since Stage 1 -- it is
the explicit backtrack LABEL of ablation 4 in Fixit_RL sec.7, and the direct analogue of ASTRO's
backtracking phrase. It rides ALONGSIDE the natural-language reflection, not instead of it: the
ablation that mattered in ASTRO was the language, and the tag is what makes backtracks countable
for the Fixit_RL sec.7 metrics.
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from action_parser import _AXIS_INV                              # noqa: E402
from astro.linearize import BACKTRACK_PART, BACKTRACK_TRANSFORM  # noqa: E402
from astro.tree import LOCK_ON_DROP, SAME_ERROR_MM               # noqa: E402

# ASTRO's hard-coded markers (sec.2.4), retargeted to repair. Kept verbatim in shape -- the
# reflection is a QUESTION, the verdict comes after it, and the two are separate sentences.
REFLECT = "But wait, is this the right repair so far? Hmm..."
NEGATIVE = "This does not look like the right repair so far."
POSITIVE = "This looks like the right repair so far."
RESTART = "Let's restart the diagnosis from the beginning and reconsider which part is faulty."
GO_BACK = "Let's go back to where we chose the operation and axis for {pid}."

# The prompt's $found_note dictates the exact reply once a SIMULATE has passed. The commit turn must
# match it verbatim, or SFT teaches the model to ignore an instruction the harness still injects.
COMMIT_THINK = "A SIMULATE reported ALL PASS, so this is the repair."


def _n(x):
    """Errors are quoted to the nearest millimetre -- the precision the observation itself reports."""
    return f"{x:.0f} mm"


def _is_flip(prev, node):
    """Did `node` invert `prev`'s sign (or reciprocate its factor) within the same hypothesis?"""
    if prev is None or node.parent is not prev or node.cell != prev.cell:
        return False
    if node.op == "SCALE":
        return prev.value > 0 and abs(node.value * prev.value - 1.0) < 1e-6
    return abs(node.value + prev.value) < 1e-9


def _evidence(prev, dev0, faulty_pid):
    """One sentence stating what the previous probe measured. Observation-only."""
    if abs(prev.dev - dev0) <= SAME_ERROR_MM:
        who = ("that part is not the faulty one" if prev.pid != faulty_pid
               else "that operation and axis are not the fault")
        return f"{prev.call} left the error at {_n(prev.dev)}, exactly as before, so {who}."
    if prev.dev > dev0:
        ratio = prev.dev / dev0 if dev0 > 0 else 0
        tail = (" -- roughly double, which means the axis is right and the sign is wrong"
                if 1.7 <= ratio <= 2.4 else "")
        return f"{prev.call} raised the error from {_n(dev0)} to {_n(prev.dev)}{tail}."
    drop = 100.0 * (dev0 - prev.dev) / dev0 if dev0 > 0 else 0.0
    return (f"{prev.call} cut the error from {_n(dev0)} to {_n(prev.dev)}, "
            f"closing {drop:.0f}% of it.")


def _intent(prev, node, dev0):
    """One sentence stating what this turn tries, and where its number came from."""
    ax = _AXIS_INV[node.axis]
    if prev is None:
        # e = E/1000 is the prompt's derivation for a TRANSLATE probe only; quoting it before a
        # ROTATE or SCALE would show a number the action does not use.
        if node.op == "TRANSLATE":
            return (f"The object is off by {_n(dev0)} and nothing has been probed yet, so "
                    f"e = {dev0 / 1000:.5f} m and I will start with {node.call}.")
        return (f"The object is off by {_n(dev0)} and nothing has been probed yet. "
                f"I will start with {node.call}.")
    if _is_flip(prev, node):
        word = "reciprocal factor" if node.op == "SCALE" else "opposite sign"
        return f"I will try the {word} on the same axis: {node.call}."
    if node.parent is prev:
        gap = dev0 - prev.dev
        k = dev0 / gap if abs(gap) > 1e-9 else float("nan")
        return (f"Closing all of it needs about {prev.value:.4g} x {_n(dev0)} / {_n(gap)} "
                f"= {k:.2f} times that value, so I will try {node.call}.")
    return f"I will test {node.op} on axis {ax} next: {node.call}."


def _backtrack_sentence(kind, node):
    return RESTART if kind == BACKTRACK_PART else GO_BACK.format(pid=node.pid)


def verbalize(steps, dev0, faulty_pid):
    """Linearized steps -> the list of assistant turns for one training trace.

    Returns [{"node", "think", "backtrack", "mode", "call", "text"}], ending with a COMMIT turn on
    the passing node. Every SIMULATE turn corresponds to one env.step; the COMMIT terminates it.
    """
    turns = []
    for i, s in enumerate(steps):
        node, bt = s["node"], s["backtrack"]
        prev = steps[i - 1]["node"] if i else None
        parts = []
        if bt:
            # ASTRO case 2: reflect, then judge, then say where we are going back to.
            parts += [REFLECT, _evidence(prev, dev0, faulty_pid), NEGATIVE,
                      _backtrack_sentence(bt, node)]
        elif prev is not None:
            parts.append(_evidence(prev, dev0, faulty_pid))
            # ASTRO also injects the reflection at HIGH-Q intermediate nodes, so the verdict is
            # something the model states after reflecting. Our high-Q moment is the lock-on: a probe
            # that closed at least half the error.
            if prev.q is not None and prev.q >= LOCK_ON_DROP and not prev.passes:
                parts += [REFLECT, POSITIVE]
        parts.append(_intent(prev, node, dev0))
        think = " ".join(p for p in parts if p)
        turns.append({"node": node, "think": think, "backtrack": bool(bt),
                      "backtrack_kind": bt, "mode": "SIMULATE", "call": node.call,
                      "text": f"<think>{think}</think>"
                              f"{'<backtrack/>' if bt else ''}"
                              f"<act>SIMULATE {node.call}</act>"})

    # ASTRO injects the reflection "immediately after the final node" so the model closes by
    # judging its own work. Here the harness's $found_note fixes the wording, so the reflection is
    # carried by the preceding turn and the commit stays byte-compatible with what the prompt asks.
    final = steps[-1]["node"]
    turns.append({"node": final, "think": COMMIT_THINK, "backtrack": False,
                  "backtrack_kind": None, "mode": "COMMIT", "call": final.call,
                  "text": f"<think>{COMMIT_THINK}</think><act>COMMIT {final.call}</act>"})
    return turns


def _demo():
    import argparse
    import json

    from astro.linearize import sample_traces
    from astro.tree import build_tree

    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default="data/instances_std30.jsonl")
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    path = args.instances if os.path.isabs(args.instances) else os.path.join(HERE, args.instances)
    for r in [json.loads(l) for l in open(path)][:args.limit]:
        root, st = build_tree(r)
        if not st["ok"]:
            print(f"\n=== {r['id']}: no passing terminal")
            continue
        print(f"\n=== {r['id']}  ({r['fault_types'][0]}, D={st['dev0_mm'] / r['tau_mm']:.1f}x tau)")
        for t in sample_traces(root, seed=args.seed):
            print(f"\n--- k={t['k']}  {t['n_probes']} probes, {t['n_backtracks']} backtracks")
            for j, turn in enumerate(verbalize(t["steps"], st["dev0_mm"], st["faulty_pid"]), 1):
                print(f"  turn {j}: {turn['text']}")


if __name__ == "__main__":
    _demo()
