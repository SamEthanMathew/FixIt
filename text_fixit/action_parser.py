#!/usr/bin/env python
"""
Parse the agent's tagged output into a structured, validated action.

Grammar (from the task prompt):
    <think>...</think>            optional, ignored except for logging
    <backtrack/>                  optional flag before the act
    <act>SIMULATE <ACTION></act>  try a fix, do not commit
    <act>COMMIT   <ACTION></act>  commit and end the episode

    <ACTION> is exactly one of:
    TRANSLATE(P#, X|Y|Z, value_m)      signed metres  -> snapped to grids.VALUE_GRID
    ROTATE(P#, X|Y|Z, value_deg)       signed degrees -> snapped to grids.ANGLE_GRID
    SCALE(P#, X|Y|Z, factor)           multiplier     -> snapped to grids.SCALE_GRID
    NO_FIX()                           assert already functional (empty fix)

The parser SNAPS + CLAMPS magnitudes onto the grids and maps P#->(link,joint) and X/Y/Z->axis 0/1/2.
It emits a corruption-style spec WITHOUT centroid/pivot -- env.py injects those canonical params
(so the agent never needs hidden geometry). Returns a result dict with valid/error; the env decides
whether to grant a reparse retry.
"""
import math
import re

import grids

_AXIS = {"X": 0, "Y": 1, "Z": 2}
_AXIS_INV = {0: "X", 1: "Y", 2: "Z"}


def format_action(spec, part_id, mode="COMMIT"):
    """Render a corruption-style spec as an agent action line (used by the oracle agent).

    Inverse of parse(): metres for translate, DEGREES for rotate, factor for scale.
    """
    ax = _AXIS_INV[spec["axis"]]
    if spec["type"] == "translate":
        return f"<act>{mode} TRANSLATE({part_id}, {ax}, {spec['value']:.4f})</act>"
    if spec["type"] == "rotate":
        return f"<act>{mode} ROTATE({part_id}, {ax}, {math.degrees(spec['value']):.1f})</act>"
    if spec["type"] == "scale":
        return f"<act>{mode} SCALE({part_id}, {ax}, {spec['value']:.4f})</act>"
    if spec["type"] == "no_fix":
        return f"<act>{mode} NO_FIX()</act>"
    raise ValueError(spec["type"])
_ACT_RE = re.compile(r"<act>(.*?)</act>", re.IGNORECASE | re.DOTALL)
_THINK_RE = re.compile(r"<think>(.*?)</think>", re.IGNORECASE | re.DOTALL)
_BACKTRACK_RE = re.compile(r"<backtrack\s*/?>", re.IGNORECASE)
_MODE_RE = re.compile(r"\b(SIMULATE|COMMIT)\b", re.IGNORECASE)
_CALL_RE = re.compile(r"\b(TRANSLATE|ROTATE|SCALE|NO_FIX)\s*\(([^)]*)\)", re.IGNORECASE)


def _err(msg, think="", backtrack=False):
    return {"valid": False, "error": msg, "think": think, "backtrack": backtrack,
            "mode": None, "action": None}


def parse(text, id_map):
    """Parse one model turn. `id_map` is part_table.build_part_table()[1]."""
    think_m = _THINK_RE.search(text)
    think = think_m.group(1).strip() if think_m else ""
    backtrack = bool(_BACKTRACK_RE.search(text))

    act_m = _ACT_RE.search(text)
    body = act_m.group(1) if act_m else text          # tolerate missing <act> tags

    mode_m = _MODE_RE.search(body)
    if not mode_m:
        return _err("missing SIMULATE or COMMIT", think, backtrack)
    mode = mode_m.group(1).upper()

    call_m = _CALL_RE.search(body)
    if not call_m:
        return _err("no TRANSLATE/ROTATE/SCALE/NO_FIX call found", think, backtrack)
    op = call_m.group(1).upper()
    args = [a.strip() for a in call_m.group(2).split(",") if a.strip() != ""]

    if op == "NO_FIX":
        if args:
            return _err("NO_FIX takes no arguments", think, backtrack)
        return {"valid": True, "error": None, "think": think, "backtrack": backtrack,
                "mode": mode, "action": {"type": "no_fix"}}

    if len(args) != 3:
        return _err(f"{op} expects 3 args (part, axis, value), got {len(args)}", think, backtrack)
    pid, axis_s, value_s = args
    pid = pid.upper()
    axis_s = axis_s.upper()

    if pid not in id_map:
        return _err(f"unknown part {pid!r}; choose from {sorted(id_map)}", think, backtrack)
    if not id_map[pid]["corruptible"]:
        return _err(f"part {pid} is not fixable", think, backtrack)
    if axis_s not in _AXIS:
        return _err(f"axis must be X, Y or Z, got {axis_s!r}", think, backtrack)
    try:
        raw = float(value_s)
    except ValueError:
        return _err(f"value {value_s!r} is not a number", think, backtrack)

    axis = _AXIS[axis_s]
    part = id_map[pid]
    ctype = {"TRANSLATE": "translate", "ROTATE": "rotate", "SCALE": "scale"}[op]

    if ctype == "translate":
        value = grids.clamp_to_grid(raw, grids.VALUE_GRID)          # metres
    elif ctype == "rotate":
        deg = grids.clamp_to_grid(raw, grids.ANGLE_GRID)            # degrees -> radians
        value = math.radians(deg)
    else:  # scale
        if raw <= 0:
            return _err("scale factor must be positive", think, backtrack)
        value = grids.clamp_to_grid(raw, grids.SCALE_GRID)

    spec = {"type": ctype, "axis": axis, "value": value,
            "link": part["link"], "joint": part["joint"]}
    return {"valid": True, "error": None, "think": think, "backtrack": backtrack,
            "mode": mode, "action": {"type": ctype, "part_id": pid, "spec": spec,
                                     "raw_value": raw, "raw_axis": axis_s}}
