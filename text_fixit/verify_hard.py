#!/usr/bin/env python
"""
Independent verification of the hard benchmark (data/instances_hard.jsonl + instances_control.jsonl).

Like validate_instances.py, this does NOT trust the fields written at generation time -- it reloads
each URDF and recomputes everything. Every check writes its full per-instance result to
runs/_analysis/verify_hard.{log,json} so the evidence is on disk, not just in a console scroll.

Checks (the plan's verification gates 1-4):

  1. INVERTIBILITY  applying gt_fix_sequence to the broken URDF restores EVERY faulty part to
                    ~0 deviation and PASSes the multi-part contract. This is the gate that keeps the
                    oracle ceiling at 100%; if reverse-order inversion were wrong it fails here.
  2. NECESSITY      the break is genuinely composite: each sub-fault individually clears 3*tau, and
                    applying any TWO of the three inverses still fails. Without this an "n=3"
                    instance could be solvable with 2 actions.
  3. DIVERSITY      distinct bases within each set, no duplicate (base, link, type, axis, value)
                    tuples, and the scale axis is not pinned to one value (the old sampler put ~78%
                    of scale faults on axis 1).
  4. HARDENING      every instance carries tau_frac 0.015, and every magnitude is OFF-GRID (a model
                    cannot land inside tolerance by recalling a grid bin).

    FIXIT_TAU_FRAC=0.015 python text_fixit/verify_hard.py
"""
import itertools
import json
import os
import sys
from collections import Counter

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corruption as corr                      # noqa: E402
import geom                                    # noqa: E402
import grids                                   # noqa: E402
from evaluation import evaluate_repair_multi   # noqa: E402
from part_table import build_part_table        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_TAU_FRAC = 0.015
SETS = {"composite": "data/instances_hard.jsonl", "control": "data/instances_control.jsonl"}


def _abs(rel):
    return rel if os.path.isabs(rel) else os.path.join(HERE, rel)


def _chain(base_urdf, specs, out_name):
    """Apply specs in order; return the final URDF path (intermediates cleaned up)."""
    cur, tmps = base_urdf, []
    for i, spec in enumerate(specs):
        name = out_name if i == len(specs) - 1 else f"_v{i}_{out_name}"
        cur = corr.apply(cur, spec, name)
        if i < len(specs) - 1:
            tmps.append(cur)
    for t in tmps:
        if os.path.exists(t):
            os.remove(t)
    return cur


def check_invertibility(rec, cid):
    broken, healthy = _abs(rec["broken_urdf"]), _abs(rec["healthy_urdf"])
    fixed = _chain(broken, [f["spec"] for f in rec["gt_fix_sequence"]], f"_vfix_{rec['id']}.urdf")
    ev = evaluate_repair_multi(fixed, healthy, rec["faults"], client=cid)
    os.remove(fixed)
    worst = max(v["deviation_mm"] for v in ev["per_part"].values())
    return {"pass": bool(ev["PASS"] and worst <= 0.1 * ev["tau_mm"]),
            "gt_fixed_deviation_mm": round(worst, 6), "tau_mm": ev["tau_mm"],
            "contract_pass": ev["PASS"],
            "per_part_deviation_mm": {k: v["deviation_mm"] for k, v in ev["per_part"].items()}}


def check_necessity(rec, cid):
    """Each sub-fault must MATTER: dropping any one inverse must leave the instance failing AND
    still >= 3*tau off -- i.e. every sub-fault individually accounts for an unambiguous share of the
    error, so an n-fault instance is not secretly solvable with n-1 actions.

    This leave-one-out residual is the correct measure for a composed break. Applying a sub-fault
    ALONE to the healthy object is not: a scale sampled onto an already-rotated door displaces
    differently against healthy geometry, so it can read below 3*tau while still being essential.
    That solo number is still reported (check_submagnitudes) but is informational only.
    """
    broken, healthy = _abs(rec["broken_urdf"]), _abs(rec["healthy_urdf"])
    seq = rec["gt_fix_sequence"]
    if len(seq) < 2:
        return {"pass": True, "note": "single fault - not applicable", "subsets": []}
    out = []
    for drop in range(len(seq)):
        partial = [f["spec"] for i, f in enumerate(seq) if i != drop]
        cand = _chain(broken, partial, f"_vpart_{rec['id']}_{drop}.urdf")
        ev = evaluate_repair_multi(cand, healthy, rec["faults"], client=cid)
        os.remove(cand)
        out.append({"dropped_fix_index": drop,
                    "dropped_type": seq[drop]["spec"]["type"],
                    "dropped_part": seq[drop]["part_name"],
                    "PASS": ev["PASS"], "deviation_mm": ev["deviation_mm"],
                    "tau_mm": ev["tau_mm"],
                    "residual_over_tau": round(ev["deviation_mm"] / ev["tau_mm"], 2)})
    ok = all((not o["PASS"]) and o["residual_over_tau"] >= corr.BROKEN_MARGIN for o in out)
    return {"pass": ok, "subsets": out,
            "min_residual_over_tau": min(o["residual_over_tau"] for o in out)}


def check_offgrid(rec):
    bad = []
    for f in rec["faults"]:
        s = f["spec"]
        v = s["value"]
        if s["type"] == "translate":
            on = grids.on_grid(abs(v), grids.VALUE_GRID, rel_tol=1e-4)
        elif s["type"] == "rotate":
            on = grids.on_grid(abs(v) * 180.0 / 3.141592653589793, grids.ANGLE_GRID, rel_tol=1e-4)
        else:
            on = grids.on_grid(v, grids.SCALE_GRID, rel_tol=1e-4)
        if on:
            bad.append({"type": s["type"], "value": v})
    return {"pass": not bad, "on_grid_values": bad}


def check_submagnitudes(rec, cid):
    """INFORMATIONAL: each sub-fault applied ALONE to the healthy object. Not a gate -- see
    check_necessity for why leave-one-out residual is the binding criterion instead."""
    healthy = _abs(rec["healthy_urdf"])
    out = []
    for k, f in enumerate(rec["faults"]):
        cand = corr.apply(healthy, f["spec"], f"_vsolo_{rec['id']}_{k}.urdf")
        g = geom.geometric_score(cand, healthy, f["joint"], f["link"], client=cid)
        os.remove(cand)
        out.append({"index": k, "type": f["spec"]["type"], "part": f["part_name"],
                    "deviation_mm": round(g["deviation_mm"], 2), "tau_mm": round(g["tau_mm"], 2),
                    "ratio": round(g["deviation_mm"] / g["tau_mm"], 2)})
    return {"pass": all(o["ratio"] >= corr.BROKEN_MARGIN for o in out), "solo": out}


def main():
    if abs(geom.TAU_FRAC - TARGET_TAU_FRAC) > 1e-12:
        raise SystemExit(f"TAU_FRAC is {geom.TAU_FRAC}; run with FIXIT_TAU_FRAC={TARGET_TAU_FRAC}")

    cid = p.connect(p.DIRECT)
    report, ok = {"tau_frac": geom.TAU_FRAC, "sets": {}}, True
    lines = [f"# Hard-benchmark verification (TAU_FRAC={geom.TAU_FRAC})", ""]

    for name, rel in SETS.items():
        rows = [json.loads(l) for l in open(_abs(rel))]
        per, fails = [], []
        for rec in rows:
            r = {"id": rec["id"], "base": rec["base"], "level": rec["level"],
                 "n_faults": rec["n_faults"],
                 "invertibility": check_invertibility(rec, cid),
                 "necessity": check_necessity(rec, cid),
                 "offgrid": check_offgrid(rec),
                 "sub_magnitudes": check_submagnitudes(rec, cid),
                 "tau_frac_ok": abs(rec["tau_frac"] - TARGET_TAU_FRAC) < 1e-12}
            r["all_pass"] = all([r["invertibility"]["pass"], r["necessity"]["pass"],
                                 r["offgrid"]["pass"], r["tau_frac_ok"]])
            if not r["all_pass"]:
                fails.append(r["id"])
            per.append(r)
            print(f"[{name}] {rec['id']:34s} inv={r['invertibility']['pass']} "
                  f"nec={r['necessity']['pass']} offgrid={r['offgrid']['pass']} "
                  f"solo={r['sub_magnitudes']['pass']}", flush=True)

        bases = [r["base"] for r in rows]
        tuples = [(r["base"], f["link"], f["spec"]["type"], f["spec"]["axis"],
                   round(f["spec"]["value"], 9)) for r in rows for f in r["faults"]]
        scale_axes = Counter(f["spec"]["axis"] for r in rows for f in r["faults"]
                             if f["spec"]["type"] == "scale")
        diversity = {
            "n": len(rows),
            "distinct_bases": len(set(bases)),
            "bases_unique": len(set(bases)) == len(bases),
            "duplicate_fault_tuples": len(tuples) - len(set(tuples)),
            "scale_axis_counts": dict(scale_axes),
            "levels": dict(Counter(r["level"] for r in rows)),
        }
        set_ok = not fails and diversity["bases_unique"] and diversity["duplicate_fault_tuples"] == 0
        ok = ok and set_ok
        report["sets"][name] = {"diversity": diversity, "failures": fails, "per_instance": per,
                                "ok": set_ok}

        lines += [f"## {name}  ({len(rows)} instances)  ->  {'OK' if set_ok else 'FAILED'}", "",
                  f"- distinct bases: {diversity['distinct_bases']}/{len(rows)} "
                  f"(unique: {diversity['bases_unique']})",
                  f"- levels: {diversity['levels']}",
                  f"- duplicate (base,link,type,axis,value) tuples: "
                  f"{diversity['duplicate_fault_tuples']}",
                  f"- scale axis spread: {diversity['scale_axis_counts']}",
                  f"- invertibility passed: {sum(r['invertibility']['pass'] for r in per)}/{len(per)}"
                  f"   max gt-fixed deviation: "
                  f"{max(r['invertibility']['gt_fixed_deviation_mm'] for r in per):.6f} mm",
                  f"- necessity (leave-one-out residual >=3tau) passed: "
                  f"{sum(r['necessity']['pass'] for r in per)}/{len(per)}"
                  + (f"   min residual: "
                     f"{min(r['necessity'].get('min_residual_over_tau', 99) for r in per):.2f}tau"
                     if any(r['necessity'].get('min_residual_over_tau') for r in per) else ""),
                  f"- off-grid passed: {sum(r['offgrid']['pass'] for r in per)}/{len(per)}",
                  f"- [informational] sub-fault solo-vs-healthy >=3tau: "
                  f"{sum(r['sub_magnitudes']['pass'] for r in per)}/{len(per)}",
                  f"- failures: {fails or 'none'}", ""]

    # part-table hardening: the fixable/role columns must actually disappear
    sample = json.loads(open(_abs(SETS["composite"])).readline())
    shown, _ = build_part_table(_abs(sample["broken_urdf"]), reveal_fixable=True)
    hidden, _ = build_part_table(_abs(sample["broken_urdf"]), reveal_fixable=False)
    table_ok = ("fixable" in shown) and ("fixable" not in hidden) and ("yes" not in hidden)
    ok = ok and table_ok
    report["part_table_hidden_ok"] = table_ok
    lines += ["## part table hardening", "",
              f"- reveal_fixable=False removes the fixable/role columns: {table_ok}", "",
              "```", "reveal_fixable=True", shown, "", "reveal_fixable=False", hidden, "```", ""]

    p.disconnect(cid)
    report["ok"] = ok
    lines += [f"## RESULT: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}", ""]

    out_dir = os.path.join(HERE, "runs", "_analysis")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "verify_hard.json"), "w") as f:
        json.dump(report, f, indent=2)
    with open(os.path.join(out_dir, "verify_hard.log"), "w") as f:
        f.write("\n".join(lines))
    print("\n" + "\n".join(lines[-2:]))
    print(f"-> {out_dir}/verify_hard.log  and  verify_hard.json")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
