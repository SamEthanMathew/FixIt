#!/usr/bin/env python
"""
PyBullet closing test: drive the BROKEN door from open to shut and see whether it seats.

Rationale: opening a door swings it into free space, so a mis-sized/mis-placed door never
collides on the way open (verified empirically). Closing is the discriminating motion -- a
door that is tilted, shifted toward the body, or too deep cannot seat against the frame and
interferes before it reaches 0 degrees.

Two details matter:
  * the actuated joint is the CORRUPTED part's joint (not just "some door");
  * we deliberately do NOT use URDF_USE_SELF_COLLISION_EXCLUDE_PARENT here, because the
    door-vs-body contact is exactly the signal. The healthy door's resting seal contact is
    handled with a penetration-depth tolerance instead of by excluding the pair.

Contacts are filtered to those involving the target door link, so we measure interference
caused by the broken part rather than unrelated geometry elsewhere on the fridge.
"""
import math
import os
import sys

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import _joint_index_by_name, _revolute_joints  # noqa: E402

FLAGS = p.URDF_USE_SELF_COLLISION          # NOT ...EXCLUDE_PARENT -- see module docstring
START_DEG = 90.0
STEPS = 60
EPS_M = 0.005                              # 5 mm penetration tolerance (seal contact)


def closing_profile(urdf, joint_name, start_deg=START_DEG, steps=STEPS, client=None,
                    others="closed"):
    """Sweep the target door from `start_deg` to 0 and record penetration at each angle.

    `others` controls the other doors while the target one closes:
      "closed" -- (default) the realistic fully-shut fridge. This is the functional question
                  we actually care about: does the fridge shut? Detected 28% of breaks.
      "open"   -- others parked out of the way, isolating the target door against the body.
                  Useful as a diagnostic, but it detects FEWER breaks (14%) and is no more
                  specific (10%): a broken door obstructs its neighbour wherever it is parked,
                  so interference is genuinely not exclusive to the actuated part.

    Returns (profile, target_link) where profile is a list of (angle_deg, penetration_m<=0).
    """
    own = client is None
    cid = p.connect(p.DIRECT) if own else client
    body = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, flags=FLAGS, physicsClientId=cid)
    doors = _revolute_joints(body)
    target = _joint_index_by_name(body, joint_name)
    if target is None:
        p.removeBody(body, physicsClientId=cid)
        if own:
            p.disconnect(cid)
        raise ValueError(f"joint {joint_name!r} not revolute in {urdf}")

    park = math.radians(start_deg) if others == "open" else 0.0
    profile = []
    for s in range(steps + 1):
        ang = math.radians(start_deg) * (1.0 - s / steps)     # open -> shut
        for jj in doors:
            p.resetJointState(body, jj, ang if jj == target else park, physicsClientId=cid)
        p.performCollisionDetection(physicsClientId=cid)
        pen = 0.0
        for c in p.getContactPoints(bodyA=body, bodyB=body, physicsClientId=cid):
            la, lb = c[3], c[4]
            if la == lb:
                continue
            if la != target and lb != target:       # only interference from the broken part
                continue
            pen = min(pen, c[8])
        profile.append((math.degrees(ang), pen))

    p.removeBody(body, physicsClientId=cid)
    if own:
        p.disconnect(cid)
    return profile, target


def evaluate_closing(urdf, joint_name, eps=EPS_M, start_deg=START_DEG, steps=STEPS,
                     shut_deg=5.0, client=None, others="closed"):
    """Can the broken door close? Returns metrics about how far shut it gets.

    closed_angle_deg : smallest angle reached before penetration exceeds `eps`
                       (0 = fully shut, larger = jams further open)
    closes           : True if it seats within `shut_deg` of fully shut
    """
    profile, _ = closing_profile(urdf, joint_name, start_deg, steps, client, others)
    closed_angle = start_deg
    for ang, pen in profile:                        # profile runs open -> shut
        if pen >= -eps:
            closed_angle = ang
        else:
            break
    pen_at_shut = profile[-1][1]
    return {
        "closed_angle_deg": closed_angle,
        "closes": closed_angle <= shut_deg,
        "max_pen_at_shut_mm": -pen_at_shut * 1000.0,
        "max_pen_overall_mm": -min(pn for _, pn in profile) * 1000.0,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    ap.add_argument("joint")
    args = ap.parse_args()
    print(evaluate_closing(args.urdf, args.joint))
