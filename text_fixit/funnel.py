#!/usr/bin/env python
"""Capability funnel for one or more runs: where in the chain does the agent lose the repair?

Every emitted action is scored against the episode's ground-truth fix on four independent
questions -- right PART, right fault TYPE, right AXIS, all three -- plus the magnitude ratio among
the actions that got all three right. Chance level is printed alongside, because for a 3-way axis
choice 33% is not a finding, it is a coin.

    python text_fixit/funnel.py strict_qw8_image one_error_qw8_image
    python text_fixit/funnel.py --by-type one_error_er_image
    python text_fixit/funnel.py --all                      # every run with a summary.json

Reads only records.jsonl + errors.jsonl, so it works on a partially-finished run.
"""
import argparse
import glob
import json
import os
import re
import statistics as st
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
CALL = re.compile(r"(TRANSLATE|ROTATE|SCALE)\((P\d+),\s*([XYZ]),\s*(-?[\d.]+)\)")
AXES = "XYZ"


def records(run):
    for f in sorted(glob.glob(os.path.join(RUNS, run, "*", "records.jsonl"))):
        lines = open(f).read().splitlines()
        if lines:
            yield json.loads(lines[0])


def n_errors(run):
    return sum(1 for f in glob.glob(os.path.join(RUNS, run, "*", "errors.jsonl"))
               for _ in open(f))


def funnel(recs):
    """-> (counts dict, n_actions, magnitude ratios, axis confusion Counter)"""
    hit, tot, ratios, conf = Counter(), 0, [], Counter()
    for r in recs:
        g = CALL.search(r.get("gt_fix_actions") or "")
        if not g:
            continue
        g_type, g_part, g_axis, g_val = g.group(1), g.group(2), g.group(3), abs(float(g.group(4)))
        for h in r["history"]:
            for m in CALL.finditer(str(h.get("action") or "")):
                tot += 1
                p, t, a = m.group(2) == g_part, m.group(1) == g_type, m.group(3) == g_axis
                hit["part"] += p
                hit["type"] += t
                hit["axis"] += a
                hit["all"] += p and t and a
                conf[(g_axis, m.group(3))] += 1
                if p and t and a and g_val > 0:
                    ratios.append(abs(float(m.group(4))) / g_val)
    return hit, tot, ratios, conf


def line(label, recs, errs, width=26):
    recs = list(recs)
    if not recs:
        return None
    hit, tot, ratios, conf = funnel(recs)
    pct = lambda k: 100 * hit[k] / tot if tot else 0.0
    best = [min(h["deviation_over_tau"] for h in r["history"]) for r in recs if r["history"]]
    solved = sum(r["terminal_pass"] for r in recs)
    reached = sum(1 for r in recs if any(h["pass"] for h in r["history"]))
    mag = st.median(ratios) if ratios else float("nan")
    print(f"{label[:width]:{width}}{solved:>3}/{len(recs):<4}{reached:>5}{errs:>7}"
          f"{pct('part'):>7.1f}{pct('type'):>7.1f}{pct('axis'):>7.1f}{pct('all'):>7.1f}"
          f"{mag:>8.2f}{st.median(best):>9.2f}")
    return conf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--all", action="store_true", help="every run directory that has records")
    ap.add_argument("--by-type", action="store_true", help="split each run by fault type")
    ap.add_argument("--confusion", action="store_true", help="print the axis confusion matrix")
    args = ap.parse_args()

    names = args.runs
    if args.all or not names:
        names = sorted(os.path.basename(os.path.dirname(p))
                       for p in glob.glob(os.path.join(RUNS, "*", ""))
                       if glob.glob(os.path.join(p, "*", "records.jsonl")))

    print(f"{'run':26}{'solved':>7}{'rchd':>5}{'errs':>7}"
          f"{'part%':>7}{'type%':>7}{'axis%':>7}{'all3%':>7}{'mag':>8}{'best':>9}")
    print(f"{'chance ->':26}{'':>7}{'':>5}{'':>7}{'~50':>7}{'33.3':>7}{'33.3':>7}{'~5.6':>7}"
          f"{'1.00':>8}{'':>9}")
    print("-" * 90)

    confs = {}
    for run in names:
        recs = list(records(run))
        if not recs:
            continue
        errs = n_errors(run)
        c = line(run, recs, errs)
        if c:
            confs[run] = c
        if args.by_type:
            for ft in ("translate", "rotate", "scale"):
                sub = [r for r in recs if r["corruption_type"] == ft]
                if sub:
                    line(f"    {ft}", sub, 0)

    if args.confusion:
        for run, conf in confs.items():
            print(f"\naxis confusion — {run}   (row = ground truth, col = emitted)")
            print("        " + "".join(f"{a:>6}" for a in AXES) + "     total")
            for gt in AXES:
                row = [conf.get((gt, e), 0) for e in AXES]
                print(f"   {gt}   " + "".join(f"{v:>6}" for v in row) + f"{sum(row):>10}")
            emitted = [sum(conf.get((gt, e), 0) for gt in AXES) for e in AXES]
            print("   emitted" + "".join(f"{v:>6}" for v in emitted))


if __name__ == "__main__":
    main()
