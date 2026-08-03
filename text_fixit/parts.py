#!/usr/bin/env python
"""
Part segmentation for a PartNet-Mobility fridge URDF.

A "part", following the FixIt paper, is a whole movable articulated component (a door):
the child link of a `revolute` joint. The body is the child of the `fixed` joint and is
kept for reference but is NOT corruptible. Each part carries the full set of visual/collision
mesh elements of its link (door_frame + handle + leaf are one part, transformed together).

This mirrors the part-selection logic in generate_data/fridge/generate_data.py (change_objs),
but works directly in native URDF coordinates via xml.etree.ElementTree.
"""
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse_semantics(shape_dir):
    """link_name -> semantic label, e.g. {'link_0':'refrigerator_body', 'link_1':'door'}."""
    sem = {}
    f = Path(shape_dir) / "semantics.txt"
    if f.exists():
        for line in f.read_text().splitlines():
            toks = line.split()
            if len(toks) >= 2:
                sem[toks[0]] = toks[-1]
    return sem


def _floats(s, default):
    if not s:
        return list(default)
    return [float(x) for x in s.split()]


def _link_mesh_files(link_el):
    """Ordered unique mesh filenames referenced by this link's visual+collision elements."""
    files = []
    for kind in ("visual", "collision"):
        for el in link_el.findall(kind):
            mesh = el.find("geometry/mesh")
            if mesh is not None and mesh.get("filename"):
                fn = mesh.get("filename")
                if fn not in files:
                    files.append(fn)
    return files


def list_parts(urdf_path):
    """Return a list of part dicts for a fridge URDF.

    Each part: {link, joint, joint_type, corruptible, semantic, name, side,
                joint_origin[3], joint_rpy[3], joint_axis[3], joint_limit(lower,upper)|None,
                mesh_files[...]}.
    Parts are returned in URDF joint order (which matches PyBullet joint indexing).
    """
    urdf_path = Path(urdf_path)
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    sem = _parse_semantics(urdf_path.parent)
    links = {l.get("name"): l for l in root.findall("link")}

    parts = []
    door_count = 0
    for joint in root.findall("joint"):
        child_el = joint.find("child")
        if child_el is None:
            continue
        child = child_el.get("link")
        link_el = links.get(child)
        if link_el is None:
            continue

        jtype = joint.get("type")
        origin_el = joint.find("origin")
        jorigin = _floats(origin_el.get("xyz") if origin_el is not None else None, [0, 0, 0])
        jrpy = _floats(origin_el.get("rpy") if origin_el is not None else None, [0, 0, 0])
        axis_el = joint.find("axis")
        jaxis = _floats(axis_el.get("xyz") if axis_el is not None else None, [0, 0, 0])
        limit_el = joint.find("limit")
        jlimit = None
        if limit_el is not None:
            jlimit = (float(limit_el.get("lower", 0.0)), float(limit_el.get("upper", 0.0)))

        semantic = sem.get(child, "")
        corruptible = (jtype == "revolute")
        if corruptible:
            door_count += 1
            side = "right" if jorigin[0] >= 0 else "left"
            name = f"door_{door_count}_{side}"
        else:
            side = None
            name = "body" if "body" in semantic else child

        parts.append({
            "link": child,
            "joint": joint.get("name"),
            "joint_type": jtype,
            "corruptible": corruptible,
            "semantic": semantic,
            "name": name,
            "side": side,
            "joint_origin": jorigin,
            "joint_rpy": jrpy,
            "joint_axis": jaxis,
            "joint_limit": jlimit,
            "mesh_files": _link_mesh_files(link_el),
        })
    return parts


def corruptible_parts(urdf_path):
    return [p for p in list_parts(urdf_path) if p["corruptible"]]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    args = ap.parse_args()
    for p in list_parts(args.urdf):
        flag = "CORRUPTIBLE" if p["corruptible"] else "fixed/body "
        print(f"[{flag}] {p['name']:16s} link={p['link']} joint={p['joint']} "
              f"({p['joint_type']}) axis={p['joint_axis']} limit={p['joint_limit']} "
              f"meshes={len(p['mesh_files'])}")
