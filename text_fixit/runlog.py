#!/usr/bin/env python
"""
Exhaustive run logging: nothing a run produces may be lost.

A run costs hours of API time, so every artifact that could be wanted later is written at the moment
it exists, flushed immediately -- a killed or crashed run keeps everything up to that point rather
than losing a buffered tail.

Layout under runs/<run>/<agent>/:

  manifest.json            run config: model, contract, modality, deviation, budget, tau_frac,
                           instance file + sha256, git commit, agent settings, timestamps, versions
  records.jsonl            one line per EPISODE (the metrics substrate)
  turns.jsonl              one line per MODEL TURN: verbatim <think>, verbatim raw output, parsed
                           actions, validity, per-part evaluation after the action, latency, tokens
  prompts/<id>_tNN.txt     the exact system + user text sent that turn
  images/<id>/tNN_k.png    every rendered view actually sent that turn
  raw/<id>.jsonl           raw API response metadata per call (finish reason, usage, retries)
  errors.jsonl             every API error, empty reply, parse failure and reparse attempt
  trajectories/<id>.md     human-readable rollout for review

The summary tables in runs/_analysis/ are DERIVED from these files; they never replace them.
"""
import hashlib
import json
import os
import subprocess
import sys
import time


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       cwd=os.path.dirname(os.path.abspath(__file__)),
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:  # noqa: BLE001 - not a git checkout / git missing
        return None


def _versions():
    out = {"python": sys.version.split()[0]}
    for mod in ("pybullet", "numpy", "PIL", "google.genai"):
        try:
            m = __import__(mod, fromlist=["__version__"])
            out[mod] = getattr(m, "__version__", "unknown")
        except Exception:  # noqa: BLE001 - optional dependency
            out[mod] = None
    return out


class RunLogger:
    """One logger per (run, agent). Every write is append-and-flush."""

    def __init__(self, run_dir, agent_name, enabled=True):
        self.enabled = enabled
        self.dir = os.path.join(run_dir, agent_name)
        if not enabled:
            return
        for sub in ("", "prompts", "images", "raw", "trajectories"):
            os.makedirs(os.path.join(self.dir, sub), exist_ok=True)
        self._records = open(os.path.join(self.dir, "records.jsonl"), "w")
        self._turns = open(os.path.join(self.dir, "turns.jsonl"), "w")
        self._errors = open(os.path.join(self.dir, "errors.jsonl"), "w")

    # ------------------------------------------------------------------ config
    def manifest(self, **cfg):
        if not self.enabled:
            return
        inst = cfg.get("instances_path")
        cfg.update({
            "git_commit": _git_commit(),
            "versions": _versions(),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "instances_sha256": _sha256(inst) if inst and os.path.exists(inst) else None,
            "argv": sys.argv,
        })
        with open(os.path.join(self.dir, "manifest.json"), "w") as f:
            json.dump(cfg, f, indent=2, default=str)

    def finish(self, **summary):
        if not self.enabled:
            return
        path = os.path.join(self.dir, "manifest.json")
        cfg = json.load(open(path)) if os.path.exists(path) else {}
        cfg["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        cfg["summary"] = summary
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2, default=str)
        for h in (self._records, self._turns, self._errors):
            h.close()

    # ------------------------------------------------------------------ per-turn
    def _write(self, handle, obj):
        handle.write(json.dumps(obj, default=str) + "\n")
        handle.flush()

    def turn(self, obj):
        if self.enabled:
            self._write(self._turns, obj)

    def error(self, obj):
        if self.enabled:
            self._write(self._errors, obj)

    def episode(self, obj):
        if self.enabled:
            self._write(self._records, obj)

    def prompt(self, episode_id, turn, system, user):
        """The exact text sent. Written even in image conditions -- the text half is still the
        instruction the model followed."""
        if not self.enabled:
            return
        path = os.path.join(self.dir, "prompts", f"{episode_id}_t{turn:02d}.txt")
        with open(path, "w") as f:
            f.write("===== SYSTEM =====\n")
            f.write((system or "") + "\n\n")
            f.write("===== USER =====\n")
            f.write((user or "") + "\n")

    def images(self, episode_id, turn, pil_images):
        """Every view actually attached to this turn's request."""
        if not self.enabled or not pil_images:
            return []
        d = os.path.join(self.dir, "images", episode_id)
        os.makedirs(d, exist_ok=True)
        paths = []
        for k, im in enumerate(pil_images):
            path = os.path.join(d, f"t{turn:02d}_{k}.png")
            try:
                im.save(path)
                paths.append(os.path.relpath(path, self.dir))
            except Exception as e:  # noqa: BLE001 - never let logging kill a run
                self.error({"episode": episode_id, "turn": turn, "kind": "image_save", "err": str(e)})
        return paths

    def raw(self, episode_id, payload):
        if not self.enabled:
            return
        with open(os.path.join(self.dir, "raw", f"{episode_id}.jsonl"), "a") as f:
            f.write(json.dumps(payload, default=str) + "\n")

    # ------------------------------------------------------------------ readable rollout
    def trajectory(self, rec, turns):
        """Human-readable rollout: what the model saw, thought, did, and what happened."""
        if not self.enabled:
            return
        L = [f"# {rec['id']}  ({rec.get('level', 'single')})", "",
             f"- agent: `{rec['agent']}`  ·  contract: `{rec.get('contract')}`  ·  "
             f"modality: `{rec['state_modality']}`  ·  deviation: `{rec['show_deviation']}`",
             f"- faults ({rec.get('n_faults', 1)}): "
             + ", ".join(rec.get("fault_types", []) or [rec.get("corruption_type", "?")])
             + f"  on {rec.get('faulty_links', [])}",
             f"- ground-truth fix sequence: {rec.get('gt_fix_actions', 'n/a')}",
             f"- **terminal: PASS={rec['terminal_pass']}  score={rec['terminal_score']:.3f}  "
             f"deviation={rec['terminal_deviation_mm']:.1f} mm  "
             f"simulates={rec['n_simulate']}**", ""]
        for t in turns:
            L += [f"## turn {t['turn']}  ({t.get('mode') or 'invalid'})", "",
                  f"- budget left: {t.get('budget_left')}"
                  + (f"  ·  images sent: {len(t.get('image_paths') or [])}"
                     if t.get("image_paths") else "")
                  + (f"  ·  latency: {t['latency_s']:.1f}s" if t.get("latency_s") else ""), ""]
            if t.get("think"):
                L += ["**reasoning**", "", "> " + t["think"].replace("\n", "\n> "), ""]
            L += [f"**action** `{t.get('action_str') or t.get('raw_action') or ''}`", ""]
            if t.get("invalid"):
                L += [f"- INVALID: {t.get('parse_error')}", ""]
            else:
                L += [f"- PASS={t.get('pass')}  score={t.get('score')}  "
                      f"deviation={t.get('deviation_mm')} mm", ""]
                pp = t.get("per_part") or {}
                if pp:
                    L += ["| part | deviation mm | within tol | closes |", "|---|---|---|---|"]
                    L += [f"| {k} | {v['deviation_mm']} | {v['within_tol']} | {v['closes']} |"
                          for k, v in pp.items()]
                    L += [""]
            if t.get("image_paths"):
                L += [f"![turn {t['turn']}]({pth})" for pth in t["image_paths"]] + [""]
        path = os.path.join(self.dir, "trajectories", f"{rec['id']}.md")
        with open(path, "w") as f:
            f.write("\n".join(L))
