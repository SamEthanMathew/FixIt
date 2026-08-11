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


def load_tau_index():
    """instance id -> {link: tau_mm}. Needed for the graded metrics: PASS is binary, but the logs
    keep per-part deviations, so partial credit and a tolerance sweep can be recomputed post-hoc
    without re-running anything."""
    idx = {}
    for f in glob.glob(os.path.join(HERE, "data", "instances_*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            if r.get("tau_mm_per_part"):
                idx[r["id"]] = r["tau_mm_per_part"]
            elif r.get("tau_mm"):
                idx[r["id"]] = {r.get("link"): r["tau_mm"]}
    return idx


def graded(recs, tau_idx):
    """Signal that survives a 0% floor.

    parts_within_tol : mean fraction of an instance's faulty parts left inside tolerance. A 3-fault
                       instance with 2 parts fixed scores 0.67 where PASS scores 0.
    deviation_closed : mean fraction of the initial error removed, clipped to [0,1]. Negative means
                       the agent made it worse, which happens often enough to be worth seeing.
    made_worse       : fraction of episodes ending with MORE error than they started.
    best_seen_pass   : did any simulated state PASS, even if it was not the one committed? Separates
                       "never found it" from "found it and failed to commit it".
    tau_sweep        : success rate if the tolerance had been 1x / 1.67x (= the old 2.5%) / 2x / 3x,
                       recomputed from per-part deviations. Geometry only -- the closes/collides
                       gates are held at their observed values, so this is an upper bound.
    """
    out = {}
    fracs, closed, worse, bestpass = [], [], 0, 0
    sweep = {m: 0 for m in (1.0, 1.667, 2.0, 3.0)}
    counted = 0
    for r in recs:
        pp = r.get("terminal_per_part") or {}
        if pp:
            fracs.append(sum(1 for v in pp.values() if v["within_tol"]) / len(pp))
        init, term = r.get("initial_deviation_mm"), r.get("terminal_deviation_mm")
        if init:
            frac = (init - term) / init
            closed.append(max(-1.0, min(1.0, frac)))
            if term > init:
                worse += 1
        if any(h.get("pass") for h in r.get("history", [])):
            bestpass += 1
        taus = tau_idx.get(r["id"])
        if pp and taus:
            counted += 1
            phys = r.get("terminal_pass") or all(v.get("closes", True) for v in pp.values())
            for m in sweep:
                ok = all(v["deviation_mm"] <= m * taus.get(k, float("inf")) for k, v in pp.items())
                sweep[m] += 1 if (ok and phys) else 0
    n = len(recs)
    out["parts_within_tol"] = round(sum(fracs) / len(fracs), 4) if fracs else None
    out["deviation_closed"] = round(sum(closed) / len(closed), 4) if closed else None
    out["made_worse_rate"] = round(worse / n, 4) if n else None
    out["ever_simulated_a_pass"] = round(bestpass / n, 4) if n else None
    out["tau_sweep"] = ({f"{m}x": round(v / counted, 4) for m, v in sweep.items()}
                        if counted else None)
    out["tau_sweep_n"] = counted
    return out


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


def summarize(label, recs, tau_idx=None):
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
    row.update(graded(recs, tau_idx or {}))

    def _pair(r):
        """Which TYPES compose a multi-fault instance, e.g. 'rotate+scale'. Derived from the record's
        existing `fault_types`, so no instance-schema or run_episode change is needed. M5 showed the
        models are lopsided in opposite directions by fault type, so on the n=2 rung the PAIR may
        matter more than the count -- this is the M6 H4 breakdown."""
        ft = r.get("fault_types") or []
        return "+".join(sorted(ft)) if len(ft) > 1 else None

    getters = {"corruption_type": lambda r: r.get("corruption_type"),
               "level": lambda r: r.get("level"),
               "fault_pair": _pair}
    for key, get in getters.items():
        groups = sorted({g for g in (get(r) for r in recs) if g})
        if len(groups) <= 1 and key in ("level", "fault_pair"):
            continue
        row["by"][key] = {}
        for g in groups:
            sub = [r for r in recs if get(r) == g]
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

    # Graded view: binary PASS goes to zero on the hard set, which would make the contract /
    # modality / level comparisons untestable. These keep ranking the conditions at a 0% floor.
    L += ["", "## Graded progress (informative when PASS floors at 0)", "",
          "| condition | parts within tol | deviation closed | made worse | ever simulated a PASS |",
          "|---|---|---|---|---|"]
    for r in rows:
        pw, dc = r.get("parts_within_tol"), r.get("deviation_closed")
        L.append(f"| {r['label']} | {'-' if pw is None else f'{100 * pw:.0f}%'} | "
                 f"{'-' if dc is None else f'{100 * dc:.0f}%'} | "
                 f"{100 * (r.get('made_worse_rate') or 0):.0f}% | "
                 f"{100 * (r.get('ever_simulated_a_pass') or 0):.0f}% |")
    if any(r.get("tau_sweep") for r in rows):
        L += ["", "## Tolerance sweep  (geometry only; closes/collides held at observed values, "
              "so these are UPPER bounds). 1.667x = the old 2.5% tolerance.", "",
              "| condition | 1x (as run) | 1.667x | 2x | 3x |", "|---|---|---|---|---|"]
        for r in rows:
            s = r.get("tau_sweep")
            if not s:
                continue
            L.append(f"| {r['label']} | " + " | ".join(
                f"{100 * s[k]:.0f}%" for k in ("1.0x", "1.667x", "2.0x", "3.0x")) + " |")
    for key, title in (("corruption_type", "By fault type"), ("level", "By difficulty level"),
                       ("fault_pair", "By fault-type pair")):
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
    "m7": ("Qwen difficulty ladder: is the trainable model compliance-bound or difficulty-bound? "
           "Same model walked down rungs already calibrated for g3/er -- hardened n=1 control "
           "(tau 1.5%, hard) and the original easy baseline (tau 2.5%, no hard, train/per-type 25). "
           "Image only; text is 0/120 across three models (M6). Watch invalid-action rate.", None),
    "m6": ("The n=2 rung: 2 sub-faults, level-matched arms (2fault_1door vs 2fault_2door), "
           "type-pair stratified. reveal_fixable ON, hard render + multi-fault hint ON, "
           "deviation OFF, budget 10, tau 1.5%. Shards merged.", None),
    "m5": ("Hardened SINGLE-fault control with the part table's fixable/role columns REVEALED "
           "(hard render + multi-fault hint still on; deviation OFF, budget 10, tau 1.5%). "
           "Isolates the reveal_fixable switch against m4's control arms, and adds the stack "
           "contract that m4 skipped as redundant for a one-action fix. Shards are merged.", None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="baseline", choices=sorted(GROUPS))
    ap.add_argument("--name", default=None)
    args = ap.parse_args()
    note, spec = GROUPS[args.group]

    if spec is None:      # discover runs named <group>_* and merge shards (…_s0 / …_s1 -> one cond)
        prefix = f"{args.group}_"
        found = {}
        for d in sorted(glob.glob(os.path.join(RUNS, prefix + "*"))):
            cond = os.path.basename(d)
            base = cond[:-3] if cond.endswith(("_s0", "_s1", "_s2", "_s3")) else cond
            found.setdefault(base[len(prefix):], []).append(d)
        spec = [(k, v) for k, v in sorted(found.items())]
    else:
        spec = [(lbl, [os.path.join(RUNS, r)]) for lbl, r in spec]

    tau_idx = load_tau_index()
    rows = []
    for label, dirs in spec:
        dirs = dirs if isinstance(dirs, list) else [dirs]
        recs = []
        for d in dirs:
            recs += load(d)
        if recs:
            rows.append(summarize(label, recs, tau_idx))
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
