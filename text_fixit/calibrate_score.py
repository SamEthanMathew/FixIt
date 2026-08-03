#!/usr/bin/env python
"""
Calibrate the fridge functional score on the HEALTHY fleet.

For every downloaded fridge, open each revolute (door) joint 0 -> 90 deg (others held
closed) and record the deepest link<->link penetration seen during the swing. A healthy
door should swing nearly freely, so the distribution of healthy max-penetration tells us
the tolerance epsilon that separates "resting mesh overlap" from a real broken-door jam.
"""
import glob, math, os, statistics
import pybullet as p

ASSETS = os.path.join(os.path.dirname(__file__), "assets", "partnet_mobility")
THETA_TARGET = math.pi / 2   # 90 deg functional open target
STEPS = 45

def door_joints(b):
    return [j for j in range(p.getNumJoints(b)) if p.getJointInfo(b, j)[2] == p.JOINT_REVOLUTE]

def max_pen_during_open(b, target, doors, flags_exclude_parent):
    """Return (max_penetration_depth, openable_fraction) opening `target` door to 90deg."""
    lo = p.getJointInfo(b, target)[8]
    hi = p.getJointInfo(b, target)[9]
    # door range is 0..pi; open toward the sign that increases |angle| up to 90deg
    end = THETA_TARGET if hi >= THETA_TARGET else (hi if hi > 0 else -THETA_TARGET)
    deepest = 0.0
    openable = 0.0
    for s in range(STEPS + 1):
        frac = s / STEPS
        for jj in doors:
            p.resetJointState(b, jj, end * frac if jj == target else 0.0)
        p.performCollisionDetection()
        pen = min([c[8] for c in p.getContactPoints(bodyA=b, bodyB=b)], default=0.0)
        deepest = min(deepest, pen)
        if pen > -1e9:  # track how far it opens under a loose 5mm tol
            if pen >= -0.005:
                openable = frac
    return deepest, openable

def run(flags, label):
    depths = []
    print(f"\n=== flags: {label} ===")
    for urdf in sorted(glob.glob(f"{ASSETS}/*/mobility.urdf")):
        mid = urdf.split("/")[-2]
        b = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, flags=flags)
        ds = door_joints(b)
        per = []
        for j in ds:
            d, frac = max_pen_during_open(b, j, ds, flags)
            per.append((j, d, frac))
            depths.append(-d)  # store as positive depth
        p.removeBody(b)
        summ = ", ".join(f"j{j}:pen={d*1000:.1f}mm,open@5mm={frac*90:.0f}deg" for j, d, frac in per)
        print(f"  {mid} ({len(ds)} doors): {summ}")
    depths.sort()
    if depths:
        print(f"\n  healthy max-penetration (mm): min={min(depths)*1000:.1f} "
              f"median={statistics.median(depths)*1000:.1f} "
              f"p90={depths[int(0.9*len(depths))-1]*1000:.1f} max={max(depths)*1000:.1f}")

p.connect(p.DIRECT)
run(p.URDF_USE_SELF_COLLISION | p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT, "self_collision + exclude_parent")
p.disconnect()
