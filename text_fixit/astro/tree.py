#!/usr/bin/env python
"""
Stage 1 of ASTRO (arXiv:2507.00417 sec.2.2), instantiated for FixIt: build a search tree over
part-transformation repairs, with a Q-value on every node.

WHAT REPLACES WHAT
------------------
ASTRO runs MCTS with PUCT because the space of math reasoning steps is unbounded and Q must be
ESTIMATED -- it samples M=16 rollouts per node and averages a verifier's binary score (Eq. 2).
Neither applies here:

  * The action space is ENUMERABLE. A repair is (part, operation, axis, magnitude): 2-4 parts x
    3 operations x 3 axes, plus a 1-D magnitude refinement. Exhaustive expansion of the shallow
    levels IS the converged tree, so PUCT selection has nothing to choose between.
  * Q is EXACT, from one call. `evaluate_repair_multi` returns the true residual error and a hard
    PASS/FAIL, so ASTRO's 16 rollouts and its N=8 LLM self-consistency filter (Appendix A.1)
    collapse into a single `env._evaluate_specs`. Our Q is ground truth, not an estimate.

So this module keeps ASTRO's OUTPUT -- a tree of states annotated with Q -- and drops the
machinery that existed only to estimate Q.

THE TREE MIRRORS THE PROMPT'S OWN ALGORITHM
-------------------------------------------
`prompts/one_error_search_text.txt` already prescribes the search: STEP A identify the part, STEPS
1-3 sweep the nine (operation, axis) pairs, STEP 4 lock on after a >=50% drop and refine the value
by V*A/(A-B). The tree is exactly that procedure, so a trace linearized from it teaches the model
the procedure the prompt asks for rather than competing with it.

    root                                   virtual, no simulation
    |- part:P0                             virtual, no simulation
    |  |- cell:(TRANSLATE,X)               one probe  <- also the part-identification probe
    |  |- cell:(TRANSLATE,Y)                 ...
    |- part:P1
       |- cell:(TRANSLATE,X)
       |  |- refine v2                     magnitude refinement, same (part, op, axis)
       |  |- refine v3                     -> PASS  (the correct terminal)
       |- cell:(ROTATE,Z)                  -> failed hypothesis (an incorrect terminal)

The three depths are what give ASTRO's ancestor-jump a MEANING here, and they line up with the two
backtrack actions in Fixit_RL sec.3.3: a jump whose lowest common ancestor is the ROOT is
`backtrack to part_selection`; one whose LCA is a PART node is `backtrack to
transformation_selection`. See linearize.py.

OBSERVABILITY INVARIANT
-----------------------
Ground truth is used for exactly one thing: the verifier, i.e. whether a candidate PASSes. That is
ASTRO's V, and it is legitimate -- it is the reward signal, not a hint. Every branching decision
here (which part is faulty, which axis to keep, what the next magnitude is) is taken from SIMULATOR
OUTPUT ONLY, by the same arithmetic the prompt hands the model. Nothing in a generated trace is
derivable only from `instance["gt_fix"]`.

    python text_fixit/astro/tree.py --instances data/instances_std30.jsonl --limit 3 --verbose
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import grids                                     # noqa: E402
from action_parser import _AXIS_INV              # noqa: E402
from env import FridgeRepairEnv                  # noqa: E402

OPS = ("TRANSLATE", "ROTATE", "SCALE")
AXES = (0, 1, 2)

# Two probes read the same error when the part they moved is not the faulty one: `deviation_mm` is
# the worst FAULTY part's error, so a healthy part cannot move it. Float noise is far below this.
SAME_ERROR_MM = 1e-4

ROTATE_PROBE_DEG = 20.0        # prompt STEP 3: "Probe ROTATE(part, A, 20) for each axis A"
SCALE_PROBE_FALLBACK = 0.85    # single-door shapes have no sibling to read a size ratio from
LOCK_ON_DROP = 0.50            # prompt STEP 4: a probe that cuts the error by half ends the search


class SearchNode:
    """One node of the search tree. `ev` and `q` are None on the two virtual kinds."""

    __slots__ = ("kind", "pid", "op", "axis", "value", "call", "ev", "q", "dev",
                 "children", "parent", "idx")

    def __init__(self, kind, parent=None, pid=None, op=None, axis=None, value=None):
        self.kind = kind          # "root" | "part" | "cell" | "refine"
        self.parent = parent
        self.pid, self.op, self.axis, self.value = pid, op, axis, value
        self.call = None          # "TRANSLATE(P1, X, -0.19847)" -- the agent's own action language
        self.ev = None            # evaluate_repair_multi result
        self.q = None             # [0,1]; 1.0 == PASS
        self.dev = None           # deviation_mm
        self.children = []
        self.idx = None           # assigned by number_nodes(), for stable references in traces
        if parent is not None:
            parent.children.append(self)

    # -------------------------------------------------------------- properties
    @property
    def simulated(self):
        return self.ev is not None

    @property
    def passes(self):
        return bool(self.ev and self.ev.get("PASS"))

    @property
    def cell(self):
        """The (part, operation, axis) hypothesis this node belongs to, or None above that level."""
        n = self
        while n is not None and n.kind == "refine":
            n = n.parent
        if n is None or n.kind != "cell":
            return None
        return (n.pid, n.op, n.axis)

    def ancestors(self):
        n, out = self.parent, []
        while n is not None:
            out.append(n)
            n = n.parent
        return out

    def path_from_root(self):
        return list(reversed([self] + self.ancestors()))

    def descendants(self):
        for c in self.children:
            yield c
            yield from c.descendants()

    def __repr__(self):
        if not self.simulated:
            return f"<{self.kind} {self.pid or ''}>"
        return (f"<{self.kind} {self.call} dev={self.dev:.1f} q={self.q:.2f}"
                f"{' PASS' if self.passes else ''}>")


def number_nodes(root):
    """Depth-first index on every node, so a linearized trace can name nodes stably."""
    for i, n in enumerate([root] + list(root.descendants())):
        n.idx = i
    return root


# ------------------------------------------------------------------ probe magnitudes

def _clamp(op, v):
    return grids.clamp_range(v, {"TRANSLATE": "translate", "ROTATE": "rotate",
                                 "SCALE": "scale"}[op])


def _size_ratios(states, id_map, pid):
    """Per-axis (sibling door size / this door size) for the SCALE probe.

    This is the "read the numbers first" step the prompt describes: two doors on one cabinet are
    normally close in size, so the axis whose ratio is furthest from 1 is the mis-sized axis and the
    ratio is roughly the factor needed. Falls back to a fixed shrink on single-door shapes, which
    have no sibling to compare against.
    """
    mine = states.get(id_map[pid]["joint"])
    others = [states[pt["joint"]] for q, pt in id_map.items()
              if q != pid and pt.get("corruptible") and pt["joint"] in states]
    if not mine or not others:
        return [SCALE_PROBE_FALLBACK] * 3
    _, my_ext = mine
    out = []
    for a in AXES:
        sib = [o[1][a] for o in others if o[1][a] > 1e-6]
        out.append(sum(sib) / len(sib) / my_ext[a] if sib and my_ext[a] > 1e-6
                   else SCALE_PROBE_FALLBACK)
    return out


def probe_value(op, axis, err_mm, ratios):
    """The magnitude the PROMPT tells the model to probe with, from the reported error alone.

    STEP 1: TRANSLATE(part, X, -e) where e = E/1000 m.  STEP 3: ROTATE(part, A, 20), and SCALE with
    the ratio read off the geometry block.
    """
    if op == "TRANSLATE":
        return _clamp(op, -err_mm / 1000.0)
    if op == "ROTATE":
        return _clamp(op, ROTATE_PROBE_DEG)
    r = ratios[axis]
    # A ratio ~1.0 (doors match on this axis) would probe SCALE(part, A, 1.0) -- a NO-OP whose
    # unchanged error then reads as "this cell is not the fault", a false inference (the probe
    # tested nothing), and whose repeated base-equal readings can feed _healthy_by_probe toward
    # ruling out the FAULTY part. Probe a real magnitude instead.
    if abs(r - 1.0) < 0.05:
        r = SCALE_PROBE_FALLBACK
    return _clamp(op, r)


def flip_value(op, value):
    """Prompt STEP 1: "error roughly DOUBLES -> right axis, wrong sign. Try the other sign."

    CONTINUOUS ADAPTATION. The sign of a translation or rotation, and the direction of a scale, are
    part of the MAGNITUDE, not of the (part, operation, axis) hypothesis -- so a flip is a
    refinement WITHIN a cell, never a new branch, and must not count against the cell-uniqueness
    invariant in linearize.py. For SCALE the multiplicative inverse plays the role the sign flip
    plays for the two additive operations: f too large -> try 1/f.

    Without this step the sweep can only ever make a wrongly-signed fault worse, the >=50% drop that
    triggers lock-on never fires, and no amount of refinement budget recovers it. That is precisely
    what happened to rotate faults, which are drawn in a single direction over 15-45 degrees.
    """
    if op == "SCALE":
        return None if value <= 0 else _clamp(op, 1.0 / value)
    return _clamp(op, -value)


def refine_value(op, value, err_before, err_after):
    """Prompt STEP 4: value V took the error A -> B, so the value closing all of A is V*A/(A-B).

    SCALE is a MULTIPLIER, so the same reasoning applies in log space: composing the correction
    means raising the factor to the power A/(A-B), not multiplying it. Doing it additively drives
    scale factors negative and off the action bounds.
    """
    gap = err_before - err_after
    if abs(gap) < 1e-9:
        return None
    k = err_before / gap
    k = max(-8.0, min(8.0, k))            # a near-flat probe must not explode the next value
    if op == "SCALE":
        if value <= 0:
            return None
        nxt = value ** k
    else:
        nxt = value * k
    nxt = _clamp(op, nxt)
    if abs(nxt - value) < 1e-9:           # clamped onto the same value -> no progress to be had
        return None
    return nxt


# ------------------------------------------------------------------ tree construction

def _simulate(env, node, pid, op, axis, value, id_map):
    """Attach one simulator call to `node`, in the agent's own action language.

    node.call is rendered by action_parser.format_call FROM THE PARSED SPEC, never by a local
    f-string: the review found a local .5f SCALE format diverging from format_call's .6f, which
    put a call text in 24/104 COMMIT targets that byte-mismatched the $history lines and the
    found_note text in the very prompt the example trains against. Rendering from the parsed
    spec also folds in any clamping the parser applied, so the trace states the action that
    actually ran."""
    from action_parser import format_call, parse
    ax = _AXIS_INV[axis]
    probe = f"{op}({pid}, {ax}, {value:.6f})"
    res = parse(f"<act>SIMULATE {probe}</act>", id_map, multi=True)
    if not res["valid"]:
        return None
    spec = res["actions"][0]["spec"]
    call = format_call(spec, pid)
    ev = env._evaluate_specs([spec], call)
    node.call, node.ev, node.dev = call, ev, float(ev["deviation_mm"])
    node.value = value
    return node


def _q(dev, dev0, passes):
    """Fraction of the original error this candidate closed; 1.0 for a PASS.

    ASTRO's Q is a rollout-averaged binary verifier score. Ours is DENSE and exact -- the env
    reports the residual error, not just pass/fail -- which is strictly more information per node
    and is what makes a single simulator call enough.
    """
    if passes:
        return 1.0
    if dev0 <= 0:
        return 0.0
    return max(0.0, min(1.0, (dev0 - dev) / dev0))


def build_tree(instance, env=None, max_refine=4, top_m=3, verbose=False):
    """Expand the search tree for one instance. Returns (root, stats).

    Simulator budget is n_parts + 8 + max_refine, about 15 calls on a two-door fridge.
    """
    own_env = env is None
    if own_env:
        # budget/modality are irrelevant here: we never call env.step(), only _evaluate_specs.
        env = FridgeRepairEnv(budget=0, state_modality="text", show_deviation=True,
                              action_contract="batch", max_actions=1)
    t0, n_sims = time.time(), 0
    try:
        env.reset(instance)
        id_map = env.id_map
        base = env.reset_eval
        dev0 = float(base["deviation_mm"])
        ratios_by_pid = {pid: _size_ratios(base["states"], id_map, pid)
                         for pid, pt in id_map.items() if pt.get("corruptible")}
        parts = [pid for pid, pt in id_map.items() if pt.get("corruptible")]

        root = SearchNode("root")
        root.dev, root.q = dev0, 0.0

        # -- STEP A: one probe per part. The faulty part is the one whose probe MOVES the error.
        part_nodes = {}
        faulty = []
        for pid in parts:
            pn = SearchNode("part", root, pid=pid)
            part_nodes[pid] = pn
            v = probe_value("TRANSLATE", 0, dev0, ratios_by_pid[pid])
            cn = SearchNode("cell", pn, pid=pid, op="TRANSLATE", axis=0)
            if _simulate(env, cn, pid, "TRANSLATE", 0, v, id_map) is None:
                pn.children.remove(cn)
                continue
            n_sims += 1
            cn.q = _q(cn.dev, dev0, cn.passes)
            if abs(cn.dev - dev0) > SAME_ERROR_MM:
                faulty.append(pid)
            if verbose:
                print(f"    partprobe {cn}", flush=True)

        # Exactly one part is faulty in this fault scope. If the probe evidence does not single one
        # out, the trace would have to assert something the observations do not support -- drop it.
        if len(faulty) != 1:
            return root, {"ok": False, "reason": f"part probe identified {len(faulty)} parts",
                          "n_sims": n_sims, "seconds": round(time.time() - t0, 1)}
        fpid = faulty[0]
        fnode = part_nodes[fpid]

        # -- STEPS 1-3: sweep the remaining eight (operation, axis) cells on the faulty part.
        for op in OPS:
            for axis in AXES:
                if op == "TRANSLATE" and axis == 0:
                    continue                                  # already probed in STEP A
                v = probe_value(op, axis, dev0, ratios_by_pid[fpid])
                cn = SearchNode("cell", fnode, pid=fpid, op=op, axis=axis)
                if _simulate(env, cn, fpid, op, axis, v, id_map) is None:
                    fnode.children.remove(cn)
                    continue
                n_sims += 1
                cn.q = _q(cn.dev, dev0, cn.passes)
                if verbose:
                    print(f"    cell      {cn}", flush=True)

        cells = [c for c in fnode.children if c.simulated]
        if not cells:
            return root, {"ok": False, "reason": "no cell simulated", "n_sims": n_sims,
                          "seconds": round(time.time() - t0, 1)}

        # -- STEP 1 (second half): any probe that made the error WORSE gets its sign flipped.
        # Attached as a refine child, not a sibling cell: the sign lives in the magnitude, so the
        # hypothesis is unchanged (see flip_value).
        for cn in list(cells):
            if cn.passes or cn.dev <= dev0 + SAME_ERROR_MM:
                continue
            nv = flip_value(cn.op, cn.value)
            if nv is None or abs(nv - cn.value) < 1e-9:
                continue
            fl = SearchNode("refine", cn, pid=fpid, op=cn.op, axis=cn.axis)
            if _simulate(env, fl, fpid, cn.op, cn.axis, nv, id_map) is None:
                cn.children.remove(fl)
                continue
            n_sims += 1
            fl.q = _q(fl.dev, dev0, fl.passes)
            if verbose:
                print(f"    flip      {fl}", flush=True)

        # -- STEP 4: refine the most promising hypotheses, best-first.
        #
        # NOT the prompt's greedy lock-on ("the moment any probe cuts the error by half, the search
        # is OVER"). That rule walks into a local minimum on SCALE faults: `deviation_mm` is mean
        # per-vertex displacement, so sliding an over-sized door ALONG the mis-scaled axis realigns
        # its centroid and cuts the error by 79-91% -- a bigger drop than the correct SCALE probe
        # gives -- while leaving the size wrong. On 10867 that path reaches 0.618*tau, inside the
        # deviation tolerance, and still fails because the over-sized door interpenetrates.
        #
        # Refining the top few cells instead costs ~4 extra simulator calls and is also the more
        # faithful reading of ASTRO, whose MCTS explores several branches and keeps whichever
        # reaches a correct terminal; greedy lock-on was a simplification, not the paper.
        # The dead branch is not waste -- a refinement chain that plateaus above tolerance is
        # exactly the failed branch linearize.py needs to teach backtracking.
        probed = [n for n in fnode.descendants() if n.simulated]
        solved = next((c for c in probed if c.passes), None)
        best_per_cell = {}
        for n in probed:
            cur_best = best_per_cell.get(n.cell)
            if cur_best is None or n.dev < cur_best.dev:
                best_per_cell[n.cell] = n
        ranked = sorted((n for n in best_per_cell.values() if n.dev < dev0 - SAME_ERROR_MM),
                        key=lambda c: c.dev)[:top_m]
        for start in ranked:
            if solved is not None:
                break
            # Only chase a hypothesis that actually moved the needle (the prompt's own threshold,
            # kept as an entry filter rather than as a commitment to one branch).
            if (dev0 - start.dev) / dev0 < LOCK_ON_DROP:
                continue
            cur = start
            for _ in range(max_refine):
                # A is ALWAYS dev0. Under the batch contract every action is applied FRESH to the
                # original broken object (env.py: "attempts never stack"), so the error a value V is
                # measured against is the broken object's, not the previous refinement's. Threading
                # the chain as if attempts composed makes the secant step solve the wrong equation
                # and the refinement walks away from the fix.
                nxt = refine_value(cur.op, cur.value, dev0, cur.dev)
                if nxt is None:
                    break
                rn = SearchNode("refine", cur, pid=fpid, op=cur.op, axis=cur.axis)
                if _simulate(env, rn, fpid, cur.op, cur.axis, nxt, id_map) is None:
                    cur.children.remove(rn)
                    break
                n_sims += 1
                rn.q = _q(rn.dev, dev0, rn.passes)
                if verbose:
                    print(f"    refine    {rn}", flush=True)
                if rn.passes:
                    solved = rn
                    break
                if rn.dev >= cur.dev - SAME_ERROR_MM:
                    break              # plateaued or got worse -> a dead branch, stop refining it
                cur = rn

        number_nodes(root)
        stats = {"ok": solved is not None,
                 "reason": None if solved is not None else "no passing terminal",
                 "faulty_pid": fpid, "dev0_mm": round(dev0, 2),
                 "n_sims": n_sims, "n_nodes": 1 + sum(1 for _ in root.descendants()),
                 "n_correct_terminals": sum(1 for n in root.descendants() if n.passes),
                 "n_failed_probes": sum(1 for n in root.descendants()
                                        if n.simulated and not n.passes),
                 "best_dev_over_tau": round(min((n.dev for n in root.descendants()
                                                 if n.simulated), default=float("nan"))
                                            / float(base["tau_mm"]), 3),
                 "seconds": round(time.time() - t0, 1)}
        return root, stats
    finally:
        if own_env:
            env.close()


# ------------------------------------------------------------------ serialisation

def to_dict(node):
    d = {"idx": node.idx, "kind": node.kind, "pid": node.pid, "op": node.op,
         "axis": (None if node.axis is None else _AXIS_INV[node.axis]),
         "value": node.value, "call": node.call, "q": node.q, "dev_mm": node.dev,
         "pass": node.passes if node.simulated else None,
         "children": [to_dict(c) for c in node.children]}
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default="data/instances_std30.jsonl")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--max-refine", type=int, default=4)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--out", default=None, help="write one JSON tree per line")
    args = ap.parse_args()

    path = args.instances if os.path.isabs(args.instances) else os.path.join(HERE, args.instances)
    rows = [json.loads(l) for l in open(path)][:args.limit]
    out = open(args.out, "w") if args.out else None
    ok = 0
    for r in rows:
        print(f"\n{r['id']}  (fault: {r['fault_types'][0]}, "
              f"D={r['broken_deviation_mm'] / r['tau_mm']:.1f}x tau)", flush=True)
        root, st = build_tree(r, max_refine=args.max_refine, verbose=args.verbose)
        print(f"  -> {st}", flush=True)
        ok += bool(st["ok"])
        if out:
            out.write(json.dumps({"id": r["id"], "stats": st, "tree": to_dict(root)}) + "\n")
    if out:
        out.close()
    print(f"\n{ok}/{len(rows)} trees have a passing terminal")


if __name__ == "__main__":
    main()
