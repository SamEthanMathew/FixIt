#!/usr/bin/env python
"""
Per-part corruption of a fridge URDF, and its exact inverse (the ground-truth fix).

A corruption transforms ONE whole part (a door = all meshes of a revolute child link),
following FixIt's granularity. All three types transform the PART'S GEOMETRY within its link
frame -- the hinge/joint is left untouched, so the door still swings about its real hinge but
is mis-sized / mis-placed / mis-oriented:

  translate: shift every visual+collision <origin xyz> of the part along one axis
  rotate:    rotate the part about its own CENTROID (tilts in place; rotating about the joint
             origin would fling the door metres away, since the hinge is ~1 m from the centroid)
  scale:     multiply the part's <mesh scale> on one axis about a bbox-edge PIVOT, with a
             compensating origin shift so the pivot edge stays fixed and the door grows one way

Meshes are never edited. Geometry-dependent parameters (centroid, pivot, axis) are computed
once at break time and STORED IN THE SPEC, so the inverse reuses identical values rather than
recomputing them from already-deformed geometry.

A spec: {type, axis(0|1|2), value, link, joint, [centroid], [pivot]}; axis is a URDF axis index.
"""
import math
import random
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

import geom

TRANSLATE_RANGE = (0.08, 0.20)   # meters
ROTATE_RANGE_DEG = (15.0, 45.0)  # degrees -- tilts in place, stays plausible
SCALE_RANGE = (1.25, 1.60)       # enlarge factor on the door's largest axis


BROKEN_MARGIN = 3.0     # a corruption must displace the part by >= BROKEN_MARGIN * tau
_GROWTH = 1.6           # magnitude multiplier per retry
_MAX_TRIES = 6


def _magnitude(spec):
    """The corruption's free magnitude parameter, in its own units."""
    return spec["value"]


def _scaled(spec, factor):
    """Same corruption with its magnitude grown by `factor` (about the identity)."""
    out = dict(spec)
    if spec["type"] == "scale":
        out["value"] = 1.0 + (spec["value"] - 1.0) * factor   # grow away from 1.0, not 0.0
    else:
        out["value"] = spec["value"] * factor
    return out


def _invert(spec):
    out = dict(spec)
    out["value"] = 1.0 / spec["value"] if spec["type"] == "scale" else -spec["value"]
    return out


def sample_corruption(urdf, part, index, ctype, ensure_broken=True, client=None):
    """Deterministically sample a corruption of `ctype` for `part` of `urdf`.

    Returns (spec, fix_spec) where fix_spec is the exact inverse.

    With `ensure_broken`, the magnitude is GROWN until the corruption displaces the part by at
    least BROKEN_MARGIN * tau, so every generated instance is unambiguously broken. Growing beats
    rejection-sampling here: rejecting would silently thin the instance set (sampled magnitudes
    routinely land under 3*tau). Returns (None, None) if it cannot clear the margin.
    """
    rng = random.Random(f"{part['link']}|{ctype}|{index}")
    g = geom.link_geometry(urdf, part["link"])
    extent = g["extent"]
    order = list(np.argsort(extent)[::-1])       # axes, largest extent first

    if ctype == "translate":
        axis = int(rng.choice(order[:2]))        # shift along a broad axis of the door
        val = rng.uniform(*TRANSLATE_RANGE) * rng.choice([-1, 1])
        spec = {"type": "translate", "axis": axis, "value": val}
        fix = {"type": "translate", "axis": axis, "value": -val}
    elif ctype == "rotate":
        axis = int(rng.choice([0, 1, 2]))
        val = math.radians(rng.uniform(*ROTATE_RANGE_DEG)) * rng.choice([-1, 1])
        c = [float(x) for x in g["centroid"]]
        spec = {"type": "rotate", "axis": axis, "value": val, "centroid": c}
        fix = {"type": "rotate", "axis": axis, "value": -val, "centroid": c}
    elif ctype == "scale":
        axis = int(order[0])                     # largest extent -> a visible size change
        f = rng.uniform(*SCALE_RANGE)
        # pivot at one bbox edge so the door grows in a single direction
        pivot = float(g["min"][axis] if rng.random() < 0.5 else g["max"][axis])
        spec = {"type": "scale", "axis": axis, "value": f, "pivot": pivot}
        fix = {"type": "scale", "axis": axis, "value": 1.0 / f, "pivot": pivot}
    else:
        raise ValueError(f"unknown corruption type: {ctype}")

    for s in (spec, fix):
        s["link"] = part["link"]
        s["joint"] = part["joint"]
    if not ensure_broken:
        return spec, fix

    # Grow the magnitude until the break clears BROKEN_MARGIN * tau. The probe URDF is written
    # beside the meshes (not a temp dir) so its relative textured_objs/ paths still resolve.
    probe_name = f"_probe_{part['link']}_{ctype}_{index}.urdf"
    probe_path = Path(urdf).parent / probe_name
    factor = 1.0
    try:
        for _ in range(_MAX_TRIES):
            cand = _scaled(spec, factor)
            apply(urdf, cand, probe_name)
            g2 = geom.geometric_score(str(probe_path), urdf, part["joint"], part["link"],
                                      client=client)
            if g2["deviation_mm"] >= BROKEN_MARGIN * g2["tau_mm"]:
                return cand, _invert(cand)
            factor *= _GROWTH
        return None, None
    finally:
        if probe_path.exists():
            probe_path.unlink()


# ----------------------------------------------------------------------------- editors

def _get_or_make_origin(el):
    origin = el.find("origin")
    if origin is None:
        origin = ET.SubElement(el, "origin")
    return origin


def _fmt(vals):
    return " ".join(repr(float(v)) for v in vals)


def _part_elements(link_el):
    """Every visual+collision element of the part (the whole door)."""
    for kind in ("visual", "collision"):
        for el in link_el.findall(kind):
            yield el


def _edit_translate(link_el, axis, delta):
    for el in _part_elements(link_el):
        origin = _get_or_make_origin(el)
        xyz = [float(x) for x in (origin.get("xyz") or "0 0 0").split()]
        xyz[axis] += delta
        origin.set("xyz", _fmt(xyz))


def _edit_rotate(link_el, axis, theta, centroid):
    R = geom.axis_rotation(axis, theta)
    c = np.asarray(centroid, dtype=float)
    for el in _part_elements(link_el):
        origin = _get_or_make_origin(el)
        xyz = np.array([float(x) for x in (origin.get("xyz") or "0 0 0").split()])
        rpy = [float(x) for x in (origin.get("rpy") or "0 0 0").split()]
        origin.set("xyz", _fmt(c + R @ (xyz - c)))
        origin.set("rpy", _fmt(geom.matrix_to_rpy(R @ geom.rpy_matrix(rpy))))


def _edit_scale(link_el, axis, factor, pivot):
    """Scale the part on `axis` about `pivot` (a coordinate in the link frame).

    Mesh scale acts about the mesh origin, so the visual origin is shifted to compensate:
        t'[a] = factor * t[a] + (1 - factor) * pivot
    which keeps the pivot edge fixed and is exactly invertible by (1/factor, same pivot).
    """
    for el in _part_elements(link_el):
        mesh = el.find("geometry/mesh")
        if mesh is None:
            continue
        scale = [float(x) for x in (mesh.get("scale") or "1 1 1").split()]
        scale[axis] *= factor
        mesh.set("scale", _fmt(scale))
        origin = _get_or_make_origin(el)
        xyz = [float(x) for x in (origin.get("xyz") or "0 0 0").split()]
        xyz[axis] = factor * xyz[axis] + (1.0 - factor) * pivot
        origin.set("xyz", _fmt(xyz))


def apply(in_urdf, spec, out_name):
    """Apply `spec` to `in_urdf`, writing a new URDF `out_name` next to it (so relative
    textured_objs/ paths still resolve). Returns the output path as a string.
    """
    in_urdf = Path(in_urdf)
    tree = ET.parse(in_urdf)
    root = tree.getroot()
    link_el = next(l for l in root.findall("link") if l.get("name") == spec["link"])

    t = spec["type"]
    if t == "translate":
        _edit_translate(link_el, spec["axis"], spec["value"])
    elif t == "rotate":
        _edit_rotate(link_el, spec["axis"], spec["value"], spec["centroid"])
    elif t == "scale":
        _edit_scale(link_el, spec["axis"], spec["value"], spec["pivot"])
    else:
        raise ValueError(f"unknown corruption type: {t}")

    out = in_urdf.parent / out_name
    tree.write(out)
    return str(out)


def describe(spec):
    ax = "xyz"[spec["axis"]]
    if spec["type"] == "translate":
        return f"translate {spec['link']} {'+' if spec['value']>=0 else '-'}{ax} {abs(spec['value']):.3f}m"
    if spec["type"] == "rotate":
        return f"rotate {spec['link']} {'+' if spec['value']>=0 else '-'}{ax} {abs(math.degrees(spec['value'])):.1f}deg"
    if spec["type"] == "scale":
        return f"scale {spec['link']} {ax} x{spec['value']:.3f}"
    return str(spec)
