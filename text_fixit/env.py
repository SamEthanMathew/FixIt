#!/usr/bin/env python
"""
FridgeRepairEnv -- a Gym-style, TEXT-only closed loop for single-fix fridge repair.

Contract (matches the paper's simulator, MILESTONE_1 loop, and the user's SIMULATE/COMMIT prompt):

  reset(instance)            -> observation for the BROKEN object
  step(parsed_action)        -> (observation, terminal, info)

  * SIMULATE: apply the fix to a COPY of the original broken URDF (NON-compounding), activate,
              evaluate, render a text observation, append to history. Not terminal. Consumes budget.
  * COMMIT:   apply the fix, evaluate, TERMINAL, return the terminal score.
  * NO_FIX:   evaluate the broken object unchanged (assert "already functional").
  * budget K of SIMULATE calls; run_episode auto-commits the best simulated fix if exhausted.

The scoring signal is evaluation.evaluate_repair (deviation vs tau AND door closes AND no
part-collision -> PASS) -- the adopted contract; score.py's open-sweep is superseded.

Feedback modes (what the agent sees each step):
  "headline" : symbolic part poses + the list of FAILED criteria (no raw scalar) -- the true task.
  "scalar"   : the above PLUS the numeric functional score (ablation).
The agent never sees centroid/pivot; env injects those canonical params (canonical.py).
"""
import math
import os
import sys

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonical  # noqa: E402
import corruption as corr  # noqa: E402
import geom  # noqa: E402
from evaluation import evaluate_repair  # noqa: E402
from part_table import build_part_table  # noqa: E402
from quiet import quiet  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def _inject_canonical(spec, urdf):
    """Fill the canonical geometry params the agent does not supply (rotation centre / scale pivot),
    recomputed from the current URDF so they equal the values the break used (see canonical.py)."""
    if spec["type"] == "rotate":
        return dict(spec, centroid=canonical.part_centroid(urdf, spec["link"]))
    if spec["type"] == "scale":
        return dict(spec, pivot=canonical.scale_pivot(urdf, spec["link"], spec["axis"]))
    return spec


def _part_states(urdf, id_map):
    """Per-part GEOMETRY centroid + axis-aligned bbox size in the part's own LINK frame, keyed by
    joint name.

    Reported in the LINK frame (not world) so the axes match BOTH the action axes and the part-table
    bbox -- when the agent commands axis Y it sees the Y coordinate move. We report the mesh geometry
    (not the link-frame origin): corruptions move the mesh WITHIN the link frame and leave the
    hinge/joint untouched, so a link-origin readout would be invariant and useless. The centroid
    shifts under translate/scale and the bbox size changes under scale/rotate, giving the agent a
    real, observable effect of its action. The hidden HEALTHY target is never shown -- it must search."""
    states = {}
    for pt in id_map.values():
        pts = geom.link_frame_points(_abs(urdf), pt["link"])
        if len(pts):
            c = pts.mean(0)
            ext = pts.max(0) - pts.min(0)
            states[pt["joint"]] = ([float(x) for x in c], [float(x) for x in ext])
        else:
            states[pt["joint"]] = ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    return states


class FridgeRepairEnv:
    def __init__(self, budget=6, feedback="headline"):
        assert feedback in ("headline", "scalar")
        self.budget = budget
        self.feedback = feedback
        self.client = p.connect(p.DIRECT)

    def close(self):
        if self.client is not None:
            p.disconnect(self.client)
            self.client = None

    # ---------------------------------------------------------------- episode lifecycle
    def reset(self, instance):
        self.instance = instance
        self.broken = _abs(instance["broken_urdf"])
        self.healthy = _abs(instance["healthy_urdf"])
        self.joint = instance["joint"]
        self.link = instance["link"]
        self.table_text, self.id_map = build_part_table(self.broken)
        self.target_pid = next(pid for pid, pt in self.id_map.items() if pt["link"] == self.link)
        self.sim_count = 0
        self.invalid_count = 0
        self.history = []          # list of dicts: {mode, action_str, eval}
        self.best = None           # best simulated {eval, spec, action_str, score}
        self.terminal = False
        ev = self._evaluate_spec(None)     # broken as-is
        self.reset_eval = ev
        return {"text": self._render(ev, header="BROKEN OBJECT (initial)"),
                "eval": ev, "part_table": self.table_text, "target_pid": self.target_pid}

    def step(self, parsed):
        """parsed: action_parser.parse() result. Returns (observation, terminal, info)."""
        assert not self.terminal, "episode already terminal"
        if not parsed["valid"]:
            self.invalid_count += 1
            return ({"text": f"INVALID ACTION: {parsed['error']}", "eval": None,
                     "invalid": True}, False, {"error": parsed["error"]})

        act = parsed["action"]
        mode = parsed["mode"]
        spec = None if act["type"] == "no_fix" else _inject_canonical(act["spec"], self.broken)
        action_str = self._action_str(act)
        ev = self._evaluate_spec(spec)

        if mode == "SIMULATE":
            self.sim_count += 1
            rec = {"mode": "SIMULATE", "action_str": action_str, "eval": ev,
                   "backtrack": parsed["backtrack"], "think": parsed.get("think", "")}
            self.history.append(rec)
            if self.best is None or ev["score"] > self.best["eval"]["score"]:
                self.best = {"eval": ev, "spec": spec, "action_str": action_str}
            obs = {"text": self._render(ev, header=f"SIMULATE result ({action_str})"),
                   "eval": ev, "invalid": False}
            return obs, False, {"budget_left": self.budget - self.sim_count}

        # COMMIT (or NO_FIX committed)
        self.terminal = True
        self.history.append({"mode": "COMMIT", "action_str": action_str, "eval": ev,
                             "backtrack": parsed["backtrack"], "think": parsed.get("think", "")})
        return ({"text": self._render(ev, header=f"COMMITTED ({action_str})"), "eval": ev,
                 "invalid": False}, True, {"committed_action": action_str})

    def auto_commit_best(self):
        """Budget exhausted with no COMMIT: commit the best-scoring simulated fix (or the broken
        object if nothing was simulated). Returns (observation, eval)."""
        self.terminal = True
        if self.best is not None:
            ev, action_str = self.best["eval"], self.best["action_str"]
        else:
            ev, action_str = self.reset_eval, "NO_FIX() [auto]"
        self.history.append({"mode": "AUTO_COMMIT", "action_str": action_str, "eval": ev})
        return {"text": self._render(ev, header=f"AUTO-COMMIT best ({action_str})"), "eval": ev}, ev

    # ---------------------------------------------------------------- internals
    def _action_str(self, act):
        if act["type"] == "no_fix":
            return "NO_FIX()"
        s = act["spec"]
        ax = "XYZ"[s["axis"]]
        if s["type"] == "translate":
            return f"TRANSLATE({act['part_id']}, {ax}, {s['value']:.4f})"
        if s["type"] == "rotate":
            return f"ROTATE({act['part_id']}, {ax}, {math.degrees(s['value']):.1f})"
        return f"SCALE({act['part_id']}, {ax}, {s['value']:.4f})"

    def _evaluate_spec(self, spec):
        """Apply spec to a COPY of the broken URDF (or evaluate broken as-is if spec is None),
        score it against the contract, and capture the candidate's part states for the observation."""
        if spec is None:
            cand = self.broken
            tmp = None
        else:
            tmp = corr.apply(self.broken, spec, f"_cand_{self.instance['id']}.urdf")
            cand = tmp
        with quiet():
            ev = evaluate_repair(cand, self.healthy, self.joint, self.link, client=self.client)
        ev = dict(ev, states=_part_states(cand, self.id_map))
        if tmp is not None and os.path.exists(tmp):
            os.remove(tmp)
        return ev

    def _failed_criteria(self, ev):
        out = []
        if not ev["within_tol"]:
            out.append(f"pose off by {ev['deviation_mm']:.0f} mm (tolerance {ev['tau_mm']:.0f} mm)")
        if not ev["closes"]:
            out.append(f"door does not close (jams at {ev['closed_angle_deg']:.0f} deg)")
        if ev["collides"]:
            pair = ev["collision_pair"] or "parts"
            out.append(f"part collision ({pair}, {ev['collision_excess_mm']:.0f} mm over healthy)")
        return out

    def _render(self, ev, header):
        states = ev.get("states", {})
        lines = [header, "", "part states (geometry centre and size in the part's own X,Y,Z axes):"]
        for pid, pt in self.id_map.items():
            c, e = states.get(pt["joint"], ([0, 0, 0], [0, 0, 0]))
            lines.append(f"  {pid} {pt['name']:<14} center=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}] "
                         f"size(w,d,h)=[{e[0]:.3f},{e[1]:.3f},{e[2]:.3f}]")
        failed = self._failed_criteria(ev)
        lines.append("")
        if ev["PASS"]:
            lines.append("criteria: ALL PASS (door within tolerance, closes, no collision)")
        else:
            lines.append("failed criteria: " + "; ".join(failed))
        if self.feedback == "scalar":
            lines.append(f"functional_score = {ev['score']:.3f}  (PASS threshold = within tol & closes & no collision)")
        return "\n".join(lines)
