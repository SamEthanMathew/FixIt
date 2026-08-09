#!/usr/bin/env python
"""
Geometric functional score: how close is a (proposed-fixed) fridge door to the healthy door?

The FixIt task is to choose the transform that restores the object. Since we generate every
break from a known-healthy base, the ground truth is the healthy door's geometry. We score a
candidate URDF by the Chamfer distance between its target door's world-space points (at closed
pose) and the healthy door's world-space points. 0 = perfect restoration; it grows as the door
is left mis-placed / mis-sized / mis-oriented.

Getting the door's world points via PyBullet getLinkState automatically reflects all three
corruption types: translate/rotate change the link's world pose; scale changes the mesh scale.
"""
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pybullet as p
from scipy.spatial import cKDTree

# Tolerance is defined RELATIVE to the part, so one constant works across large/small fridges
# and 1-door/3-door shapes: tau = TAU_FRAC * door bbox diagonal (~20 mm on a typical 800 mm door).
#
# Overridable via FIXIT_TAU_FRAC so the hard benchmark can tighten it (0.015) WITHOUT changing the
# default -- every pre-existing run stays byte-reproducible at 0.025. Instances record the tau_frac
# they were generated under and env.reset asserts the running value matches, so a generation/eval
# mismatch is a loud failure rather than a silently mis-scored run.
TAU_FRAC = float(os.environ.get("FIXIT_TAU_FRAC", 0.025))


def tolerance(diag_m):
    """Repair tolerance (meters) for a part whose bbox diagonal is `diag_m`."""
    return TAU_FRAC * diag_m


def _floats(s, default):
    return [float(x) for x in s.split()] if s else list(default)


def _rpy_matrix(rpy):
    r, pt, y = rpy
    cr, sr = np.cos(r), np.sin(r)
    cp, sp = np.cos(pt), np.sin(pt)
    cy, sy = np.cos(y), np.sin(y)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx           # URDF fixed-axis roll(x)->pitch(y)->yaw(z)


def _origin_matrix(xyz, rpy):
    T = np.eye(4)
    T[:3, :3] = _rpy_matrix(rpy)
    T[:3, 3] = xyz
    return T


def axis_rotation(axis, theta):
    c, s = np.cos(theta), np.sin(theta)
    if axis == 0:
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 1:
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def matrix_to_rpy(R):
    """Inverse of _rpy_matrix (URDF fixed-axis roll->pitch->yaw)."""
    pitch = np.arctan2(-R[2, 0], np.hypot(R[2, 1], R[2, 2]))
    roll = np.arctan2(R[2, 1], R[2, 2])
    yaw = np.arctan2(R[1, 0], R[0, 0])
    return [float(roll), float(pitch), float(yaw)]


def rpy_matrix(rpy):
    return _rpy_matrix(rpy)


def _load_obj_vertices(path):
    verts = []
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                verts.append([float(x) for x in line.split()[1:4]])
    return np.asarray(verts, dtype=np.float64)


def _link_visual_meshes(urdf_path, link_name):
    """Yield (mesh_abs_path, origin_xyz[3], origin_rpy[3], scale[3]) for a link's visuals."""
    urdf_path = Path(urdf_path)
    root = ET.parse(urdf_path).getroot()
    link = next(l for l in root.findall("link") if l.get("name") == link_name)
    out = []
    for vis in link.findall("visual"):
        mesh = vis.find("geometry/mesh")
        if mesh is None:
            continue
        origin = vis.find("origin")
        xyz = _floats(origin.get("xyz") if origin is not None else None, [0, 0, 0])
        rpy = _floats(origin.get("rpy") if origin is not None else None, [0, 0, 0])
        scale = _floats(mesh.get("scale"), [1, 1, 1])
        out.append((str(urdf_path.parent / mesh.get("filename")), xyz, rpy, scale))
    return out


def door_world_points(urdf_path, joint_name, link_name, max_points=4000, client=None):
    """World-space point cloud of the given door link at closed pose (all joints = 0)."""
    own = client is None
    cid = p.connect(p.DIRECT) if own else client
    body = p.loadURDF(urdf_path, [0, 0, 0], useFixedBase=1, physicsClientId=cid)
    li = None
    for j in range(p.getNumJoints(body, physicsClientId=cid)):
        p.resetJointState(body, j, 0.0, physicsClientId=cid)
        if p.getJointInfo(body, j, physicsClientId=cid)[1].decode() == joint_name:
            li = j
    ls = p.getLinkState(body, li, computeForwardKinematics=True, physicsClientId=cid)
    world_pos, world_orn = ls[4], ls[5]                      # URDF link frame in world
    R = np.array(p.getMatrixFromQuaternion(world_orn)).reshape(3, 3)
    T_wl = np.eye(4)
    T_wl[:3, :3] = R
    T_wl[:3, 3] = world_pos
    p.removeBody(body, physicsClientId=cid)
    if own:
        p.disconnect(cid)

    chunks = []
    for mesh_path, o_xyz, o_rpy, scale in _link_visual_meshes(urdf_path, link_name):
        v = _load_obj_vertices(mesh_path)
        if v.size == 0:
            continue
        v = v * np.asarray(scale)                            # mesh scale
        T = T_wl @ _origin_matrix(o_xyz, o_rpy)              # world <- link <- visual
        vh = np.c_[v, np.ones(len(v))] @ T.T
        chunks.append(vh[:, :3])
    pts = np.vstack(chunks) if chunks else np.zeros((0, 3))
    if len(pts) > max_points:                                # deterministic subsample
        idx = np.linspace(0, len(pts) - 1, max_points).astype(int)
        pts = pts[idx]
    return pts


def link_frame_points(urdf_path, link_name):
    """Point cloud of a link's visual meshes expressed in the LINK frame."""
    chunks = []
    for mesh_path, o_xyz, o_rpy, scale in _link_visual_meshes(urdf_path, link_name):
        v = _load_obj_vertices(mesh_path)
        if v.size == 0:
            continue
        v = v * np.asarray(scale)
        T = _origin_matrix(o_xyz, o_rpy)
        vh = np.c_[v, np.ones(len(v))] @ T.T
        chunks.append(vh[:, :3])
    return np.vstack(chunks) if chunks else np.zeros((0, 3))


def link_geometry(urdf_path, link_name):
    """Centroid / bbox / extent of a link's geometry in the LINK frame."""
    pts = link_frame_points(urdf_path, link_name)
    return {
        "centroid": pts.mean(0),
        "min": pts.min(0),
        "max": pts.max(0),
        "extent": pts.max(0) - pts.min(0),
    }


def chamfer(a, b):
    """Symmetric mean nearest-neighbour distance (meters)."""
    if len(a) == 0 or len(b) == 0:
        return float("inf")
    da, _ = cKDTree(b).query(a)
    db, _ = cKDTree(a).query(b)
    return float((da.mean() + db.mean()) / 2.0)


def displacement(a, b):
    """Mean per-vertex displacement (meters), using exact correspondence.

    We never edit mesh files -- a fix only changes URDF transform attributes -- so the
    candidate and healthy doors have identical vertices in identical order. Correspondence
    therefore measures the true transform error, unlike Chamfer, which under-measures
    in-plane shifts (a flat door slid within its own plane maps onto its own surface).
    Falls back to Chamfer if the point sets somehow differ in length.
    """
    if len(a) == 0 or len(b) == 0:
        return float("inf")
    if len(a) != len(b):
        return chamfer(a, b)
    return float(np.linalg.norm(a - b, axis=1).mean())


def geometric_score(candidate_urdf, healthy_urdf, joint_name, link_name, client=None):
    """Compare a candidate door against the healthy door.

    Returns deviation, the part-relative tolerance tau, whether the candidate is within it, and a
    continuous score = exp(-deviation / tau) (1.0 = perfectly restored, ~0.37 exactly at tau).
    """
    healthy = door_world_points(healthy_urdf, joint_name, link_name, client=client)
    cand = door_world_points(candidate_urdf, joint_name, link_name, client=client)
    err = displacement(cand, healthy)
    diag = float(np.linalg.norm(healthy.max(0) - healthy.min(0))) if len(healthy) else 1.0
    tau = tolerance(diag)
    return {
        "deviation_mm": err * 1000.0,
        "tau_mm": tau * 1000.0,
        "within_tol": bool(err <= tau),
        "score": float(np.exp(-err / tau)) if tau > 0 else 0.0,
        "diag_mm": diag * 1000.0,
    }
