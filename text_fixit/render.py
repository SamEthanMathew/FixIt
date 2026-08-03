#!/usr/bin/env python
"""
Headless PyBullet rendering of fridge URDFs.

Camera framing is computed once from a reference (healthy) shape and reused for the broken
variants, so a corruption shows up as a visible difference rather than being normalised away
by per-image auto-zoom.
"""
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pybullet as p
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import _joint_index_by_name, _revolute_joints  # noqa: E402

# Use the real material colours from the .mtl files instead of PyBullet's default flat grey.
LOAD_FLAGS = p.URDF_USE_MATERIAL_COLORS_FROM_MTL


def _textures_for_obj(obj_path):
    """Texture image paths referenced (via map_Kd) by an OBJ's material libraries."""
    try:
        txt = open(obj_path, errors="ignore").read()
    except OSError:
        return []
    base = os.path.dirname(obj_path)
    tex = []
    for mtl in re.findall(r"mtllib\s+(\S+)", txt):
        mp = os.path.join(base, mtl)
        if not os.path.exists(mp):
            continue
        for m in re.findall(r"map_Kd\s+(\S+)", open(mp, errors="ignore").read()):
            path = os.path.normpath(os.path.join(base, m))
            if path not in tex:
                tex.append(path)
    return tex


def apply_textures(body, cid):
    """Bind each visual shape's texture where it is unambiguous.

    PyBullet supports one texture per visual shape, but PartNet-Mobility's merged `new-*.obj`
    meshes reference several textures at once. Binding one of those would smear the wrong
    texture over the whole mesh, so we only bind when a mesh references exactly ONE texture;
    ambiguous meshes keep their .mtl diffuse colour.
    """
    per_link = defaultdict(int)
    tex_cache = {}   # texture ids belong to this physics client only -- never cache globally
    for t in p.getVisualShapeData(body, physicsClientId=cid):
        link = t[1]
        mesh = t[4].decode() if isinstance(t[4], bytes) else t[4]
        idx = per_link[link]
        per_link[link] += 1
        tex = _textures_for_obj(mesh)
        rgba = t[7]
        # PartNet-Mobility materials often pair a dim/black Kd with the real appearance in
        # map_Kd. PyBullet multiplies Kd through the texture, which renders those parts far too
        # dark (or pure black). Per standard OBJ semantics map_Kd overrides Kd, so we set the
        # diffuse to white wherever a texture is bound and let the texture define the colour.
        too_dark = max(rgba[:3]) < 0.12

        if len(tex) == 1 and os.path.exists(tex[0]):
            tid = tex_cache.get(tex[0])
            if tid is None:
                tid = tex_cache[tex[0]] = p.loadTexture(tex[0], physicsClientId=cid)
            try:
                p.changeVisualShape(body, link, shapeIndex=idx, textureUniqueId=tid,
                                    rgbaColor=[1, 1, 1, 1], physicsClientId=cid)
            except p.error:
                pass
        elif too_dark:
            try:
                p.changeVisualShape(body, link, shapeIndex=idx,
                                    rgbaColor=[0.80, 0.80, 0.82, 1], physicsClientId=cid)
            except p.error:
                pass


def _scene_aabb(body, cid):
    lo = np.array([1e9, 1e9, 1e9])
    hi = -lo
    for link in range(-1, p.getNumJoints(body, physicsClientId=cid)):
        amin, amax = p.getAABB(body, link, physicsClientId=cid)
        lo = np.minimum(lo, amin)
        hi = np.maximum(hi, amax)
    return lo, hi


def camera_from_urdf(urdf, margin=1.7):
    """Return (center, distance) framing this URDF with all doors closed."""
    cid = p.connect(p.DIRECT)
    body = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, physicsClientId=cid)
    for j in range(p.getNumJoints(body, physicsClientId=cid)):
        p.resetJointState(body, j, 0.0, physicsClientId=cid)
    p.performCollisionDetection(physicsClientId=cid)
    lo, hi = _scene_aabb(body, cid)
    p.disconnect(cid)
    center = (lo + hi) / 2.0
    return center, margin * float(np.linalg.norm(hi - lo))


def render_urdf(urdf, joint_name=None, angle=0.0, center=None, dist=None,
                res=360, yaw=45, pitch=-25, textured=True):
    """Render one frame. If joint_name is given, that door is opened to `angle` (others closed)."""
    cid = p.connect(p.DIRECT)
    body = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, flags=LOAD_FLAGS, physicsClientId=cid)
    if textured:
        apply_textures(body, cid)
    doors = _revolute_joints(body)
    target = _joint_index_by_name(body, joint_name) if joint_name else None
    for jj in doors:
        p.resetJointState(body, jj, angle if jj == target else 0.0, physicsClientId=cid)
    p.performCollisionDetection(physicsClientId=cid)
    if center is None or dist is None:
        lo, hi = _scene_aabb(body, cid)
        center = (lo + hi) / 2.0
        dist = 1.7 * float(np.linalg.norm(hi - lo))
    view = p.computeViewMatrixFromYawPitchRoll(list(center), dist, yaw, pitch, 0, 2)
    proj = p.computeProjectionMatrixFOV(55, 1.0, 0.01, 100)
    _, _, rgb, _, _ = p.getCameraImage(res, res, view, proj, renderer=p.ER_TINY_RENDERER,
                                       shadow=1, lightDirection=[0.6, 0.4, 1.0],
                                       physicsClientId=cid)
    p.disconnect(cid)
    arr = np.reshape(np.array(rgb, dtype=np.uint8), (res, res, 4))[:, :, :3]
    return Image.fromarray(arr)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path
