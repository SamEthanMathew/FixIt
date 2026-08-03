#!/usr/bin/env python
"""
Batch-generate and validate broken-fridge instances under the evaluation contract.

Every emitted instance satisfies all of:

  1. deviation(broken)   >= BROKEN_MARGIN * tau   -- unambiguously broken (guaranteed by the
                                                     adaptive magnitude search in corruption.py)
  2. deviation(gt_fixed) <= 0.1 * tau             -- exactly reversible
  3. closes(healthy, target joint) is True        -- the physical half of the pass criterion must
                                                     be ACHIEVABLE. ~6/22 fridge doors have source
                                                     meshes that already interpenetrate and never
                                                     close; instances built on those would be
                                                     unsolvable even with a perfect repair.
  4. gt_fixed PASSes the full contract            -- no instance is unsolvable, checked explicitly

Instances where the break also stops the door closing are tagged `physics_verified` (~28%): those
carry a real physical signal on top of the geometric one.

    python text_fixit/instances.py --split test --per-combo 3
"""
import argparse
import json
import os
import sys

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corruption as corr          # noqa: E402
import geom                        # noqa: E402
from close_eval import evaluate_closing   # noqa: E402
from evaluation import evaluate_repair    # noqa: E402
from parts import corruptible_parts       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets", "partnet_mobility")
IDS = os.path.join(HERE, "data", "fridge_ids.json")
CTYPES = ("scale", "translate", "rotate")


def build(split, per_combo, out_path):
    ids = json.load(open(IDS))
    shape_ids = ids["train"] + ids["test"] if split == "all" else ids[split]

    cid = p.connect(p.DIRECT)
    kept = []
    rej = {"healthy_wont_close": 0, "no_margin": 0, "not_reversible": 0, "unsolvable": 0}
    skipped_doors = []

    for base in shape_ids:
        urdf = os.path.join(ASSETS, base, "mobility.urdf")
        if not os.path.isfile(urdf):
            continue
        for part in corruptible_parts(urdf):
            jn, ln = part["joint"], part["link"]

            # Gate 3: the physical target must be achievable on this door.
            if not evaluate_closing(urdf, jn, client=cid)["closes"]:
                rej["healthy_wont_close"] += per_combo * len(CTYPES)
                skipped_doors.append(f"{base}/{ln}")
                continue

            for ctype in CTYPES:
                for index in range(per_combo):
                    iid = f"{base}_{ln}_{ctype}_{index}"
                    spec, fix = corr.sample_corruption(urdf, part, index, ctype, client=cid)
                    if spec is None:                       # gate 1
                        rej["no_margin"] += 1
                        continue

                    broken = corr.apply(urdf, spec, f"_inst_{iid}.urdf")
                    rb = evaluate_repair(broken, urdf, jn, ln, client=cid)
                    tmp = corr.apply(broken, fix, "_tmp_fixcheck.urdf")
                    rf = evaluate_repair(tmp, urdf, jn, ln, client=cid)
                    os.remove(tmp)

                    if rf["deviation_mm"] > 0.1 * rf["tau_mm"]:          # gate 2
                        rej["not_reversible"] += 1
                        os.remove(broken)
                        continue
                    if not rf["PASS"]:                                    # gate 4
                        rej["unsolvable"] += 1
                        os.remove(broken)
                        continue

                    kept.append({
                        "id": iid,
                        "base": base,
                        "split": split if split != "all" else
                                 ("test" if base in ids["test"] else "train"),
                        "part_name": part["name"],
                        "link": ln,
                        "joint": jn,
                        "broken_urdf": os.path.relpath(broken, HERE),
                        "healthy_urdf": os.path.relpath(urdf, HERE),
                        "corruption": spec,
                        "gt_fix": fix,
                        "tau_mm": rb["tau_mm"],
                        "broken_deviation_mm": rb["deviation_mm"],
                        "broken_score": rb["score"],
                        "broken_pass": rb["PASS"],
                        "gt_fixed_deviation_mm": rf["deviation_mm"],
                        "gt_fixed_pass": rf["PASS"],
                        "closes_healthy": True,
                        "closes_broken": rb["closes"],
                        "collides_broken": rb["collides"],
                        "collision_excess_mm": rb["collision_excess_mm"],
                        "collision_pair": rb["collision_pair"],
                        "physics_verified": (not rb["closes"]) or rb["collides"],
                    })
    p.disconnect(cid)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        for r in kept:
            f.write(json.dumps(r) + "\n")

    print(f"\nsplit={split}  shapes={len(shape_ids)}  kept={len(kept)}")
    print(f"  rejected: {rej}")
    if skipped_doors:
        print(f"  doors skipped (healthy never closes, gate 3): {len(skipped_doors)} -> "
              f"{sorted(set(skipped_doors))}")
    if kept:
        dev = [r["broken_deviation_mm"] for r in kept]
        ratio = [r["broken_deviation_mm"] / r["tau_mm"] for r in kept]
        pv = sum(r["physics_verified"] for r in kept)
        by = {c: sum(1 for r in kept if r["corruption"]["type"] == c) for c in CTYPES}
        print(f"  deviation: min={min(dev):.0f}mm mean={sum(dev)/len(dev):.0f}mm max={max(dev):.0f}mm")
        print(f"  deviation/tau: min={min(ratio):.1f}x mean={sum(ratio)/len(ratio):.1f}x "
              f"(floor {corr.BROKEN_MARGIN}x)")
        print(f"  physics_verified (break stops closing OR collides): {pv}/{len(kept)} ({100*pv/len(kept):.0f}%)")
        print(f"  by type: {by}   distinct shapes: {len({r['base'] for r in kept})}")
        assert all(r["gt_fixed_pass"] for r in kept), "an instance is unsolvable"
        assert not any(r["broken_pass"] for r in kept), "a broken instance already passes"
        print("  assertions OK: every instance is broken-and-solvable")
    print(f"  -> {out_path}")
    return kept


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "test", "all"], default="test")
    ap.add_argument("--per-combo", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(HERE, "data", f"instances_{args.split}.jsonl")
    build(args.split, args.per_combo, out)
