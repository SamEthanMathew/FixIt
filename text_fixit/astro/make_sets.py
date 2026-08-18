#!/usr/bin/env python
"""
Split-aware instance generation for the ASTRO stage.

`instances_hard.py --set easy` cycles the WHOLE shape pool and only records which split each
instance landed in, so a run gets a train/test mixture it cannot control. For SFT that is not
good enough: the held-out set must contain no shape the model trained on, and the training set
wants many instances per train shape. This builds each split separately, from
`data/fridge_ids.json` (30 train / 13 test, split by shape, 0 overlap).

Everything else -- corruption ranges, the five solvability gates, the oracle round-trip -- is
`instances_hard.build_control` unchanged, so these instances are drop-in comparable with
`instances_std30.jsonl` (tau_frac 0.015, broken_margin 3.0, default magnitude ranges).

    FIXIT_TAU_FRAC=0.015 python text_fixit/astro/make_sets.py \
        --split train --per-type 100 --out data/instances_astro_train.jsonl
    FIXIT_TAU_FRAC=0.015 python text_fixit/astro/make_sets.py \
        --split test  --per-type 35  --out data/instances_astro_heldout.jsonl

Bases are CYCLED with an incrementing seed once the pool is exhausted: `build_control` seeds on
(base, ctype, seed) and ids embed the seed, so a second pass over the same 30 shapes yields
genuinely different corruptions rather than duplicates. Instances sharing a base are correlated,
so the per-base count is reported -- the effective n is below the nominal n.
"""
import argparse
import json
import os
import random
import sys

import pybullet as p

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import corruption as corr                        # noqa: E402
import geom                                      # noqa: E402
from instances_hard import (CTYPES, TARGET_TAU_FRAC, build_control,  # noqa: E402
                            inventory)


def build_split(split, per_type, seed0, cid, verbose=True):
    """`per_type` instances of each corruption type, drawn only from `split`'s shapes."""
    inv, split_of = inventory(cid)
    pool = sorted(b for b in inv if split_of[b] == split)
    if not pool:
        raise SystemExit(f"no usable shapes in split {split!r}")
    rng = random.Random(seed0)
    rng.shuffle(pool)
    if verbose:
        print(f"{split}: {len(pool)} usable shapes, targeting {per_type} per type "
              f"({per_type * len(CTYPES)} total)", flush=True)

    rows = []
    for ci, ctype in enumerate(CTYPES):
        # Stagger each fault type's entry point into the pool. Restarting every type at pool[0]
        # means that whenever per_type < len(pool) all three types land on the SAME few shapes, and
        # the set ends up correlated in threes instead of spread across the split.
        off = (ci * len(pool)) // len(CTYPES)
        tpool = pool[off:] + pool[:off]
        got, k, dropped = 0, 0, 0
        # cap the attempts so an un-corruptible type cannot spin forever
        while got < per_type and k < len(tpool) * 8:
            base = tpool[k % len(tpool)]
            seed_i = seed0 + (k // len(tpool))    # new seed on each pass over the pool
            k += 1
            rec = build_control(base, inv[base], split_of[base], seed_i, ctype, cid)
            if rec is None:
                dropped += 1
                continue
            rows.append(rec)
            got += 1
            if verbose and got % 10 == 0:
                print(f"  {ctype}: {got}/{per_type}", flush=True)
        if got < per_type:
            print(f"  UNDER-FILLED {ctype}: {got}/{per_type} (recorded, not padded)")
        if verbose:
            print(f"  {ctype}: {got} kept, {dropped} dropped by the gates", flush=True)
    return rows


def report(rows, path, split):
    from collections import Counter
    bases = Counter(r["base"] for r in rows)
    types = Counter(r["fault_types"][0] for r in rows)
    dev = [r["broken_deviation_mm"] / r["tau_mm"] for r in rows]
    print(f"\n{split}: {len(rows)} instances over {len(bases)} bases -> {path}")
    print(f"  types: {dict(types)}")
    print(f"  per base: min={min(bases.values())} max={max(bases.values())} "
          f"(correlated; effective n < {len(rows)})")
    print(f"  deviation/tau: min={min(dev):.1f}x median={sorted(dev)[len(dev)//2]:.1f}x "
          f"max={max(dev):.1f}x  (floor {corr.BROKEN_MARGIN}x)")
    # The same assertions instances_hard._write_sets makes, minus the distinct-base one (we
    # deliberately reuse bases here).
    assert all(r["gt_fixed_pass"] for r in rows), "an instance is unsolvable"
    assert not any(r["broken_pass"] for r in rows), "an instance already passes"
    assert all(abs(r["tau_frac"] - geom.TAU_FRAC) < 1e-12 for r in rows), "tau mismatch"
    assert all(r["split"] == split for r in rows), "split leak"
    print("  assertions OK: broken, solvable, tau matches, no split leak")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["train", "test"])
    ap.add_argument("--per-type", type=int, required=True,
                    help="instances per corruption type (x3 types = total)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True, help="path relative to text_fixit/, or absolute")
    ap.add_argument("--allow-default-tau", action="store_true")
    args = ap.parse_args()

    if not args.allow_default_tau and abs(geom.TAU_FRAC - TARGET_TAU_FRAC) > 1e-12:
        raise SystemExit(f"TAU_FRAC is {geom.TAU_FRAC}, expected {TARGET_TAU_FRAC}. "
                         f"Run with FIXIT_TAU_FRAC={TARGET_TAU_FRAC} so these instances are "
                         f"comparable with instances_std30.jsonl.")

    out = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
    cid = p.connect(p.DIRECT)
    try:
        rows = build_split(args.split, args.per_type, args.seed, cid)
    finally:
        p.disconnect(cid)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    report(rows, out, args.split)


if __name__ == "__main__":
    main()
