#!/usr/bin/env python
"""
Aggregate finished runs into the analysis tables, and write them to disk.

Reads every `runs/<run>/<agent>/records.jsonl` given (or a named group), and emits
runs/_analysis/<name>.{md,json}: success rate, tries-to-submit range/median/mean (overall, and among
SOLVED episodes only), plus breakdowns by fault type and by difficulty level, and the integrity
counters that say whether the numbers can be trusted (invalid actions, API give-ups).

    python text_fixit/summarize_runs.py --group baseline
    python text_fixit/summarize_runs.py --group m4 --name m4_composite

Tries-to-submit is `n_simulate`: SIMULATE calls made before the final answer, hard-capped by the
budget. The solved-only column is the informative one -- failures pile up at the cap and drag the
overall median to it.
"""
import argparse
import glob
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
OUT = os.path.join(RUNS, "_analysis")


def _stats(xs):
    if not xs:
        return None
    return {"n": len(xs), "min": min(xs), "max": max(xs),
            "median": st.median(xs), "mean": round(sum(xs) / len(xs), 2)}


def _fmt(s):
    return "-" if not s else f"{s['min']}-{s['max']}  med {s['median']:g} / mean {s['mean']:g}"


def load(run_dir):
    hits = glob.glob(os.path.join(run_dir, "*", "records.jsonl"))
    recs = []
    for h in hits:
        recs += [json.loads(l) for l in open(h)]
    return recs


def summarize(label, recs):
    solved = [r for r in recs if r["terminal_pass"]]
    row = {
        "label": label, "n": len(recs), "solved": len(solved),
        "success_rate": round(len(solved) / len(recs), 4) if recs else None,
        "tries_all": _stats([r["n_simulate"] for r in recs]),
        "tries_solved": _stats([r["n_simulate"] for r in solved]),
        "mean_score": round(sum(r["terminal_score"] for r in recs) / len(recs), 4) if recs else None,
        "committed_rate": round(sum(1 for r in recs if r["committed"]) / len(recs), 4) if recs else None,
        "invalid_actions": sum(r.get("n_invalid", 0) for r in recs),
        "resets": sum(r.get("n_reset", 0) for r in recs),
        "api_giveup_episodes": sum(1 for r in recs if r.get("n_api_giveup", 0)),
        "by": {},
    }
    for key in ("corruption_type", "level"):
        groups = sorted({r.get(key) for r in recs if r.get(key)})
        if len(groups) <= 1 and key == "level":
            continue
        row["by"][key] = {}
        for g in groups:
            sub = [r for r in recs if r.get(key) == g]
            sv = [r for r in sub if r["terminal_pass"]]
            row["by"][key][g] = {
                "n": len(sub), "solved": len(sv),
                "success_rate": round(len(sv) / len(sub), 4),
                "tries_all": _stats([r["n_simulate"] for r in sub]),
                "tries_solved": _stats([r["n_simulate"] for r in sv]),
            }
    return row


def render(name, rows, note):
    L = [f"# {name}", "", note, ""]
    L += ["| condition | N | solved | success | tries all (min-max med/mean) | tries when solved | "
          "invalid | resets | API give-ups |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['label']} | {r['n']} | {r['solved']} | "
                 f"{100 * r['success_rate']:.0f}% | {_fmt(r['tries_all'])} | "
                 f"{_fmt(r['tries_solved'])} | {r['invalid_actions']} | {r['resets']} | "
                 f"{r['api_giveup_episodes']} |")
    for key, title in (("corruption_type", "By fault type"), ("level", "By difficulty level")):
        blocks = [r for r in rows if key in r["by"]]
        if not blocks:
            continue
        L += ["", f"## {title}", ""]
        for r in blocks:
            L += [f"**{r['label']}**", "",
                  "| group | N | solved | success | tries all | tries when solved |",
                  "|---|---|---|---|---|---|"]
            for g, v in r["by"][key].items():
                L.append(f"| {g} | {v['n']} | {v['solved']} | {100 * v['success_rate']:.0f}% | "
                         f"{_fmt(v['tries_all'])} | {_fmt(v['tries_solved'])} |")
            L.append("")
    return "\n".join(L) + "\n"


GROUPS = {
    "baseline": ("Single-fault standing baseline (deviation OFF, budget 10, tau 2.5%)",
                 [("gemini-3.1-pro text", "base_g3_text"),
                  ("gemini-3.1-pro image", "base_g3_image"),
                  ("robotics-er-2 text", "base_er_text"),
                  ("robotics-er-2 image", "base_er_image")]),
    "m4": ("Composite-fault hard benchmark (deviation OFF, budget 10, tau 1.5%, hard mode). "
           "Shards of one condition are merged.", None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="baseline", choices=sorted(GROUPS))
    ap.add_argument("--name", default=None)
    args = ap.parse_args()
    note, spec = GROUPS[args.group]

    if spec is None:      # m4: discover runs and merge shards (…_s0 / …_s1 -> one condition)
        found = {}
        for d in sorted(glob.glob(os.path.join(RUNS, "m4_*"))):
            cond = os.path.basename(d)
            base = cond[:-3] if cond.endswith(("_s0", "_s1", "_s2", "_s3")) else cond
            found.setdefault(base[3:], []).append(d)
        spec = [(k, v) for k, v in sorted(found.items())]
    else:
        spec = [(lbl, [os.path.join(RUNS, r)]) for lbl, r in spec]

    rows = []
    for label, dirs in spec:
        dirs = dirs if isinstance(dirs, list) else [dirs]
        recs = []
        for d in dirs:
            recs += load(d)
        if recs:
            rows.append(summarize(label, recs))
        else:
            print(f"  (no records yet: {label})")

    name = args.name or f"{args.group}_summary"
    os.makedirs(OUT, exist_ok=True)
    md = render(name, rows, note)
    with open(os.path.join(OUT, f"{name}.md"), "w") as f:
        f.write(md)
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump(rows, f, indent=2)
    print(md)
    print(f"-> {OUT}/{name}.md  and  {name}.json")


if __name__ == "__main__":
    main()
