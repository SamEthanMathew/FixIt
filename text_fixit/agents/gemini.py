#!/usr/bin/env python
"""
Gemini-backed agent (the off-the-shelf ceiling; Stage-1, no training).

Provider-agnostic loop input: run_episode hands us ctx (env state, budget, history); we fill the
system + step prompt templates and return the model's raw tagged text, which run_episode parses
exactly like every other agent. A Qwen backend can drop in behind the same act() contract later.

API key from env var RPAD_GEMINI_API_KEY (never hard-coded). Model via env GEMINI_MODEL
(default gemini-2.5-flash). oneshot=True => propose once from the broken object and COMMIT, no
feedback (isolates the value of the loop).
"""
import os
import re
import sys
import time
from string import Template

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grids  # noqa: E402
from agents.base import Agent  # noqa: E402

_PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")

# Per-category task text (fridge only for M1).
FUNCTION_TEXT = {
    "Refrigerator": "Open and close the door: the door must swing to 90 degrees without colliding "
                    "with the body or the other door, and must close flush.",
}
SUCCESS_TEXT = {
    "Refrigerator": "The faulty door is restored to its correct pose (within tolerance), the door "
                    "still closes, and no parts interpenetrate.",
}

VALUE_GRID_STR = f"multiples of {grids.TRANSLATE_STEP} m up to +/-{max(grids.VALUE_GRID)} m"
ANGLE_GRID_STR = f"multiples of {int(grids.ANGLE_STEP)} deg up to +/-{int(max(grids.ANGLE_GRID))} deg"
SCALE_GRID_STR = (f"log-spaced factors {min(grids.SCALE_GRID):.2f}..{max(grids.SCALE_GRID):.2f} "
                  f"(reciprocal-symmetric, e.g. 0.74, 0.82, 0.90, 1.11, 1.22, 1.35)")


def _load(name):
    with open(os.path.join(_PROMPT_DIR, name)) as f:
        return Template(f.read())


class GeminiAgent(Agent):
    def __init__(self, oneshot=False, model=None, temperature=0.7, max_tokens=800):
        self.oneshot = oneshot
        self.name = "oneshot_gemini" if oneshot else "loop_gemini"
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._system_tmpl = _load("system.txt")
        self._step_tmpl = _load("step.txt")
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            from google import genai
            key = os.environ.get("RPAD_GEMINI_API_KEY")
            if not key:
                raise RuntimeError("RPAD_GEMINI_API_KEY not set")
            self._client = genai.Client(api_key=key)
        return self._client

    def _system_prompt(self, env):
        cat = env.instance.get("category", "Refrigerator")
        return self._system_tmpl.safe_substitute(
            category=cat, instance_id=env.instance["id"],
            function_text=FUNCTION_TEXT.get(cat, ""), success_text=SUCCESS_TEXT.get(cat, ""),
            part_table=env.table_text, value_grid=VALUE_GRID_STR, angle_grid=ANGLE_GRID_STR,
            scale_grid=SCALE_GRID_STR, K=(0 if self.oneshot else env.budget))

    def _history_text(self, env):
        hist = [h for h in env.history if h["mode"] == "SIMULATE"][-3:]
        if not hist:
            return "  none yet"
        lines = []
        for h in hist:
            ev = h["eval"]
            crit = "PASS" if ev["PASS"] else "; ".join(env._failed_criteria(ev)) or "not restored"
            extra = f"  score={ev['score']:.3f}" if env.feedback == "scalar" else ""
            lines.append(f"  {h['action_str']} -> {crit}{extra}")
        return "\n".join(lines)

    def _step_prompt(self, env, obs, budget_left):
        if self.oneshot:
            note = " -- you get NO simulations; output a single COMMIT action now"
        elif budget_left <= 0:
            note = " -- budget exhausted, you MUST COMMIT now"
        else:
            note = ""
        return self._step_tmpl.safe_substitute(
            observation=obs["text"], budget_left=(0 if self.oneshot else budget_left),
            commit_note=note, history=self._history_text(env))

    def act(self, ctx):
        env, obs = ctx["env"], ctx["obs"]
        system = self._system_prompt(env)
        step = self._step_prompt(env, obs, ctx["budget_left"])
        if ctx.get("retry_error"):
            step += (f"\n\nYour previous output was invalid: {ctx['retry_error']}. "
                     "Re-emit exactly one <think> and one <act> block with a valid action.")
        raw = self._generate(system, step)
        if self.oneshot:                       # force a single commit, no matter what it emitted
            raw = re.sub(r"\bSIMULATE\b", "COMMIT", raw, flags=re.IGNORECASE)
        return raw

    def _generate(self, system, step, retries=3):
        from google.genai import types
        client = self._client_lazy()
        cfg = types.GenerateContentConfig(system_instruction=system, temperature=self.temperature,
                                          max_output_tokens=self.max_tokens)
        # gemini-2.5-* spends "thinking" tokens against max_output_tokens, which can leave the
        # visible reply empty; disable thinking (also faster + more deterministic for this task).
        if self.model.startswith("gemini-2.5"):
            try:
                cfg.thinking_config = types.ThinkingConfig(thinking_budget=0)
            except Exception:  # noqa: BLE001 - older SDKs without ThinkingConfig
                pass
        last = None
        for i in range(retries):
            try:
                resp = client.models.generate_content(model=self.model, contents=step, config=cfg)
                txt = resp.text or ""
                if txt.strip():
                    return txt
            except Exception as e:  # noqa: BLE001 - network/quota; back off and retry
                last = e
                time.sleep(1.5 * (i + 1))
        # give up -> a parseable fallback so the episode still terminates cleanly
        return f"<think>api error: {last}</think><act>COMMIT NO_FIX()</act>"
