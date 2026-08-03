#!/usr/bin/env python
"""
Turn a fridge URDF into the agent-facing PART TABLE (the "object classification into parts").

The table gives the agent a stable vocabulary: one row per part with a numeric id (P0, P1, ...),
a human label, its role, whether it is fixable, its bounding-box size, and its joint. The parser
maps the agent's `P#` references back to the concrete (link, joint) via the returned id_map.

Rows come straight from parts.list_parts (segmentation: a part = a revolute child link = a whole
door; the body is the fixed base) and geom.link_geometry (bbox). No new segmentation logic.

Frame: all coordinates are the URDF LINK/world frame, right-handed. The revolute axis and its
location are given per fixable part so the agent knows how each door swings.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom  # noqa: E402
from parts import list_parts  # noqa: E402


def _axis_str(vec):
    """'+Z' / '-Y' for the dominant component; '—' for a zero axis (fixed part)."""
    i = max(range(3), key=lambda k: abs(vec[k]))
    if abs(vec[i]) < 1e-9:
        return "—"
    return f"{'+' if vec[i] >= 0 else '-'}{'XYZ'[i]}"


def build_part_table(urdf):
    """Return (table_text, id_map).

    table_text : the formatted table string for the prompt.
    id_map     : {"P0": part_dict, ...} where part_dict is the parts.list_parts entry augmented
                 with "id" and "bbox" (extent w,d,h in metres).
    """
    parts = list_parts(urdf)
    id_map = {}
    rows = []
    header = f"  {'id':<4} {'label':<14} {'role':<10} {'fixable':<8} {'bbox (w,d,h)':<18} joint"
    for i, part in enumerate(parts):
        pid = f"P{i}"
        ext = geom.link_geometry(urdf, part["link"])["extent"]
        bbox = f"{ext[0]:.2f},{ext[1]:.2f},{ext[2]:.2f}"
        role = "base" if not part["corruptible"] else part["joint_type"]
        fixable = "yes" if part["corruptible"] else "no"
        if part["corruptible"]:
            o = part["joint_origin"]
            joint = f"axis {_axis_str(part['joint_axis'])} at ({o[0]:.2f},{o[1]:.2f},{o[2]:.2f})"
        else:
            joint = "—"
        rows.append(f"  {pid:<4} {part['name']:<14} {role:<10} {fixable:<8} {bbox:<18} {joint}")
        part = dict(part, id=pid, bbox=[float(x) for x in ext])
        id_map[pid] = part
    return header + "\n" + "\n".join(rows), id_map


def fixable_ids(id_map):
    return [pid for pid, part in id_map.items() if part["corruptible"]]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    args = ap.parse_args()
    table, id_map = build_part_table(args.urdf)
    print(table)
    print("\nfixable:", fixable_ids(id_map))
