#!/usr/bin/env python
"""
FridgeRepairEnv -- a Gym-style closed loop for fridge repair, single-fault or COMPOSITE.

Contract (matches the paper's simulator, MILESTONE_1 loop, and the SIMULATE/COMMIT prompt):

  reset(instance)            -> observation for the BROKEN object
  step(parsed_action)        -> (observation, terminal, info)

  * SIMULATE: apply the fix, evaluate, render an observation, append to history. Not terminal.
              Consumes budget.
  * COMMIT:   apply the fix, evaluate, TERMINAL, return the terminal score.
  * NO_FIX:   evaluate the broken object unchanged (assert "already functional").
  * budget K of SIMULATE calls; run_episode auto-commits the best simulated fix if exhausted.

TWO ACTION CONTRACTS (`action_contract`), the axis this env exists to compare:

  "batch"  A turn carries an ordered LIST of actions, applied in order to a fresh copy of the
           ORIGINAL broken object -- attempts never stack, so the agent must always issue the FULL
           correction. Repairing a 3-fault break means planning all three magnitudes before seeing
           any feedback on them.
  "stack"  A turn carries ONE action, applied on top of a persisted WORKING STATE that accumulates
           across SIMULATEs -- the MDP framing. RESET() discards the working state (costing a budget
           step) so a bad step is recoverable; a bare COMMIT commits the working state as-is.

The working state is represented as a LIST OF SPECS rather than a URDF on disk: any state is
`apply(broken, specs)`, so RESET is just clearing the list, "best so far" is just a list, and the
two contracts share one evaluation path. Canonical params (rotation centre / scale pivot) are
injected PER OP from the intermediate state that op actually acts on -- which is what makes an
ordered sequence of repairs exactly expressible in the agent's parameter-free action space.

The scoring signal is evaluation.evaluate_repair_multi (every faulty part within tau AND every
faulty door closes AND no part-collision -> PASS).

Observation toggles:
  state_modality "text"  -> per-part geometry text; "image" -> rendered closed views.
  show_deviation True    -> include the numeric 'pose off by N mm' gradient; False -> hide it.
  hard True              -> hide the part table's fixable/role columns AND render doors in one
                            neutral colour from a less favourable yaw (the hard benchmark).
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
from action_parser import format_call  # noqa: E402
from evaluation import evaluate_repair_multi  # noqa: E402
from part_table import build_part_table  # noqa: E402
from quiet import quiet  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def _inject_canonical(spec, urdf):
    """Fill the canonical geometry params the agent does not supply (rotation centre / scale pivot),
    recomputed from the URDF THIS op is applied to, so they equal the values the break used at the
    matching point of the sequence (see canonical.py)."""
    if spec["type"] == "rotate":
        return dict(spec, centroid=canonical.part_centroid(urdf, spec["link"]))
    if spec["type"] == "scale":
        return dict(spec, pivot=canonical.scale_pivot(urdf, spec["link"], spec["axis"]))
    return spec


def _instance_faults(instance):
    """Fault list for either schema: the composite `faults` list, or the legacy single link/joint."""
    if instance.get("faults"):
        return [{"link": f["link"], "joint": f["joint"], "part_name": f.get("part_name", "")}
                for f in instance["faults"]]
    return [{"link": instance["link"], "joint": instance["joint"],
             "part_name": instance.get("part_name", "")}]


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
    """See the module docstring for the observation toggles and the two action contracts."""

    def __init__(self, budget=6, state_modality="text", show_deviation=True,
                 action_contract="batch", hard=False,
                 reveal_fixable=None, hard_render=None, multi_fault_hint=None,
                 max_actions=None):
        """`hard` is a preset for the three hardening switches below; each can be overridden
        independently, because they are separable difficulties and worth varying one at a time:

          reveal_fixable    show the part table's role/fixable columns (False = the agent must work
                            out which parts are repairable)
          hard_render       one neutral colour for every door + an adverse camera yaw
          multi_fault_hint  tell the agent that several parts, and several faults per part, are
                            possible (without revealing the count)
        """
        assert state_modality in ("text", "image")
        assert action_contract in ("batch", "stack")
        self.budget = budget
        self.state_modality = state_modality
        self.show_deviation = show_deviation
        self.action_contract = action_contract
        # Cap on actions per turn. The `one_error` prompt promises exactly one; batch otherwise
        # accepts up to MAX_ACTIONS_PER_TURN, so the promise has to be enforced here.
        self.max_actions = max_actions
        self.hard = hard
        self.reveal_fixable = (not hard) if reveal_fixable is None else reveal_fixable
        self.hard_render = hard if hard_render is None else hard_render
        self.multi_fault_hint = hard if multi_fault_hint is None else multi_fault_hint
        self.client = p.connect(p.DIRECT)
        # unique token so concurrent runs (the conditions share the same instances) never clobber
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
        self.faults = _instance_faults(instance)
        self.faulty_links = list(dict.fromkeys(f["link"] for f in self.faults))
        # legacy single-fault attributes, still used by tooling that predates composite instances
        self.link = self.faults[0]["link"]
        self.joint = self.faults[0]["joint"]

        # A tau mismatch between generation and evaluation would silently mis-score the whole run.
        tf = instance.get("tau_frac")
        if tf is not None and abs(tf - geom.TAU_FRAC) > 1e-12:
            raise RuntimeError(f"instance {instance['id']} was generated at tau_frac={tf} but "
                               f"geom.TAU_FRAC={geom.TAU_FRAC}; set FIXIT_TAU_FRAC={tf}")

        self.table_text, self.id_map = build_part_table(self.broken,
                                                        reveal_fixable=self.reveal_fixable)
        self.pid_of_link = {pt["link"]: pid for pid, pt in self.id_map.items()}
        self.target_pids = [self.pid_of_link[ln] for ln in self.faulty_links
                            if ln in self.pid_of_link]
        self.target_pid = self.target_pids[0] if self.target_pids else None

        self.sim_count = 0
        self.invalid_count = 0
        self.reset_count = 0
        self.history = []          # list of dicts: {mode, action_str, eval, think, backtrack}
        self.best = None           # best simulated {eval, specs, action_str}
        self.terminal = False
        self.working_specs = []    # stack contract: raw specs accumulated so far
        self._eval_seq = 0         # candidate filenames must be UNIQUE -- see _evaluate_specs
        self._img_cache = {}       # state key -> [PIL images] (a state is deterministic per key)
        self._annotated = None
        self._last_images = []     # views most recently shown -> re-sent on an INVALID ACTION turn
        # baseline reference: the ORIGINAL broken part geometry (link frame), shown every turn
        self._broken_states = _part_states(self.broken, self.id_map)
        if self.state_modality == "image":
            self.center, self.dist = R.camera_from_urdf(self.healthy)   # locked to healthy shape
            with quiet():
                self._annotated = views.annotated_part_view(self.broken, self.id_map,
                                                            self.center, self.dist, hard=self.hard_render)
        ev = self._evaluate_specs([], "broken")     # broken as-is
        self.reset_eval = ev
        # cache the ORIGINAL broken object's views -> shown every turn as the "before"
        self._broken_views = list(ev.get("images", []))
        obs = {"text": self._render(ev, header="BROKEN OBJECT (initial)", reset=True),
               "eval": ev, "part_table": self.table_text, "target_pid": self.target_pid,
               "images": self._obs_images(ev, reset=True)}
        return obs

    def step(self, parsed):
        """parsed: action_parser.parse() result. Returns (observation, terminal, info)."""
        assert not self.terminal, "episode already terminal"
        if not parsed["valid"]:
            self.invalid_count += 1
            # An unparseable reply must not also blind the model. This observation used to carry no
            # "images" key at all, so run_episode's `obs.get("images", [])` sent ZERO images on the
            # turn after every malformed output -- 203/203 of the image-less turns in the std30 Qwen
            # arms followed a parse error. On a model that emits prose instead of the action grammar
            # that is a doom loop: bad format -> blind -> worse format. Re-show the views it had.
            return ({"text": f"INVALID ACTION: {parsed['error']}", "eval": None,
                     "invalid": True, "images": list(self._last_images)},
                    False, {"error": parsed["error"]})

        actions = parsed["actions"]
        mode = parsed["mode"]
        is_reset = bool(actions) and actions[0]["type"] == "reset"
        is_no_fix = bool(actions) and actions[0]["type"] == "no_fix"

        if is_reset:
            self.working_specs = []
            self.reset_count += 1
            specs, action_str = [], "RESET()"
        elif is_no_fix:
            specs, action_str = [], "NO_FIX()"
        else:
            new = [a["spec"] for a in actions]
            # batch: the turn's list IS the whole candidate, applied fresh to the broken object.
            # stack: the turn's single action is appended to the persisted working state.
            specs = new if self.action_contract == "batch" else self.working_specs + new
            action_str = self._action_str(actions, specs)

        ev = self._evaluate_specs(specs, action_str)

        if mode == "SIMULATE":
            self.sim_count += 1
            if self.action_contract == "stack" and not is_reset:
                self.working_specs = specs          # the step sticks
            rec = {"mode": "SIMULATE", "action_str": action_str, "eval": ev,
                   "backtrack": parsed["backtrack"], "think": parsed.get("think", ""),
                   "n_actions": len(actions), "state_specs": len(specs)}
            self.history.append(rec)
            if self.best is None or ev["score"] > self.best["eval"]["score"]:
                self.best = {"eval": ev, "specs": list(specs), "action_str": action_str}
            obs = {"text": self._render(ev, header=f"SIMULATE result ({action_str})"),
                   "eval": ev, "invalid": False, "images": self._obs_images(ev)}
            return obs, False, {"budget_left": self.budget - self.sim_count}

        # COMMIT (or NO_FIX committed)
        self.terminal = True
        if self.action_contract == "stack" and not is_reset:
            self.working_specs = specs
        self.history.append({"mode": "COMMIT", "action_str": action_str, "eval": ev,
                             "backtrack": parsed["backtrack"], "think": parsed.get("think", ""),
                             "n_actions": len(actions), "state_specs": len(specs)})
        return ({"text": self._render(ev, header=f"COMMITTED ({action_str})"), "eval": ev,
                 "invalid": False, "images": self._obs_images(ev)}, True,
                {"committed_action": action_str})

    def auto_commit_best(self):
        """Budget exhausted with no COMMIT: commit the best-scoring simulated state (or the broken
        object if nothing was simulated). Returns (observation, eval)."""
        self.terminal = True
        if self.best is not None:
            ev, action_str = self.best["eval"], self.best["action_str"]
        else:
            ev, action_str = self.reset_eval, "NO_FIX() [auto]"
        self.history.append({"mode": "AUTO_COMMIT", "action_str": action_str, "eval": ev})
        return {"text": self._render(ev, header=f"AUTO-COMMIT best ({action_str})"), "eval": ev}, ev

    # ---------------------------------------------------------------- internals
    def _action_str(self, actions, specs):
        """Readable label for the turn. In stack mode the cumulative depth is appended, because the
        same call means a different candidate depending on what it is stacked on."""
        s = "; ".join(format_call(a["spec"], a["part_id"]) for a in actions)
        if len(actions) > 1:
            s = f"[{s}]"
        if self.action_contract == "stack":
            s = f"{s} @depth{len(specs)}"
        return s

    def _state_key(self, specs):
        """Deterministic key for a candidate state -- the ordered specs that produce it."""
        if not specs:
            return "broken"
        return "|".join(f"{s['type']}:{s['link']}:{s['axis']}:{s['value']:.9g}" for s in specs)

    def _build_candidate(self, specs, out_name):
        """Apply raw (uninjected) specs IN ORDER to a copy of the broken URDF, injecting each op's
        canonical params from the intermediate state it actually acts on. Returns the final path."""
        cur, tmps = self.broken, []
        for i, raw in enumerate(specs):
            spec = _inject_canonical(raw, cur)
            name = out_name if i == len(specs) - 1 else f"_i{i}_{out_name}"
            nxt = corr.apply(cur, spec, name)
            if cur != self.broken:
                tmps.append(cur)
            cur = nxt
        for t in tmps:
            if os.path.exists(t):
                os.remove(t)
        return cur

    def _evaluate_specs(self, specs, action_str="broken"):
        """Apply `specs` (possibly empty) to a COPY of the broken URDF, score against the multi-part
        contract, capture part states, and (image modality) render the candidate's views -- cached
        by the STATE key, since the same ordered specs always yield identical geometry."""
        if not specs:
            cand, tmp = self.broken, None
        else:
            # The candidate filename must be UNIQUE per evaluation. PyBullet caches parsed URDF and
            # collision geometry BY FILENAME inside a client, so rewriting one path and re-loading it
            # returns the FIRST version's bodies: `closes` and `collides` silently freeze at their
            # first-candidate values while deviation (read from the XML by geom) keeps updating.
            self._eval_seq += 1
            tmp = self._build_candidate(
                specs, f"_cand_{self.instance['id']}_{self._tok}_{self._eval_seq}.urdf")
            cand = tmp
        with quiet():
            ev = evaluate_repair_multi(cand, self.healthy, self.faults, client=self.client)
        ev = dict(ev, states=_part_states(cand, self.id_map))
        if self.state_modality == "image":
            ev = dict(ev, images=self._render_views(cand, self._state_key(specs)))
        else:
            # begin/end of the doors' activation trajectory: world centres with ALL doors driven
            # OPEN (90 deg, start) then SHUT (0 deg, end) -- shows the swing / whether they seat
            ev = dict(ev, act_start=self._world_states(cand, math.pi / 2),
                      act_end=self._world_states(cand, 0.0))
        if tmp is not None and os.path.exists(tmp):
            os.remove(tmp)
        return ev

    def _world_states(self, urdf, angle):
        """Per-part WORLD geometry centre with ALL doors driven to `angle`. Reading it at doors-open
        then doors-shut gives the two ends of the activation. ALL doors are moved (not just the faulty
        ones) so the readout never reveals which doors are broken."""
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

    def _render_views(self, cand_urdf, state_key):
        if state_key in self._img_cache:
            return self._img_cache[state_key]
        with quiet():
            imgs = views.closed_view(cand_urdf, self.center, self.dist, self.id_map, hard=self.hard_render)
        self._img_cache[state_key] = imgs
        return imgs

    def _obs_images(self, ev, reset=False):
        """Images attached to an observation: the ORIGINAL broken object as the 'before', then the
        current candidate as the 'after'. Reset shows the labelled part view + the broken view.
        Empty for the text conditions.

        The result is cached in _last_images so the INVALID-ACTION observation in step() can re-show
        the views the model was already looking at instead of sending it a blind turn."""
        if self.state_modality != "image":
            self._last_images = []
            return []
        broken = list(getattr(self, "_broken_views", []))
        if reset:
            out = ([self._annotated] if self._annotated is not None else []) + broken
        else:
            out = broken + list(ev.get("images", []))
        self._last_images = list(out)
        return out

    def _render(self, ev, header, reset=False):
        lines = [header, ""]
        if self.state_modality == "text":
            lines.append("original broken (reference) - part geometry [centre; size] in each part's X,Y,Z:")
            for pid, pt in self.id_map.items():
                c, e = self._broken_states.get(pt["joint"], ([0, 0, 0], [0, 0, 0]))
                lines.append(f"  {pid} {pt['name']:<14} centre=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}] "
                             f"size=[{e[0]:.3f},{e[1]:.3f},{e[2]:.3f}]")
            st, en = ev.get("act_start", {}), ev.get("act_end", {})
            lines.append("")
            label = ("current working state" if self.action_contract == "stack" and not reset
                     else "your attempt")
            lines.append(f"{label} - world centres at the START of activation (doors open):")
            for pid, pt in self.id_map.items():
                c = st.get(pt["joint"], [0, 0, 0])
                lines.append(f"  {pid} {pt['name']:<14} centre=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}]")
            lines.append(f"{label} - world centres at the END of activation (doors shut):")
            for pid, pt in self.id_map.items():
                c = en.get(pt["joint"], [0, 0, 0])
                lines.append(f"  {pid} {pt['name']:<14} centre=[{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}]")
        elif reset:
            lines.append("(attached: the labelled parts view, then the BROKEN object with all doors "
                         "CLOSED)")
        else:
            after = ("YOUR CURRENT WORKING STATE" if self.action_contract == "stack"
                     else "YOUR FIX applied to it")
            lines.append(f"(attached: the ORIGINAL BROKEN object CLOSED, then {after} CLOSED - "
                         "compare before vs after. Parts colour-coded as in the labelled view; "
                         "body grey)")
        if self.action_contract == "stack" and not reset:
            lines.append("")
            lines.append(f"repairs currently applied to the working state: {len(self.working_specs)}"
                         " (RESET() discards them and returns to the original broken object)")
        lines.append("")

        # deviation gradient (the numeric mm) is gated; pass/fail + physical symptoms always shown
        dev = ([f"worst part off by {ev['deviation_mm']:.0f} mm (tolerance {ev['tau_mm']:.0f} mm)"]
               if self.show_deviation and not ev["within_tol"] else [])
        phys = []
        if not ev["closes"]:
            phys.append(f"a door does not close (jams at {ev['closed_angle_deg']:.0f} deg)")
        if ev["collides"]:
            phys.append(f"part collision ({ev['collision_pair'] or 'parts'}, "
                        f"{ev['collision_excess_mm']:.0f} mm over healthy)")
        if ev["PASS"]:
            lines.append("criteria: ALL PASS (every part within tolerance, doors close, no collision)")
        else:
            items = dev + phys
            if not items:                       # -deviation and physically fine: pose still wrong
                items = ["at least one part is not yet in its correct position"]
            lines.append("failed criteria: " + "; ".join(items))
        return "\n".join(lines)
