#!/usr/bin/env python
"""
Part-collision check: do any two parts of the fridge interpenetrate?

A repair can land a door close to correct yet still leave it passing through the body or the
other door. This module measures the deepest interpenetration over ALL distinct part (link) pairs
at a configuration, and gates a repair on it RELATIVE to the fridge's own healthy baseline.

Relative, not absolute, because the source meshes are imperfect: measured across all 43 fridges at
closed pose, 36/43 have <5 mm part-pair penetration but 7 self-overlap up to 57 mm (their two doors
touch in the middle). An absolute rule would permanently flag those 7 healthy fridges. Comparing a
candidate against the SAME fridge's healthy penetration cancels that baseline out.
"""
import os
import sys

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import _revolute_joints, _joint_index_by_name   # noqa: E402
from parts import list_parts                                # noqa: E402

FLAGS = p.URDF_USE_SELF_COLLISION          # NOT ...EXCLUDE_PARENT -- part-vs-part is the signal
MARGIN_M = 0.005                           # 5 mm, matches the closing seal tolerance


def _link_part_names(urdf_path):
    """PyBullet link index -> friendly part name (body / door_N_side); base link = -1."""
    names = {-1: "base"}
    for i, part in enumerate(list_parts(urdf_path)):
        # list_parts is in URDF joint order, which matches PyBullet joint/link indexing.
        names[i] = part["name"]
    return names


def max_part_penetration(urdf, joint_angles=None, client=None):
    """Deepest interpenetration over all distinct link pairs at a configuration.

    joint_angles: {joint_index: radians}; joints not listed (and the default None) are set to 0
    (closed pose). Returns {pen_mm >= 0, worst_pair_links, worst_pair_names}.
    """
    own = client is None
    cid = p.connect(p.DIRECT) if own else client
    body = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, flags=FLAGS, physicsClientId=cid)
    for j in range(p.getNumJoints(body, physicsClientId=cid)):
        ang = 0.0 if joint_angles is None else joint_angles.get(j, 0.0)
        p.resetJointState(body, j, ang, physicsClientId=cid)
    p.performCollisionDetection(physicsClientId=cid)

    deepest = 0.0
    worst = None
    for c in p.getContactPoints(bodyA=body, bodyB=body, physicsClientId=cid):
        la, lb = c[3], c[4]
        if la == lb:                       # a link vs itself is not a part-part collision
            continue
        if c[8] < deepest:
            deepest = c[8]
            worst = (la, lb)

    if own:
        p.removeBody(body, physicsClientId=cid)
        p.disconnect(cid)
    else:
        p.removeBody(body, physicsClientId=cid)

    names = _link_part_names(urdf)
    pair_names = None if worst is None else (names.get(worst[0], worst[0]),
                                             names.get(worst[1], worst[1]))
    return {"pen_mm": -deepest * 1000.0, "worst_pair_links": worst, "worst_pair_names": pair_names}


def evaluate_part_collision(candidate_urdf, healthy_urdf, margin_m=MARGIN_M,
                            joint_angles=None, client=None):
    """Does the candidate interpenetrate MORE than its healthy baseline (by > margin)?

    Evaluated at closed pose (all doors shut) unless `joint_angles` says otherwise. Returns
    {collides, worst_pen_mm, healthy_pen_mm, excess_mm, worst_pair_names}.
    """
    cand = max_part_penetration(candidate_urdf, joint_angles, client=client)
    healthy = max_part_penetration(healthy_urdf, joint_angles, client=client)
    excess = cand["pen_mm"] - healthy["pen_mm"]
    return {
        "collides": bool(excess > margin_m * 1000.0),
        "worst_pen_mm": round(cand["pen_mm"], 3),
        "healthy_pen_mm": round(healthy["pen_mm"], 3),
        "excess_mm": round(excess, 3),
        "worst_pair_names": cand["worst_pair_names"],
    }


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate_urdf")
    ap.add_argument("--healthy", default=None,
                    help="healthy reference (default: mobility.urdf beside the candidate)")
    args = ap.parse_args()
    healthy = args.healthy or os.path.join(os.path.dirname(args.candidate_urdf), "mobility.urdf")
    print(json.dumps(evaluate_part_collision(args.candidate_urdf, healthy), indent=2))
