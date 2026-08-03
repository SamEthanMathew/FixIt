#!/usr/bin/env python
"""
Functional score for a fridge: can the target door open to 90 degrees without the door
colliding with the body / other door?

Opens the target door 0 -> theta_target in `steps`, holding other doors closed, and detects
self-collision penetration each step (contact[8] < -eps_tol). The collision-free open fraction
is the score. Calibrated on the healthy fleet (calibrate_score.py): clean doors penetrate
0-2 mm and open fully (score 1.0); broken doors jam early (score -> 0). eps_tol = 5 mm.
"""
import math
import pybullet as p

_FLAGS = p.URDF_USE_SELF_COLLISION | p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT


def _revolute_joints(body):
    return [j for j in range(p.getNumJoints(body))
            if p.getJointInfo(body, j)[2] == p.JOINT_REVOLUTE]


def _joint_index_by_name(body, joint_name):
    for j in range(p.getNumJoints(body)):
        if p.getJointInfo(body, j)[1].decode() == joint_name:
            return j
    return None


def functional_score(urdf_path, joint_name, theta_target=math.pi / 2, steps=45,
                     eps_tol=0.005, client=None):
    """Return {score, open_angle_deg, max_penetration_mm} for opening `joint_name`.

    score in [0,1] = fraction of theta_target the door opens before the deepest self-collision
    penetration exceeds eps_tol.
    """
    own = client is None
    cid = p.connect(p.DIRECT) if own else client
    body = p.loadURDF(urdf_path, [0, 0, 0], useFixedBase=1, flags=_FLAGS,
                      physicsClientId=cid)
    doors = _revolute_joints(body)
    target = _joint_index_by_name(body, joint_name)
    if target is None:
        p.removeBody(body, physicsClientId=cid)
        if own:
            p.disconnect(cid)
        raise ValueError(f"joint {joint_name!r} not found / not revolute in {urdf_path}")

    deepest = 0.0
    open_frac = 0.0
    for s in range(steps + 1):
        frac = s / steps
        for jj in doors:
            p.resetJointState(body, jj, theta_target * frac if jj == target else 0.0,
                              physicsClientId=cid)
        p.performCollisionDetection(physicsClientId=cid)
        contacts = p.getContactPoints(bodyA=body, bodyB=body, physicsClientId=cid)
        pen = min((c[8] for c in contacts), default=0.0)
        deepest = min(deepest, pen)
        if pen >= -eps_tol:
            open_frac = frac
        else:
            break

    p.removeBody(body, physicsClientId=cid)
    if own:
        p.disconnect(cid)
    return {
        "score": open_frac,
        "open_angle_deg": open_frac * math.degrees(theta_target),
        "max_penetration_mm": -deepest * 1000.0,
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    ap.add_argument("joint")
    args = ap.parse_args()
    print(functional_score(args.urdf, args.joint))
