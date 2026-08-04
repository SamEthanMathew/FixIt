#!/usr/bin/env python
"""
Rendered observations for the image (VLM) conditions.

Three view products, all framed with a camera locked to the HEALTHY shape (render.camera_from_urdf)
so a fix shows up as a visible change rather than being auto-zoomed away:

  hero_views(urdf)       -> [Hero A, Hero B]   two yaws, closed pose, textured (resolve depth)
  closing_filmstrip(urdf, joint) -> one tiled image of the target door swinging 90deg -> shut
                            (a still can't show a jam; the strip can -- same rollout as
                            visualize_episode.py)
  annotated_part_view(urdf, id_map) -> one image with each fixable door FLAT-recoloured from a fixed
                            palette and its P# label drawn at the part's projected centroid (via the
                            segmentation buffer) -- grounds the P# vocabulary to visible doors.

These are the agent's PERCEPTION only; scoring stays physics-based (evaluation.evaluate_repair).
"""
import os
import sys

import numpy as np
import pybullet as p
from PIL import Image, ImageDraw, ImageFont


def _font(size=20):
    for path in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402
from score import _joint_index_by_name, _revolute_joints  # noqa: E402

# distinct, high-contrast flat colours for labelling fixable parts (RGBA 0-1)
PALETTE = [(0.16, 0.47, 0.84, 1), (0.92, 0.41, 0.20, 1), (0.11, 0.69, 0.48, 1),
           (0.93, 0.63, 0.0, 1), (0.91, 0.48, 0.64, 1), (0.29, 0.23, 0.65, 1)]
BODY_RGBA = (0.72, 0.72, 0.70, 1)


def _joint_to_link_index(body, cid):
    """joint name -> child-link index (getLinkState/segmentation index)."""
    out = {}
    for j in range(p.getNumJoints(body, physicsClientId=cid)):
        out[p.getJointInfo(body, j, physicsClientId=cid)[1].decode()] = j
    return out


def _render(urdf, joint=None, angle=0.0, center=None, dist=None, res=384, yaw=45, pitch=-25,
            recolor=None, textured=True, want_seg=False):
    cid = p.connect(p.DIRECT)
    body = p.loadURDF(urdf, [0, 0, 0], useFixedBase=1, flags=R.LOAD_FLAGS, physicsClientId=cid)
    if recolor is not None:
        for link_idx, rgba in recolor.items():
            p.changeVisualShape(body, link_idx, rgbaColor=rgba, physicsClientId=cid)
    elif textured:
        R.apply_textures(body, cid)
    doors = _revolute_joints(body)
    target = _joint_index_by_name(body, joint) if joint else None
    for jj in doors:
        p.resetJointState(body, jj, angle if jj == target else 0.0, physicsClientId=cid)
    p.performCollisionDetection(physicsClientId=cid)
    if center is None or dist is None:
        lo, hi = R._scene_aabb(body, cid)
        center = (lo + hi) / 2.0
        dist = 1.7 * float(np.linalg.norm(hi - lo))
    view = p.computeViewMatrixFromYawPitchRoll(list(center), dist, yaw, pitch, 0, 2)
    proj = p.computeProjectionMatrixFOV(55, 1.0, 0.01, 100)
    # request per-LINK segmentation (default only gives object id -> every link reads as base)
    seg_flag = p.ER_SEGMENTATION_MASK_OBJECT_AND_LINKINDEX if want_seg else 0
    w, h, rgb, _, seg = p.getCameraImage(res, res, view, proj, renderer=p.ER_TINY_RENDERER,
                                         shadow=1, lightDirection=[0.6, 0.4, 1.0],
                                         flags=seg_flag, physicsClientId=cid)
    j2l = _joint_to_link_index(body, cid) if want_seg else None
    p.disconnect(cid)
    img = Image.fromarray(np.reshape(np.array(rgb, dtype=np.uint8), (res, res, 4))[:, :, :3])
    seg = np.reshape(np.array(seg, dtype=np.int32), (res, res)) if want_seg else None
    return img, seg, j2l


def hero_views(urdf, center, dist, res=384):
    a, _, _ = _render(urdf, center=center, dist=dist, res=res, yaw=-45, pitch=-30)
    b, _, _ = _render(urdf, center=center, dist=dist, res=res, yaw=135, pitch=-20)
    return [a, b]


def closing_filmstrip(urdf, joint, center, dist, frames=4, res=260):
    import math
    angs = [math.radians(90.0) * (1 - i / (frames - 1)) for i in range(frames)]
    imgs = [_render(urdf, joint, a, center, dist, res=res, yaw=-45, pitch=-30)[0] for a in angs]
    strip = Image.new("RGB", (res * frames + 2 * (frames - 1), res), (252, 252, 251))
    for i, im in enumerate(imgs):
        strip.paste(im, (i * (res + 2), 0))
    return strip


def annotated_part_view(urdf, id_map, center, dist, res=420):
    """Flat-recolour fixable doors, render, and label each with its P# at its projected centroid."""
    # build recolor map: fixable parts -> palette, body -> grey
    # need link indices; open a scratch client only to resolve joint->link, reuse in _render via names
    recolor_names = {}
    ci = 0
    for pid, part in id_map.items():
        if part["corruptible"]:
            recolor_names[part["joint"]] = PALETTE[ci % len(PALETTE)]
            ci += 1
        else:
            recolor_names[part["joint"]] = BODY_RGBA
    # first pass to get joint->link index mapping (and seg), then recolor by link index.
    # yaw -45/pitch -30 = the Hero-A angle where the doors face the camera (front), so labels
    # land on visible door panels rather than edge-on slivers.
    YAW, PITCH = -45, -30
    _, _, j2l = _render(urdf, center=center, dist=dist, res=res, yaw=YAW, pitch=PITCH, want_seg=True)
    recolor = {j2l[jn]: rgba for jn, rgba in recolor_names.items() if jn in j2l}
    img, seg, j2l = _render(urdf, center=center, dist=dist, res=res, yaw=YAW, pitch=PITCH,
                            recolor=recolor, want_seg=True)

    draw = ImageDraw.Draw(img)
    for pid, part in id_map.items():
        li = j2l.get(part["joint"])
        if li is None:
            continue
        ys, xs = np.where(_link_mask(seg, li))
        if len(xs) == 0:
            continue
        cx, cy = int(xs.mean()), int(ys.mean())
        _label(draw, cx, cy, pid)
    return img


def _link_mask(seg, link_idx):
    """Pixels belonging to `link_idx`. PyBullet packs seg = objectUid | ((linkIndex+1)<<24)."""
    return ((seg >> 24) - 1) == link_idx


_FONT = _font(22)


def _label(draw, cx, cy, text):
    pad = 5
    tb = draw.textbbox((0, 0), text, font=_FONT)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    x0, y0 = cx - tw // 2 - pad, cy - th // 2 - pad
    draw.rectangle([x0, y0, x0 + tw + 2 * pad, y0 + th + 2 * pad], fill=(15, 15, 15))
    draw.text((x0 + pad, y0 + pad - tb[1]), text, fill=(255, 255, 255), font=_FONT)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


if __name__ == "__main__":
    import argparse

    from part_table import build_part_table

    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    ap.add_argument("--joint", default=None)
    ap.add_argument("--out", default="runs/gallery/views")
    args = ap.parse_args()
    _, id_map = build_part_table(args.urdf)
    center, dist = R.camera_from_urdf(args.urdf)
    joint = args.joint or next(p["joint"] for p in id_map.values() if p["corruptible"])
    for i, im in enumerate(hero_views(args.urdf, center, dist)):
        save(im, f"{args.out}/hero_{'AB'[i]}.png")
    save(closing_filmstrip(args.urdf, joint, center, dist), f"{args.out}/filmstrip.png")
    save(annotated_part_view(args.urdf, id_map, center, dist), f"{args.out}/annotated.png")
    print(f"wrote hero_A/B, filmstrip, annotated -> {args.out}")
