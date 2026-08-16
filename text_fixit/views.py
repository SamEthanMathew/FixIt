#!/usr/bin/env python
"""
Rendered observations for the image (VLM) conditions.

View products, framed with a camera locked to the HEALTHY shape (render.camera_from_urdf) so a fix
shows up as a visible change rather than being auto-zoomed away:

  closed_view(urdf, ..., id_map) -> [closed]   the CLOSED (all doors at 0 deg) front 3/4 view; parts
                            flat-recoloured by index. Only the closed view is fed to the model.
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

# HARD perception mode: every door gets the SAME neutral colour, so colour no longer identifies
# which panel is which (the labelled reset view stays the only P# grounding), and the camera moves
# to a less favourable yaw where the door panels are more foreshortened.
HARD_DOOR_RGBA = (0.62, 0.64, 0.66, 1)
EASY_YAW, HARD_YAW = -45, 35
# Flat recolouring is KEPT in hard mode: PartNet's own materials render near-black under the tiny
# renderer, so dropping it would make the views unreadable rather than merely harder.


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
    # bright, even lighting (high ambient, no shadow) so PartNet's dark materials stay legible
    w, h, rgb, _, seg = p.getCameraImage(res, res, view, proj, renderer=p.ER_TINY_RENDERER,
                                         shadow=0, lightDirection=[1.0, 1.0, 1.4],
                                         lightColor=[1, 1, 1], lightAmbientCoeff=0.65,
                                         lightDiffuseCoeff=0.70, lightSpecularCoeff=0.05,
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


def closed_view(urdf, center, dist, id_map, res=768, hard=False):
    """A single CLOSED (all doors at 0 deg) front 3/4 view -- shows the seam gap / overlap / oversize.
    (Open views were removed: only the closed view is fed to the model.)

    Rendered with FLAT light materials (PartNet textures render near-black and hide the geometry).
    Each part gets a fixed colour BY INDEX (the SAME palette as the labelled reset view: P1, P2, ...),
    NOT by which door is faulty -- so the colours ground the parts without revealing which door is
    broken.

    hard=True: every door gets one NEUTRAL colour instead (colour stops identifying parts) and the
    camera swings to HARD_YAW, a less favourable angle. Returns a one-image list."""
    _, _, j2l = _render(urdf, center=center, dist=dist, res=res, want_seg=True)   # joint -> link idx
    recolor, ci = {}, 0
    for pt in id_map.values():                                    # colour by PART INDEX, not fault
        li = j2l.get(pt["joint"])
        if li is None:
            continue
        if not pt["corruptible"]:
            recolor[li] = BODY_RGBA
        elif hard:
            recolor[li] = HARD_DOOR_RGBA
        else:
            recolor[li] = PALETTE[ci % len(PALETTE)]
            ci += 1
    yaw = HARD_YAW if hard else EASY_YAW
    closed, _, _ = _render(urdf, None, 0.0, center, dist, res=res, yaw=yaw, pitch=-30,
                           recolor=recolor)
    return [closed]


def annotated_part_view(urdf, id_map, center, dist, res=420, hard=False):
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
    # land on visible door panels rather than edge-on slivers. In hard mode we match closed_view's
    # yaw so this reference view and the observation views share a viewpoint -- the labelled view
    # KEEPS its distinct palette (it is the only P# grounding), while the observations go neutral,
    # so the agent must carry the identity across by position rather than by colour.
    YAW, PITCH = (HARD_YAW if hard else EASY_YAW), -30
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
    save(closed_view(args.urdf, center, dist, id_map)[0], f"{args.out}/closed.png")
    save(annotated_part_view(args.urdf, id_map, center, dist), f"{args.out}/annotated.png")
    print(f"wrote closed, annotated -> {args.out}")


# --------------------------------------------------------------------------- axis legend
# A vision model is asked for an axis in the OBJECT frame but its only evidence is a 2D render.
# Nothing connected the two: prompts stated "right-handed object frame" and stopped, and Qwen3-VL-8B
# duly picked the axis at chance (36.2% against 33.3%). This derives the missing legend FROM THE
# ACTUAL CAMERA rather than hardcoding it -- closed_view swings the yaw by 80 degrees when hard=True,
# so a fixed legend would be confidently inverted on half the runs.
def _camera_basis(center, dist, yaw, pitch):
    """World-space (right, up, toward_viewer) unit vectors for the render camera."""
    import numpy as np
    import pybullet as p
    v = np.array(p.computeViewMatrixFromYawPitchRoll(list(center), dist, yaw, pitch, 0, 2))
    R = v.reshape(4, 4, order="F")[:3, :3]      # column-major; rows are the camera axes in world
    # Row 2 of a lookAt rotation is the BACKWARD axis -- it points from the target to the eye, i.e.
    # toward the viewer. (Negating it, the intuitive-looking choice, inverts every depth statement.)
    return R[0], R[1], R[2]


def _link_axes_world(urdf, link_name):
    """Rotation of a link's own frame into world, as (x_world, y_world, z_world) unit vectors."""
    import numpy as np
    import pybullet as p
    from quiet import quiet
    with quiet():
        cid = p.connect(p.DIRECT)
        try:
            body = p.loadURDF(urdf, useFixedBase=True, physicsClientId=cid)
            idx = None
            for j in range(p.getNumJoints(body, physicsClientId=cid)):
                info = p.getJointInfo(body, j, physicsClientId=cid)
                if info[12].decode() == link_name:
                    idx = j
                    break
            if idx is None:
                quat = p.getBasePositionAndOrientation(body, physicsClientId=cid)[1]
            else:
                quat = p.getLinkState(body, idx, physicsClientId=cid)[5]
            R = np.array(p.getMatrixFromQuaternion(quat)).reshape(3, 3)
        finally:
            p.disconnect(cid)
    return R[:, 0], R[:, 1], R[:, 2]


def _describe(vec, right, up, toward):
    """One object axis -> plain words, from its components on the camera basis.

    Depth is mentioned ONLY when the axis barely moves on screen. Under this camera all three
    positive axes tilt somewhat toward the viewer, so an unconditional "and toward you" is true of
    everything and therefore discriminates nothing -- the usable cue is the in-plane direction.
    """
    import math
    import numpy as np
    r, u, t = float(np.dot(vec, right)), float(np.dot(vec, up)), float(np.dot(vec, toward))
    inplane = math.hypot(r, u)
    if inplane < 0.35:
        return ("almost straight out of the screen toward you" if t > 0
                else "almost straight into the screen away from you") + \
               " (it hardly moves the part sideways or up in the picture)"
    if abs(u) > 0.8:
        return "straight up in the picture" if u > 0 else "straight down in the picture"
    horiz = "right" if r > 0.15 else ("left" if r < -0.15 else "")
    vert = "upper" if u > 0.15 else ("lower" if u < -0.15 else "")
    where = f"{vert}-{horiz}" if vert and horiz else (vert or horiz)
    return f"toward the {where} of the picture"


def axis_image_legend(urdf, id_map, center, dist, hard=False):
    """Plain-language mapping from object axes to directions in the rendered view.

    Returns None when the fixable parts do not share one frame -- in that case no single legend is
    true, and saying nothing beats saying something wrong for the general case.
    """
    import numpy as np
    links = [pt["link"] for pt in id_map.values() if pt.get("corruptible")]
    if not links:
        return None
    try:
        axes = [_link_axes_world(urdf, ln) for ln in links]
    except Exception:
        return None
    a0 = axes[0]
    for a in axes[1:]:
        if any(float(np.dot(a[i], a0[i])) < 0.99 for i in range(3)):
            return None                      # parts disagree -> no single legend holds
    yaw = HARD_YAW if hard else EASY_YAW
    right, up, toward = _camera_basis(center, dist, yaw, -30)
    names = ("X", "Y", "Z")
    lines = [f"  +{n} points {_describe(v, right, up, toward)}; -{n} is the opposite."
             for n, v in zip(names, a0)]
    return ("HOW THE AXES LOOK IN THE PICTURES\n"
            "Every view uses the same fixed camera, so these directions hold in every image:\n"
            + "\n".join(lines) + "\n"
            "The part table lists each part's size along its own X, Y and Z, in that order, so you\n"
            "can tell which axis is the part's height, its width and its thickness by comparing\n"
            "those three numbers against what you see.")
