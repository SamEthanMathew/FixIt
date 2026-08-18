#!/usr/bin/env python
"""
Stage 2 of ASTRO (arXiv:2507.00417 sec.2.3, Algorithm 1): flatten a search tree into a linear
sequence of nodes whose ancestor-jumps are backtracks.

ASTRO'S ALGORITHM 1, VERBATIM IN STRUCTURE
------------------------------------------
    Psi, Lambda <- DFS(root)                     terminal nodes, correct and incorrect
    Psi' <- {n in Psi : self_eval(n) == 1}       high-quality correct solutions
    n*   <- sample(Psi')
    Lk   <- sample_with_unique_answers(Lambda, k)
    for n in Lk + [n*]:
        l <- gather_nodes_from_root(n)
        L <- merge_sequences(L, l - L)

Two invariants: the sequence ENDS at a correct terminal, and no two nodes in it carry the same
incorrect answer -- so the model learns not to repeat a failed attempt.

THREE ADAPTATIONS FOR A CONTINUOUS ACTION SPACE
-----------------------------------------------
ASTRO searches over discrete reasoning steps. A repair here is (part, operation, axis, MAGNITUDE),
and the magnitude is continuous. That changes Algorithm 1 in three places, and getting any of them
wrong silently produces degenerate traces.

1.  UNIQUENESS IS PER HYPOTHESIS CELL, NOT PER ACTION STRING.
    ASTRO forbids two nodes with the same incorrect *answer*. The literal translation -- forbid two
    identical action strings -- is useless here, because TRANSLATE(P1,Y,-0.145) and
    TRANSLATE(P1,Y,-0.150) are different strings expressing the SAME hypothesis, and a trace that
    "explored" both would be teaching the model to re-probe a branch it already refuted. So the
    unit of uniqueness is the discrete cell (part, operation, axis), which is exactly the level the
    prompt's own sweep enumerates, and exactly what `repeated-failure rate` measures in
    Fixit_RL sec.7.

2.  A MAGNITUDE REFINEMENT IS NOT A BACKTRACK.
    Descending a refine chain is CONTINUATION within one hypothesis -- the search has locked on and
    is tuning a number. Only a jump that changes the cell counts as a backtrack. This distinction
    does not exist in ASTRO (math steps carry no parameter to tune) and it is the main reason the
    tree is three levels deep rather than flat: the depth of the lowest common ancestor is what
    tells us WHICH KIND of backtrack occurred.

        LCA is the ROOT       -> the faulty part itself is in question
                                 = Fixit_RL sec.3.3  {"action":"backtrack","to":"part_selection"}
        LCA is a PART node    -> the part stands, the operation/axis does not
                                 = Fixit_RL sec.3.3  {"action":"backtrack","to":
                                                      "transformation_selection"}
        LCA is a CELL node    -> not a backtrack at all; a sibling refinement

3.  NO LLM SELF-EVALUATION.
    ASTRO's Psi' filter (Appendix A.1) exists to reject correct answers reached by a lucky guess,
    and it costs N=8 sampled self-evaluations per solution. Our verifier is PyBullet: a terminal
    PASSes only if the faulty part is inside tolerance AND the door still closes AND nothing
    interpenetrates. There is no lucky guess to filter -- a pass IS the repair. Psi' = Psi.
    What DOES need filtering is traces whose correct terminal is reached without any observable
    justification, and that cannot happen by construction: every node's magnitude is derived from
    the reported error by the prompt's own arithmetic (see tree.probe_value / tree.refine_value).

SAMPLING
--------
ASTRO sec.3.1 curates, per problem, one direct solution (k=0) and three search solutions (k>=1),
varying k in [0,2]. `sample_traces` mirrors that ratio; see DEFAULT_K_MIX.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from astro.tree import build_tree, number_nodes   # noqa: E402

# ASTRO sec.3.1: "for each math problem we sample one direct solution without any backtracking
# (k = 0), and three search solutions which reach the correct answer with at least one
# self-reflection and backtracking instance (k >= 1)."
DEFAULT_K_MIX = (0, 1, 1, 2)

BACKTRACK_PART = "part_selection"
BACKTRACK_TRANSFORM = "transformation_selection"


def terminals(root):
    """(correct, incorrect) terminal nodes.

    A terminal is a simulated node that ends a line of enquiry: it PASSes (correct), or it has no
    simulated children, meaning the search never refined it further (incorrect). Interior nodes of
    a refine chain are not terminals -- they are steps on the way to one.
    """
    correct, incorrect = [], []
    for n in root.descendants():
        if not n.simulated:
            continue
        if n.passes:
            correct.append(n)
        elif not any(c.simulated for c in n.children):
            incorrect.append(n)
    return correct, incorrect


def lca(a, b):
    """Lowest common ancestor of two nodes."""
    seen = {id(x) for x in [a] + a.ancestors()}
    n = b
    while n is not None and id(n) not in seen:
        n = n.parent
    return n


def backtrack_kind(prev, node):
    """Which backtrack the move from `prev` to `node` represents. None if it is not one.

    Classified from the LOWEST COMMON ANCESTOR of the two nodes, not from `node.parent`. The
    difference is not cosmetic: a trace only ever emits SIMULATED nodes, so the structural `part`
    node is absent from the sequence, and reading `node.parent` alone cannot tell a jump WITHIN one
    part from a jump ACROSS two. Both have a cell as their first fresh node and a part node as its
    parent; only the LCA separates them -- root for a cross-part jump, the part node for a
    within-part one.
    """
    if prev is None or node is None:
        return None
    a = lca(prev, node)
    if a is None or a.kind == "root":
        return BACKTRACK_PART
    if a.kind == "part":
        return BACKTRACK_TRANSFORM
    return None                      # LCA is a cell/refine -> a magnitude step, not a backtrack


def branch_nodes(term):
    """The simulated nodes a trace must contain to reach `term`, in search order.

    `gather_nodes_from_root` in ASTRO's Algorithm 1 returns the root path. Ours needs one addition:
    PART nodes are structural and carry no simulation, so the bare root path to a cell under P1 is
    just [that cell] -- a trace built from it would pick an operation and axis before ever
    establishing which part is faulty, which inverts the prompt's STEP A and teaches the wrong
    order. Prepending each part ancestor's identification probe (its first simulated child) restores
    "find the part, then the transformation" without changing the tree.
    """
    path = term.path_from_root()
    out = []
    for n in path:
        if n.kind == "part":
            ident = next((c for c in n.children if c.simulated), None)
            if ident is not None:
                out.append(ident)
        elif n.simulated:
            out.append(n)
    # dedupe, preserving order (the identification probe IS the target on a translate solve)
    seen, uniq = set(), []
    for n in out:
        if id(n) not in seen:
            seen.add(id(n))
            uniq.append(n)
    return uniq


def _sample_unique_cells(incorrect, k, rng):
    """ASTRO's `sample_with_unique_answers`, at cell granularity (adaptation 1).

    Prefers branches that are informative to backtrack FROM: a probe on a healthy part (which left
    the error untouched) and a probe with a real but insufficient effect teach different lessons, so
    both kinds are eligible and the choice is random rather than by score -- picking the k
    highest-Q failures would only ever show near-misses and never the wrong-part case.
    """
    by_cell = {}
    for n in incorrect:
        by_cell.setdefault(n.cell, []).append(n)
    cells = sorted(by_cell, key=lambda c: (c[0], c[1], c[2]))
    rng.shuffle(cells)
    return [rng.choice(by_cell[c]) for c in cells[:k]]


def linearize(root, k, rng, correct_node=None):
    """ASTRO Algorithm 1 -> a list of steps ending at a passing terminal.

    Returns [] when the tree has no correct terminal (ASTRO's "invalid tree").

    Each step is {"node", "backtrack": None|part_selection|transformation_selection, "branch": i},
    covering SIMULATED nodes only -- root and part nodes are structural, carry no action, and would
    have nothing to emit as a turn.
    """
    correct, incorrect = terminals(root)
    if not correct:
        return []
    # Psi' == Psi: the simulator is the verifier, so there is no lucky-guess class to filter
    # (adaptation 3). Prefer the SHORTEST passing path -- the search that found the repair with
    # fewest probes -- since Fixit_RL sec.7 scores simulator calls per solved episode.
    target = correct_node or min(correct, key=lambda n: len(n.ancestors()))
    chosen = _sample_unique_cells([n for n in incorrect if n.cell != target.cell], k, rng)

    steps, seen = [], set()
    for branch_i, term in enumerate(chosen + [target]):
        path = branch_nodes(term)
        if term is not target:
            # A failed branch under the same part prepends that part's identification probe -- and
            # on a translate solve the identification probe IS the correct terminal. Letting a
            # failed branch consume it would end the trace on a failure and break invariant 1.
            path = [n for n in path if n is not target]
        fresh = [n for n in path if id(n) not in seen]
        if not fresh:
            continue
        for j, n in enumerate(fresh):
            seen.add(id(n))
            # Only the FIRST node of a newly merged branch can be a jump; the rest continue it.
            bt = backtrack_kind(steps[-1]["node"], n) if (j == 0 and steps) else None
            steps.append({"node": n, "backtrack": bt, "branch": branch_i})
    # Invariant 1: the sequence ends at the correct terminal.
    assert steps and steps[-1]["node"] is target, "linearized trace does not end at a PASS"
    return steps


def sample_traces(root, k_mix=DEFAULT_K_MIX, seed=0):
    """One trace per k in `k_mix` (ASTRO sec.3.1's 1 direct + 3 search mix), deduplicated.

    Two draws at the same k can pick the same failed cells and produce an identical trace; keeping
    both would silently upweight it in the SFT mix.
    """
    rng = random.Random(seed)
    _, incorrect = terminals(root)
    n_cells = len({n.cell for n in incorrect})
    out, sigs = [], set()
    for k in k_mix:
        kk = min(k, n_cells)
        steps = linearize(root, kk, rng)
        if not steps:
            continue
        sig = tuple(s["node"].idx for s in steps)
        if sig in sigs:
            continue
        sigs.add(sig)
        out.append({"k": kk, "steps": steps,
                    "n_backtracks": sum(1 for s in steps if s["backtrack"]),
                    "n_part_backtracks": sum(1 for s in steps
                                             if s["backtrack"] == BACKTRACK_PART),
                    "n_probes": len(steps)})
    return out


def describe(trace):
    """One-line-per-step rendering, for eyeballing a trace."""
    out = []
    for s in trace["steps"]:
        n = s["node"]
        tag = f"  [backtrack->{s['backtrack']}]" if s["backtrack"] else ""
        out.append(f"    {n.call:34} dev={n.dev:8.1f}  q={n.q:.2f}"
                   f"{'  PASS' if n.passes else ''}{tag}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default="data/instances_std30.jsonl")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    path = args.instances if os.path.isabs(args.instances) else os.path.join(HERE, args.instances)
    rows = [json.loads(l) for l in open(path)][:args.limit]
    tot, bt = 0, 0
    for r in rows:
        root, st = build_tree(r)
        if not st["ok"]:
            print(f"\n{r['id']}: no passing terminal ({st['reason']})")
            continue
        number_nodes(root)
        traces = sample_traces(root, seed=args.seed)
        print(f"\n{r['id']}  ({r['fault_types'][0]}, {st['n_sims']} sims, "
              f"{len(traces)} traces)")
        for t in traces:
            print(f"  k={t['k']}  probes={t['n_probes']}  backtracks={t['n_backtracks']}")
            print(describe(t))
            tot += 1
            bt += t["n_backtracks"]
    print(f"\n{tot} traces, {bt} backtracks total")


if __name__ == "__main__":
    main()
