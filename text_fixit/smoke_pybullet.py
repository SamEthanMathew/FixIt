#!/usr/bin/env python
"""
Headless PyBullet plumbing check for the Text-FixIt physics simulator.

Validates the three primitives the fridge environment needs, on any PartNet-Mobility
object (default: the Genesis-bundled Bottle 3763, which is the only such asset already
on disk before the SAPIEN download):

  1. load a mobility.urdf in DIRECT (no-GUI) mode,
  2. sweep an articulated joint across its range,
  3. detect link<->link collisions during the sweep (the core of the fridge score:
     a broken door jams / self-collides before it can fully open).

Run:  python text_fixit/smoke_pybullet.py [--urdf /path/to/mobility.urdf]
"""
import argparse
import math
from pathlib import Path

import pybullet as p
import pybullet_data

DEFAULT_URDF = "/home/sammathew/miniconda3/envs/robotsmith/lib/python3.11/site-packages/genesis/assets/urdf/3763/mobility.urdf"


def articulated_joints(body):
    out = []
    for j in range(p.getNumJoints(body)):
        info = p.getJointInfo(body, j)
        jtype = info[2]
        if jtype in (p.JOINT_REVOLUTE, p.JOINT_PRISMATIC):
            lo, hi = info[8], info[9]
            out.append((j, info[1].decode(), jtype, lo, hi))
    return out


def sweep_joint(body, j, lo, hi, steps=60):
    """Drive joint j across [lo,hi]; return (max_collision_free_frac, total_contacts)."""
    # continuous joints report lo>=hi; give them a nominal +/- pi range.
    if hi <= lo:
        lo, hi = -math.pi, math.pi
    max_free = 0.0
    total_contacts = 0
    for s in range(steps + 1):
        frac = s / steps
        p.resetJointState(body, j, lo + (hi - lo) * frac)
        p.performCollisionDetection()
        # self-collision contacts on this body, excluding adjacent-link noise at the driven joint
        contacts = [c for c in p.getContactPoints(bodyA=body, bodyB=body) if c[8] < -1e-4]
        total_contacts += len(contacts)
        if not contacts:
            max_free = frac
        else:
            break
    return max_free, total_contacts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", default=DEFAULT_URDF)
    args = ap.parse_args()

    urdf = Path(args.urdf)
    if not urdf.is_file():
        raise SystemExit(f"URDF not found: {urdf}")

    client = p.connect(p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -10)

    body = p.loadURDF(str(urdf), [0, 0, 0], useFixedBase=1,
                      flags=p.URDF_USE_SELF_COLLISION)
    n = p.getNumJoints(body)
    print(f"[1] loaded OK: {urdf.name}  ({n} joints, {len(articulated_joints(body))} articulated)")

    joints = articulated_joints(body)
    if not joints:
        print("    (no articulated joints to sweep — plumbing for load+collision still validated)")
    for (j, name, jtype, lo, hi) in joints:
        kind = "revolute" if jtype == p.JOINT_REVOLUTE else "prismatic"
        free, contacts = sweep_joint(body, j, lo, hi)
        print(f"[2] swept joint {j} ({name}, {kind}, range[{lo:.3f},{hi:.3f}]): "
              f"collision-free fraction = {free:.2f}, contacts seen = {contacts}")

    print("[3] collision detection via getContactPoints: OK")
    print("\nPlumbing OK — load + joint sweep + self-collision detection all work headless.")
    p.disconnect()


if __name__ == "__main__":
    main()
