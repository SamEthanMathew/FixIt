#!/usr/bin/env python
"""
Per-episode results log: outcome, fault type, and iterations-to-outcome for every problem.

`records.jsonl` already carries all of this; nothing here re-runs anything. What it adds is the view
the aggregate tables hide — which specific problem was solved, of which fault type, and how many
SIMULATE iterations it took, separated for SOLVED and FAILED episodes.

Iterations = `n_simulate`, the number of SIMULATE calls made before the final answer. For a FAILED
episode this is how much of the budget was burned before giving up (it usually pins to the cap); for
a SOLVED episode it is the search cost, and a median of 1 means the loop contributed nothing.

    python text_fixit/episode_report.py --glob 'm13_*'
    python text_fixit/episode_report.py --glob 'm13_*' --csv out.csv

Writes markdown to runs/_analysis/<name>.md when --name is given.
"""
import argparse
import csv
import glob
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")


def load(pattern):
    """{condition: [records]} with shards (…_s0/_s1) merged under one condition name."""
    out = {}
    for f in sorted(glob.glob(os.path.join(RUNS, pattern, "*", "records.jsonl"))):
        run = f.split(os.sep)[-3]
        cond = run[:-3] if run.endswith(("_s0", "_s1", "_s2", "_s3")) else run
        out.setdefault(cond, []).extend(json.loads(line) for line in open(f))
    return out


def _stats(xs):
    if not xs:
        return "-"
    return (f"n={len(xs)} min={min(xs)} max={max(xs)} "
            f"med={st.median(xs):g} mean={sum(xs)/len(xs):.1f}")


def report(conds):
    L = ["# Per-episode results — outcome, fault type, iterations", ""]
    L += ["`iterations` = SIMULATE calls before the final answer. For solved episodes this is the "
          "search cost; for failed ones it is how much of the budget was spent before committing.", ""]

    for cond, recs in sorted(conds.items()):
        solved = [r for r in recs if r["terminal_pass"]]
        failed = [r for r in recs if not r["terminal_pass"]]
        L += [f"## {cond}", "",
              f"**{len(solved)}/{len(recs)} solved ({100*len(solved)/max(1,len(recs)):.0f}%)**", "",
              f"- iterations, SOLVED: {_stats([r['n_simulate'] for r in solved])}",
              f"- iterations, FAILED: {_stats([r['n_simulate'] for r in failed])}", ""]

        # by fault type: success AND iteration cost, which differ per type
        types = sorted({r.get("corruption_type") for r in recs if r.get("corruption_type")})
        if types:
            L += ["| fault type | solved | rate | iterations (solved) | iterations (failed) |",
                  "|---|---|---|---|---|"]
            for t in types:
                sub = [r for r in recs if r.get("corruption_type") == t]
                sv = [r for r in sub if r["terminal_pass"]]
                fl = [r for r in sub if not r["terminal_pass"]]
                L.append(f"| {t} | {len(sv)}/{len(sub)} | {100*len(sv)/len(sub):.0f}% | "
                         f"{_stats([r['n_simulate'] for r in sv])} | "
                         f"{_stats([r['n_simulate'] for r in fl])} |")
            L.append("")

        L += ["<details><summary>every episode</summary>", "",
              "| episode | type | outcome | iterations | invalid | dev before → after (mm) | ground truth |",
              "|---|---|---|---|---|---|---|"]
        for r in sorted(recs, key=lambda r: (not r["terminal_pass"], r["id"])):
            L.append(f"| `{r['id']}` | {r.get('corruption_type')} | "
                     f"{'**PASS**' if r['terminal_pass'] else 'fail'} | {r['n_simulate']} | "
                     f"{r.get('n_invalid', 0)} | "
                     f"{r.get('initial_deviation_mm', 0):.0f} → {r.get('terminal_deviation_mm', 0):.0f} | "
                     f"`{r.get('gt_fix_actions', '')}` |")
        L += ["", "</details>", ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True, help="run-dir glob, e.g. 'm13_*'")
    ap.add_argument("--name", default=None, help="write runs/_analysis/<name>.md")
    ap.add_argument("--csv", default=None, help="also write a per-episode CSV")
    a = ap.parse_args()

    conds = load(a.glob)
    if not conds:
        raise SystemExit(f"no runs matched {a.glob!r}")
    md = report(conds)

    if a.name:
        os.makedirs(os.path.join(RUNS, "_analysis"), exist_ok=True)
        p = os.path.join(RUNS, "_analysis", f"{a.name}.md")
        open(p, "w").write(md)
        print(f"-> {p}")
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["condition", "episode", "fault_type", "passed", "iterations",
                        "invalid_actions", "deviation_before_mm", "deviation_after_mm",
                        "terminal_score", "committed", "ground_truth"])
            for cond, recs in sorted(conds.items()):
                for r in recs:
                    w.writerow([cond, r["id"], r.get("corruption_type"), r["terminal_pass"],
                                r["n_simulate"], r.get("n_invalid", 0),
                                round(r.get("initial_deviation_mm", 0), 1),
                                round(r.get("terminal_deviation_mm", 0), 1),
                                r.get("terminal_score"), r.get("committed"),
                                r.get("gt_fix_actions")])
        print(f"-> {a.csv}")
    if not a.name and not a.csv:
        print(md)


if __name__ == "__main__":
    main()
