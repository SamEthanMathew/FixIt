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

import numpy as np
import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import canonical  # noqa: E402
import corruption as corr  # noqa: E402
import geom  # noqa: E402
import render as R  # noqa: E402
import views  # noqa: E402
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
    """Two orthogonal observation toggles (the modality x deviation 2x2):
      state_modality "text"  -> per-part geometry text; "image" -> rendered hero+filmstrip views.
      show_deviation True    -> include the numeric 'pose off by N mm' gradient; False -> hide it
                                (pass/fail + physical symptoms only; agent must infer direction)."""

    def __init__(self, budget=6, state_modality="text", show_deviation=True):
        assert state_modality in ("text", "image")
        self.budget = budget
        self.state_modality = state_modality
        self.show_deviation = show_deviation
        self.client = p.connect(p.DIRECT)
        # unique token so concurrent runs (the 4 conditions share the same instances) never clobber
        # each other's temp candidate URDF written beside the meshes.
        self._tok = f"{os.getpid()}_{id(self) & 0xffff}"

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
        self._img_cache = {}       # action_str -> [PIL images] (SIMULATE is deterministic per action)
        self._annotated = None
        # baseline reference: the ORIGINAL broken part geometry (link frame), shown every turn
        self._broken_states = _part_states(self.broken, self.id_map)
        if self.state_modality == "image":
            self.center, self.dist = R.camera_from_urdf(self.healthy)   # locked to healthy shape
            with quiet():
                self._annotated = views.annotated_part_view(self.broken, self.id_map,
                                                            self.center, self.dist)
        ev = self._evaluate_spec(None, "broken")     # broken as-is
        self.reset_eval = ev
        obs = {"text": self._render(ev, header="BROKEN OBJECT (initial)"),
               "eval": ev, "part_table": self.table_text, "target_pid": self.target_pid,
               "images": self._obs_images(ev, reset=True)}
        return obs

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
        ev = self._evaluate_spec(spec, action_str)

        if mode == "SIMULATE":
            self.sim_count += 1
            rec = {"mode": "SIMULATE", "action_str": action_str, "eval": ev,
                   "backtrack": parsed["backtrack"], "think": parsed.get("think", "")}
            self.history.append(rec)
            if self.best is None or ev["score"] > self.best["eval"]["score"]:
                self.best = {"eval": ev, "spec": spec, "action_str": action_str}
            obs = {"text": self._render(ev, header=f"SIMULATE result ({action_str})"),
                   "eval": ev, "invalid": False, "images": self._obs_images(ev)}
            return obs, False, {"budget_left": self.budget - self.sim_count}

        # COMMIT (or NO_FIX committed)
        self.terminal = True
        self.history.append({"mode": "COMMIT", "action_str": action_str, "eval": ev,
                             "backtrack": parsed["backtrack"], "think": parsed.get("think", "")})
        return ({"text": self._render(ev, header=f"COMMITTED ({action_str})"), "eval": ev,
                 "invalid": False, "images": self._obs_images(ev)}, True,
                {"committed_action": action_str})

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

    def _evaluate_spec(self, spec, action_str="broken"):
        """Apply spec to a COPY of the broken URDF (or evaluate broken as-is if spec is None),
        score it against the contract, capture part states, and (image modality) render the
        candidate's views -- cached by action_str, since SIMULATE re-applies to the original broken
        object, so a repeated action yields identical geometry and identical renders."""
        if spec is None:
            cand = self.broken
            tmp = None
        else:
            tmp = corr.apply(self.broken, spec, f"_cand_{self.instance['id']}_{self._tok}.urdf")
            cand = tmp
        with quiet():
            ev = evaluate_repair(cand, self.healthy, self.joint, self.link, client=self.client)
        ev = dict(ev, states=_part_states(cand, self.id_map))
        if self.state_modality == "image":
            ev = dict(ev, images=self._render_views(cand, action_str))
        else:
            # begin/end of the door's activation trajectory: world centres with the target door
            # driven OPEN (90 deg, start) then SHUT (0 deg, end) -- shows the swing / whether it seats
            ev = dict(ev, act_start=self._world_states(cand, math.pi / 2),
                      act_end=self._world_states(cand, 0.0))
        if tmp is not None and os.path.exists(tmp):
            os.remove(tmp)
        return ev

    def _world_states(self, urdf, angle):
        """Per-part WORLD geometry centre with ALL doors driven to `angle`. Reading it at doors-open
        then doors-shut gives the two ends of the activation. ALL doors are moved (not just the faulty
        one) so the readout never reveals which door is broken."""
        with quiet():
            body = p.loadURDF(_abs(urdf), [0, 0, 0], useFixedBase=1, physicsClientId=self.client)
            jidx = {}
            for j in range(p.getNumJoints(body, physicsClientId=self.client)):
                info = p.getJointInfo(body, j, physicsClientId=self.client)
                jidx[info[1].decode()] = j
                a = angle if info[2] == p.JOINT_REVOLUTE else 0.0
                p.resetJointState(body, j, a, physicsClientId=self.client)
            out = {}
            for pt in self.id_map.values():
                ls = p.getLinkState(body, jidx[pt["joint"]], computeForwardKinematics=True,
                                    physicsClientId=self.client)
                Rw = np.array(p.getMatrixFromQuaternion(ls[5])).reshape(3, 3)
                tw = np.array(ls[4])
                lf = geom.link_frame_points(_abs(urdf), pt["link"])
                c = (lf @ Rw.T + tw).mean(0) if len(lf) else np.zeros(3)
                out[pt["joint"]] = [float(x) for x in c]
            p.removeBody(body, physicsClientId=self.client)
        return out

    def _render_views(self, cand_urdf, action_str):
        if action_str in self._img_cache:
            return self._img_cache[action_str]
        with quiet():
            imgs = views.open_closed_views(cand_urdf, self.joint, self.center, self.dist, self.id_map)
        self._img_cache[action_str] = imgs
        return imgs

    def _obs_images(self, ev, reset=False):
        """Images attached to an observation: candidate hero A/B + closing filmstrip, plus the
        labeled part view once at reset. Empty for the text conditions."""
        if self.state_modality != "image":
            return []
        imgs = list(ev.get("images", []))
        if reset and self._annotated is not None:
            imgs = [self._annotated] + imgs
        return imgs

    def _render(self, ev, header):
        lines = [header, ""]
        if self.state_modality == "text":
            lines.append("original broken (reference) - part geometry [centre; size] in each part's X,Y,Z:")
            for pid, pt in self.id_map.items():
                c, e = self._broken_states.get(pt["joint"], ([0, 0, 0], [0, 0, 0]))
                lines.append(f"  {pid} {pt['name']:<14} centre=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}] "
                             f"size=[{e[0]:.3f},{e[1]:.3f},{e[2]:.3f}]")
            st, en = ev.get("act_start", {}), ev.get("act_end", {})
            lines.append("")
            lines.append("your attempt - world centres at the START of activation (doors open):")
            for pid, pt in self.id_map.items():
                c = st.get(pt["joint"], [0, 0, 0])
                lines.append(f"  {pid} {pt['name']:<14} centre=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}]")
            lines.append("your attempt - world centres at the END of activation (doors shut):")
            for pid, pt in self.id_map.items():
                c = en.get(pt["joint"], [0, 0, 0])
                lines.append(f"  {pid} {pt['name']:<14} centre=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}]")
        else:
            lines.append("(see the attached views: all doors CLOSED, then all doors OPEN at 90 "
                         "degrees; parts colour-coded by id as in the labelled view, body grey)")
        lines.append("")

        # deviation gradient (the numeric mm) is gated; pass/fail + physical symptoms always shown
        dev = ([f"pose off by {ev['deviation_mm']:.0f} mm (tolerance {ev['tau_mm']:.0f} mm)"]
               if self.show_deviation and not ev["within_tol"] else [])
        phys = []
        if not ev["closes"]:
            phys.append(f"door does not close (jams at {ev['closed_angle_deg']:.0f} deg)")
        if ev["collides"]:
            phys.append(f"part collision ({ev['collision_pair'] or 'parts'}, "
                        f"{ev['collision_excess_mm']:.0f} mm over healthy)")
        if ev["PASS"]:
            lines.append("criteria: ALL PASS (door within tolerance, closes, no collision)")
        else:
            items = dev + phys
            if not items:                       # -deviation and physically fine: pose still wrong
                items = ["the door is not yet in its correct position"]
            lines.append("failed criteria: " + "; ".join(items))
        return "\n".join(lines)
