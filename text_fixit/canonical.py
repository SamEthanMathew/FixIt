#!/usr/bin/env python
"""
Canonical, recomputable geometry parameters shared by the break (corruption.py) and the fix
(env.py). The whole point: neither the rotation centre nor the scale pivot is a hidden random
number stored in the instance -- each is a DETERMINISTIC function of the part's current geometry,
so the agent's clean action space (rotate about the part, scale a part axis, no extra params) can
express the exact inverse of any break.

Why these are invariant (hence recomputable from the BROKEN urdf and still equal to the value the
corruption used on the HEALTHY urdf):

  rotation centre = part centroid.  A rotation about the centroid maps the centroid to itself, so
      the broken part's centroid equals the healthy part's centroid. Recompute -> identical.

  scale pivot = the HINGE-SIDE bbox edge on the scaled axis.  In the link frame the revolute axis
      passes through the origin, so the door hangs off coordinate 0; the hinge-side edge is the bbox
      extreme nearer 0. Scaling about that edge keeps it fixed, so it stays put (and stays the
      near-0 edge, since scaling only grows the door away from the hinge). Recompute -> identical.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom  # noqa: E402


def part_centroid(urdf, link):
    """Centroid of the part's geometry in the LINK frame (the rotation centre)."""
    return [float(x) for x in geom.link_geometry(urdf, link)["centroid"]]


def scale_pivot(urdf, link, axis):
    """Hinge-side bbox edge coordinate on `axis`, in the LINK frame (the scale pivot).

    The link-frame origin lies on the hinge line, so the door extends from ~0 outward; we return
    whichever bbox extreme (min or max) on this axis is closer to 0.
    """
    g = geom.link_geometry(urdf, link)
    lo, hi = float(g["min"][axis]), float(g["max"][axis])
    return lo if abs(lo) <= abs(hi) else hi


if __name__ == "__main__":
    import argparse

    from parts import corruptible_parts

    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    args = ap.parse_args()
    for pt in corruptible_parts(args.urdf):
        c = part_centroid(args.urdf, pt["link"])
        pivots = [scale_pivot(args.urdf, pt["link"], a) for a in range(3)]
        print(f"{pt['name']:16s} link={pt['link']}  centroid=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}]  "
              f"scale_pivot(x,y,z)=[{pivots[0]:.3f},{pivots[1]:.3f},{pivots[2]:.3f}]")
