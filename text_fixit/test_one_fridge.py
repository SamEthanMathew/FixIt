#!/usr/bin/env python
"""
Single-fridge smoke test of the broken-fridge generation system.

For one base fridge: print its part segmentation, then break one door three ways
(scale / translate / rotate), score healthy vs broken vs ground-truth-fixed, and render
before/after images so we can eyeball what the corruption looks like.

    python text_fixit/test_one_fridge.py [--base 10489] [--door 0]
"""
import argparse
import math
import os
import sys

import numpy as np
import pybullet as p
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts as parts_mod          # noqa: E402
import corruption as corr          # noqa: E402
import geom                        # noqa: E402
from score import _joint_index_by_name, _revolute_joints  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets", "partnet_mobility")


def _scene_aabb(body, cid):
    lo = np.array([1e9, 1e9, 1e9])
    hi = -lo
    for link in range(-1, p.getNumJoints(body, physicsClientId=cid)):
        amin, amax = p.getAABB(body, link, physicsClientId=cid)
        lo = np.minimum(lo, amin)
        hi = np.maximum(hi, amax)
    return lo, hi


def render(urdf, joint_name, angle, out_png, res=640, yaw=45, pitch=-30):
    cid = p.connect(p.DIRECT)
    body = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, physicsClientId=cid)
    doors = _revolute_joints(body)
    target = _joint_index_by_name(body, joint_name)
    for jj in doors:
        p.resetJointState(body, jj, angle if jj == target else 0.0, physicsClientId=cid)
    p.performCollisionDetection(physicsClientId=cid)
    lo, hi = _scene_aabb(body, cid)
    center = (lo + hi) / 2.0
    diag = float(np.linalg.norm(hi - lo))
    view = p.computeViewMatrixFromYawPitchRoll(center.tolist(), 1.6 * diag, yaw, pitch, 0, 2)
    proj = p.computeProjectionMatrixFOV(55, 1.0, 0.01, 100)
    _, _, rgb, _, _ = p.getCameraImage(res, res, view, proj, renderer=p.ER_TINY_RENDERER,
                                       physicsClientId=cid)
    img = np.reshape(np.array(rgb, dtype=np.uint8), (res, res, 4))[:, :, :3]
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    Image.fromarray(img).save(out_png)
    p.disconnect(cid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="10489")
    ap.add_argument("--door", type=int, default=0, help="index into the corruptible parts list")
    args = ap.parse_args()

    shape_dir = os.path.join(ASSETS, args.base)
    urdf = os.path.join(shape_dir, "mobility.urdf")
    run_dir = os.path.join(HERE, "runs", "test_one", args.base)

    # --- Step 1: part segmentation ---
    all_parts = parts_mod.list_parts(urdf)
    print(f"\n=== Part segmentation for fridge {args.base} ===")
    for pt in all_parts:
        flag = "CORRUPTIBLE" if pt["corruptible"] else "fixed/body "
        print(f"  [{flag}] {pt['name']:16s} link={pt['link']} joint={pt['joint']} "
              f"({pt['joint_type']}) axis={pt['joint_axis']} meshes={len(pt['mesh_files'])}")

    doors = [pt for pt in all_parts if pt["corruptible"]]
    if not doors:
        sys.exit("no corruptible door parts found")
    part = doors[args.door]
    jn = part["joint"]
    ln = part["link"]
    print(f"\nTarget part: {part['name']} (joint {jn}, link {ln})")

    # --- Step 3: healthy sanity (self-comparison must be perfect) ---
    self_chk = geom.geometric_score(urdf, urdf, jn, ln)
    print(f"\nHEALTHY self-check: score={self_chk['score']:.3f} error={self_chk['error_mm']:.2f}mm "
          f"(door diag={self_chk['diag_mm']:.0f}mm) -> should be score=1.000, error~0")
    render(urdf, jn, 0.0, os.path.join(run_dir, "healthy_closed.png"))
    render(urdf, jn, math.pi / 2, os.path.join(run_dir, "healthy_open90.png"))

    # --- Step 2+4: break three ways, score geometrically vs healthy, render ---
    print(f"\n{'type':10s} {'corruption':38s} {'BROKEN vs healthy':>24s} {'GT-FIXED vs healthy':>24s}")
    print("-" * 100)
    for ctype in ("scale", "translate", "rotate"):
        spec, fix = corr.sample_corruption(urdf, part, index=0, ctype=ctype)
        broken = corr.apply(urdf, spec, f"broken_{ctype}.urdf")
        fixed = corr.apply(broken, fix, f"fixed_{ctype}.urdf")
        bs = geom.geometric_score(broken, urdf, jn, ln)
        fs = geom.geometric_score(fixed, urdf, jn, ln)
        cdir = os.path.join(run_dir, ctype)
        render(broken, jn, 0.0, os.path.join(cdir, "broken_closed.png"))
        render(broken, jn, math.pi / 2, os.path.join(cdir, "broken_open90.png"))
        print(f"{ctype:10s} {corr.describe(spec):38s} "
              f"score={bs['score']:.2f} error={bs['error_mm']:7.1f}mm   "
              f"score={fs['score']:.2f} error={fs['error_mm']:6.1f}mm")

    print(f"\nImages under: {run_dir}")
    print("Expect: healthy self-check score=1.0; BROKEN score low (large error); "
          "GT-FIXED score~1.0 (error~0).")


if __name__ == "__main__":
    main()
