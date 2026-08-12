#!/usr/bin/env python
"""
Failure decomposition: WHERE in the repair pipeline does each model break?

Success rate says a model fails; it does not say whether it failed to find the broken part, to
choose the right kind of fix, to choose the right axis, or to estimate the magnitude. Those are four
different capabilities and they imply four different remedies, so the report needs them separated.

Recomputed entirely from `runs/<cond>/<agent>/records.jsonl` -- no re-running. Every record carries
`gt_fix_actions` (the ground-truth repair rendered in the agent's own action language) and the full
history of attempted actions, which is enough to ask, per episode:

  localised   did ANY attempt target a part that is actually faulty?
  type        did any attempt use the correct action type on that part?
  axis        did any attempt use the correct axis?
  type+axis   did any attempt get both together -- i.e. reach the right 1-D search problem?
  magnitude   among attempts that got type+axis right, how close did the best one get to the
              ground-truth magnitude? (ratio; 1.0 = exact)

The funnel is monotone by construction (type+axis <= axis <= localised), so the biggest drop between
consecutive stages is the binding constraint for that model.

    python text_fixit/decompose.py --runs m9_qw8_easy_image m5_g3_batch_image ...
    python text_fixit/decompose.py --group m9
"""
import argparse
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")

CALL = re.compile(r"(TRANSLATE|ROTATE|SCALE)\(\s*(P\d+)\s*,\s*([XYZ])\s*,\s*(-?[\d.]+)\s*\)",
                  re.IGNORECASE)


def _calls(text):
    """(type, part, axis, magnitude) for every call in an action string."""
    return [(m.group(1).upper(), m.group(2).upper(), m.group(3).upper(), float(m.group(4)))
            for m in CALL.finditer(text or "")]


def decompose(records):
    """Per-episode funnel + magnitude accuracy. Returns a dict of rates."""
    n = len(records)
    if not n:
        return None
    loc = typ = ax = both = 0
    ratios = []
    solved_first_try, solved = 0, 0
    for r in records:
        gt = _calls(r.get("gt_fix_actions"))
        if not gt:
            continue
        gt_parts = {c[1] for c in gt}
        gt_types = {(c[1], c[0]) for c in gt}
        gt_axes = {(c[1], c[2]) for c in gt}
        gt_both = {(c[1], c[0], c[2]): abs(c[3]) for c in gt}

        tried = [c for h in r.get("history", []) for c in _calls(h.get("action"))]
        hit_loc = any(c[1] in gt_parts for c in tried)
        hit_typ = any((c[1], c[0]) in gt_types for c in tried)
        hit_ax = any((c[1], c[2]) in gt_axes for c in tried)
        best = None
        for c in tried:
            k = (c[1], c[0], c[2])
            if k in gt_both and gt_both[k]:
                rr = abs(c[3]) / gt_both[k]
                if best is None or abs(rr - 1.0) < abs(best - 1.0):
                    best = rr
        loc += hit_loc
        typ += hit_typ
        ax += hit_ax
        both += best is not None
        if best is not None:
            ratios.append(best)
        if r.get("terminal_pass"):
            solved += 1
            if r.get("n_simulate", 0) <= 1:
                solved_first_try += 1

    ratios.sort()
    return {
        "n": n,
        "success": solved / n,
        "localised": loc / n,
        "type": typ / n,
        "axis": ax / n,
        "type_axis": both / n,
        "mag_median": ratios[len(ratios) // 2] if ratios else None,
        "mag_within_25pct": (sum(1 for x in ratios if 0.75 <= x <= 1.25) / len(ratios)
                             if ratios else None),
        "solved_first_try": solved_first_try / solved if solved else None,
    }


def load(run):
    recs = []
    for f in glob.glob(os.path.join(RUNS, run, "*", "records.jsonl")):
        recs += [json.loads(line) for line in open(f)]
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=None, help="explicit run dir names")
    ap.add_argument("--glob", default=None, help="glob over runs/, e.g. 'm9_*'")
    ap.add_argument("--label-from", type=int, default=0, help="strip this many chars off the label")
    args = ap.parse_args()

    names = args.runs or []
    if args.glob:
        names += [os.path.basename(d) for d in sorted(glob.glob(os.path.join(RUNS, args.glob)))
                  if os.path.isdir(d)]
    # merge shards (…_s0/_s1) under one label
    merged = {}
    for nm in names:
        base = nm[:-3] if nm.endswith(("_s0", "_s1", "_s2", "_s3")) else nm
        merged.setdefault(base, []).extend(load(nm))

    print(f"{'condition':<26} {'n':>4} {'PASS':>6} | {'local':>6} {'type':>6} {'axis':>6} "
          f"{'ty+ax':>6} | {'mag med':>8} {'mag±25%':>8} | {'1-try':>6}")
    print("-" * 104)
    for label, recs in sorted(merged.items()):
        d = decompose(recs)
        if not d:
            continue
        f = lambda x: "  -  " if x is None else f"{100 * x:4.0f}%"  # noqa: E731
        mm = "   -  " if d["mag_median"] is None else f"{d['mag_median']:6.2f}x"
        print(f"{label[args.label_from:]:<26} {d['n']:>4} {f(d['success']):>6} | "
              f"{f(d['localised']):>6} {f(d['type']):>6} {f(d['axis']):>6} {f(d['type_axis']):>6} | "
              f"{mm:>8} {f(d['mag_within_25pct']):>8} | {f(d['solved_first_try']):>6}")
    print()
    print("localised = ever targeted a genuinely faulty part; type/axis = ever used the correct one;")
    print("ty+ax = ever reached the right 1-D problem; mag = best magnitude / ground truth among those;")
    print("1-try = of SOLVED episodes, fraction solved on the first SIMULATE (loop not load-bearing).")


if __name__ == "__main__":
    main()
