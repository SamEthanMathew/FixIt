#!/usr/bin/env python
"""Verify a downloaded FixIt dataset matches the layout the code expects.
Run from the repo root:  python verify_data.py
Expected (per flownet3d/data.py, utils/*, dynamics/*):
  data/<category>/shapes/<split>_before/<shape_id>/new/*.npy
  data/<category>/shapes/<split>_before/<shape_id>/flow/*.npy
  data/<category>/shapes/<split>_before/<shape_id>/instance_segmentation.npy
  data/<category>/shapes/<split>/<shape_id>_<0..4>/answer.json
"""
import os, glob, json, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def main():
    if not os.path.isdir(ROOT):
        print("No data/ directory at", ROOT); return 1
    cats = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)))
    if not cats:
        print("data/ is empty — nothing downloaded yet."); return 1
    print("Categories found:", cats, "\n")
    for cat in cats:
        shapes = os.path.join(ROOT, cat, "shapes")
        print(f"== {cat} ==")
        if not os.path.isdir(shapes):
            print(f"  !! missing {cat}/shapes/  (extraction nesting is wrong)")
            sub = os.listdir(os.path.join(ROOT, cat))
            print(f"     {cat}/ actually contains: {sub[:10]}")
            continue
        splits = sorted(os.listdir(shapes))
        print("  splits:", splits)
        for sp in splits:
            spdir = os.path.join(shapes, sp)
            if not os.path.isdir(spdir):
                continue
            entries = [e for e in os.listdir(spdir) if os.path.isdir(os.path.join(spdir, e))]
            tag = ""
            if sp.endswith("_before") and entries:
                s0 = os.path.join(spdir, entries[0])
                n_new = len(glob.glob(os.path.join(s0, "new", "*.npy")))
                n_flow = len(glob.glob(os.path.join(s0, "flow", "*.npy")))
                has_seg = os.path.exists(os.path.join(s0, "instance_segmentation.npy"))
                tag = f" | sample '{entries[0]}': new={n_new} flow={n_flow} seg={'Y' if has_seg else 'N'}"
            elif entries:  # choice split
                s0 = os.path.join(spdir, entries[0])
                has_ans = os.path.exists(os.path.join(s0, "answer.json"))
                tag = f" | sample '{entries[0]}': answer.json={'Y' if has_ans else 'N'}"
            print(f"    {sp}: {len(entries)} shapes{tag}")
        print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
