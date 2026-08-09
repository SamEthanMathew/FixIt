#!/usr/bin/env python
"""
Parse the agent's tagged output into structured, validated actions.

Grammar (from the task prompt):
    <think>...</think>            optional, ignored except for logging
    <backtrack/>                  optional flag before the act
    <act>SIMULATE <ACTIONS></act>  try a fix, do not commit
    <act>COMMIT   <ACTIONS></act>  commit and end the episode

    <ACTION> is one of:
    TRANSLATE(P#, X|Y|Z, value_m)      signed metres
    ROTATE(P#, X|Y|Z, value_deg)       signed degrees
    SCALE(P#, X|Y|Z, factor)           multiplier
    NO_FIX()                           assert already functional (empty fix)
    RESET()                            stack contract only: discard the working state

Magnitudes are CLAMPED into the continuous action-space bounds (grids.clamp_range) -- they are NOT
snapped to a grid; the agent's action space is continuous.

TWO ACTION CONTRACTS (see env.FridgeRepairEnv.action_contract):
  batch  multi=True   -- <ACTIONS> is an ordered LIST applied in order to a fresh copy of the broken
                         object. This is how a composite (multi-fault) break is repaired in one turn.
  stack  multi=False  -- exactly one action per turn, applied on top of the persisted working state;
                         RESET() and a bare COMMIT (commit the working state as-is) are legal.

The parser emits corruption-style specs WITHOUT centroid/pivot -- env.py injects those canonical
params per step, from the state each action actually acts on. Returns a result dict with
valid/error; the env decides whether to grant a reparse retry.
"""
import math
import re

import grids

_AXIS = {"X": 0, "Y": 1, "Z": 2}
_AXIS_INV = {0: "X", 1: "Y", 2: "Z"}

MAX_ACTIONS_PER_TURN = 6     # batch contract: guard against a runaway list


def format_action(spec, part_id, mode="COMMIT"):
    """Render a corruption-style spec as an agent action line (used by the oracle agent).

    Inverse of parse(): metres for translate, DEGREES for rotate, factor for scale.
    """
    return f"<act>{mode} {format_call(spec, part_id)}</act>"


def format_call(spec, part_id):
    """Just the CALL text, no <act> wrapper -- so a sequence can be joined into one batch action."""
    if spec["type"] == "no_fix":
        return "NO_FIX()"
    ax = _AXIS_INV[spec["axis"]]
    if spec["type"] == "translate":
        return f"TRANSLATE({part_id}, {ax}, {spec['value']:.5f})"
    if spec["type"] == "rotate":
        return f"ROTATE({part_id}, {ax}, {math.degrees(spec['value']):.4f})"
    if spec["type"] == "scale":
        return f"SCALE({part_id}, {ax}, {spec['value']:.6f})"
    raise ValueError(spec["type"])


_ACT_RE = re.compile(r"<act>(.*?)</act>", re.IGNORECASE | re.DOTALL)
_THINK_RE = re.compile(r"<think>(.*?)</think>", re.IGNORECASE | re.DOTALL)
_BACKTRACK_RE = re.compile(r"<backtrack\s*/?>", re.IGNORECASE)
_MODE_RE = re.compile(r"\b(SIMULATE|COMMIT)\b", re.IGNORECASE)
_CALL_RE = re.compile(r"\b(TRANSLATE|ROTATE|SCALE|NO_FIX|RESET)\s*\(([^)]*)\)", re.IGNORECASE)


def _err(msg, think="", backtrack=False):
    return {"valid": False, "error": msg, "think": think, "backtrack": backtrack,
            "mode": None, "actions": [], "action": None}


def _ok(mode, actions, think, backtrack):
    return {"valid": True, "error": None, "think": think, "backtrack": backtrack,
            "mode": mode, "actions": actions,
            "action": actions[0] if actions else None}


def _parse_call(op, arg_str, id_map, reveal_fixable=True):
    """One CALL -> (action_dict, error_msg). Exactly one of the two is None."""
    args = [a.strip() for a in arg_str.split(",") if a.strip() != ""]

    if op in ("NO_FIX", "RESET"):
        if args:
            return None, f"{op} takes no arguments"
        return {"type": op.lower(), "part_id": None, "spec": None}, None

    if len(args) != 3:
        return None, f"{op} expects 3 args (part, axis, value), got {len(args)}"
    pid, axis_s, value_s = args[0].upper(), args[1].upper(), args[2]

    if pid not in id_map:
        return None, f"unknown part {pid!r}; choose from {sorted(id_map)}"
    if not id_map[pid]["corruptible"]:
        # Generic wording: under reveal_fixable=False the part table deliberately hides which parts
        # are repairable, so the error must not hand that back.
        return None, (f"part {pid} is not fixable" if reveal_fixable
                      else f"part {pid} is not a movable part and cannot be repaired")
    if axis_s not in _AXIS:
        return None, f"axis must be X, Y or Z, got {axis_s!r}"
    try:
        raw = float(value_s)
    except ValueError:
        return None, f"value {value_s!r} is not a number"

    axis = _AXIS[axis_s]
    part = id_map[pid]
    ctype = {"TRANSLATE": "translate", "ROTATE": "rotate", "SCALE": "scale"}[op]

    if ctype == "translate":
        value = grids.clamp_range(raw, "translate")                 # metres, continuous
    elif ctype == "rotate":
        value = math.radians(grids.clamp_range(raw, "rotate"))      # degrees -> radians, continuous
    else:  # scale
        if raw <= 0:
            return None, "scale factor must be positive"
        value = grids.clamp_range(raw, "scale")                     # multiplier, continuous

    spec = {"type": ctype, "axis": axis, "value": value,
            "link": part["link"], "joint": part["joint"]}
    return {"type": ctype, "part_id": pid, "spec": spec,
            "raw_value": raw, "raw_axis": axis_s}, None


def parse(text, id_map, multi=False, allow_reset=False, allow_bare_commit=False,
          reveal_fixable=True):
    """Parse one model turn. `id_map` is part_table.build_part_table()[1].

    multi=True             accept an ordered LIST of calls (the batch contract)
    allow_reset=True       accept RESET() (the stack contract)
    allow_bare_commit=True accept `COMMIT` with no call, meaning "commit the working state as-is"
    """
    think_m = _THINK_RE.search(text)
    think = think_m.group(1).strip() if think_m else ""
    backtrack = bool(_BACKTRACK_RE.search(text))

    act_m = _ACT_RE.search(text)
    body = act_m.group(1) if act_m else text          # tolerate missing <act> tags

    mode_m = _MODE_RE.search(body)
    if not mode_m:
        return _err("missing SIMULATE or COMMIT", think, backtrack)
    mode = mode_m.group(1).upper()

    calls = list(_CALL_RE.finditer(body))
    if not calls:
        if mode == "COMMIT" and allow_bare_commit:
            return _ok(mode, [], think, backtrack)    # commit the working state unchanged
        return _err("no TRANSLATE/ROTATE/SCALE/NO_FIX call found", think, backtrack)
    if not multi and len(calls) > 1:
        return _err(f"exactly one action per turn is allowed, found {len(calls)}",
                    think, backtrack)
    if len(calls) > MAX_ACTIONS_PER_TURN:
        return _err(f"at most {MAX_ACTIONS_PER_TURN} actions per turn, found {len(calls)}",
                    think, backtrack)

    actions = []
    for m in calls:
        op = m.group(1).upper()
        if op == "RESET" and not allow_reset:
            return _err("RESET() is not available in this contract", think, backtrack)
        act, err = _parse_call(op, m.group(2), id_map, reveal_fixable=reveal_fixable)
        if err:
            return _err(err, think, backtrack)
        actions.append(act)

    # NO_FIX / RESET are whole-turn statements, never list members
    for special in ("no_fix", "reset"):
        if any(a["type"] == special for a in actions) and len(actions) > 1:
            return _err(f"{special.upper()}() must be the only action in the turn",
                        think, backtrack)

    return _ok(mode, actions, think, backtrack)
