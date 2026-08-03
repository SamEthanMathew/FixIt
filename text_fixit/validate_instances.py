#!/usr/bin/env python
"""
Benchmark integrity check for the Text-FixIt instance sets.

Independently re-runs the evaluation contract over every saved instance and asserts the
invariants the benchmark depends on:

  * BROKEN fails      -- the broken URDF must NOT pass (deviation > tau, i.e. genuinely broken)
  * SOLVABLE          -- applying the stored gt_fix to the broken URDF must PASS the full contract
  * MARGIN            -- broken deviation >= BROKEN_MARGIN * tau
  * REVERSIBLE        -- gt-fixed deviation <= 0.1 * tau (essentially 0)
  * PHYSICS ACHIEVABLE -- the healthy door closes (else the AND criterion is unsatisfiable)

Run this after regenerating instances, or as a regression check. It reads only the JSONL and the
referenced URDFs -- it does not trust the fields written at generation time, it recomputes them.

    python text_fixit/validate_instances.py --split test
    python text_fixit/validate_instances.py --split all
"""
import argparse
import json
import os
import sys

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corruption as corr                 # noqa: E402  (BROKEN_MARGIN)
from close_eval import evaluate_closing   # noqa: E402
from evaluation import evaluate_repair    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def validate_split(split, cid):
    path = os.path.join(HERE, "data", f"instances_{split}.jsonl")
    if not os.path.isfile(path):
        print(f"  (no file for split={split})")
        return True
    records = [json.loads(l) for l in open(path)]
    fails = []
    stats = {"physics_verified": 0, "n": len(records), "caught_closing": 0,
             "caught_collision": 0, "caught_either": 0}
    healthy_closes_cache = {}

    for r in records:
        hu = os.path.join(HERE, r["healthy_urdf"])
        bu = os.path.join(HERE, r["broken_urdf"])
        jn, ln = r["joint"], r["link"]

        if not os.path.isfile(bu):
            fails.append((r["id"], "broken URDF missing on disk"))
            continue

        rb = evaluate_repair(bu, hu, jn, ln, client=cid)
        fixed = corr.apply(bu, r["gt_fix"], "_val_fix.urdf")
        rf = evaluate_repair(fixed, hu, jn, ln, client=cid)
        os.remove(fixed)

        hc = healthy_closes_cache.get((hu, jn))
        if hc is None:
            hc = healthy_closes_cache[(hu, jn)] = evaluate_closing(hu, jn, client=cid)["closes"]

        if rb["PASS"]:
            fails.append((r["id"], "BROKEN passes the contract"))
        if not rf["PASS"]:
            fails.append((r["id"], f"UNSOLVABLE: gt_fix fails (within={rf['within_tol']} closes={rf['closes']})"))
        if rb["deviation_mm"] < corr.BROKEN_MARGIN * rb["tau_mm"] - 1e-6:
            fails.append((r["id"], f"below margin: {rb['deviation_mm']:.1f} < {corr.BROKEN_MARGIN}x{rb['tau_mm']:.1f}"))
        if rf["deviation_mm"] > 0.1 * rf["tau_mm"] + 1e-6:
            fails.append((r["id"], f"not reversible: gt-fix dev {rf['deviation_mm']:.1f}mm"))
        if not hc:
            fails.append((r["id"], "healthy door does not close (unsolvable AND-criterion)"))
        if not rb["closes"]:
            stats["physics_verified"] += 1
        # standalone detection: which physical gate(s) catch this broken instance?
        if not rb["closes"]:
            stats["caught_closing"] += 1
        if rb["collides"]:
            stats["caught_collision"] += 1
        if (not rb["closes"]) or rb["collides"]:
            stats["caught_either"] += 1

    ok = not fails
    tag = "OK" if ok else f"{len(fails)} FAILURES"
    n = max(1, stats["n"])
    print(f"  split={split:5s}  n={stats['n']:4d}  physics_verified={stats['physics_verified']:3d} "
          f"({100*stats['physics_verified']//n}%)  -> {tag}")
    print(f"    physical-gate detection: closing={stats['caught_closing']} ({100*stats['caught_closing']//n}%)  "
          f"collision={stats['caught_collision']} ({100*stats['caught_collision']//n}%)  "
          f"either={stats['caught_either']} ({100*stats['caught_either']//n}%)")
    for iid, why in fails[:20]:
        print(f"      FAIL {iid}: {why}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    args = ap.parse_args()
    splits = ["test", "train"] if args.split == "all" else [args.split]
    cid = p.connect(p.DIRECT)
    all_ok = all(validate_split(s, cid) for s in splits)
    p.disconnect(cid)
    print("\nALL INVARIANTS HOLD" if all_ok else "\nINTEGRITY CHECK FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
