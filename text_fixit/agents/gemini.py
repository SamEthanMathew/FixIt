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

VALUE_GRID_STR = f"any value in [-{grids.TRANSLATE_MAX}, {grids.TRANSLATE_MAX}] m (continuous)"
ANGLE_GRID_STR = f"any value in [-{int(grids.ANGLE_MAX)}, {int(grids.ANGLE_MAX)}] deg (continuous)"
SCALE_GRID_STR = f"any multiplier in [{grids.SCALE_MIN}, {grids.SCALE_MAX}] (continuous)"


def _load(name):
    with open(os.path.join(_PROMPT_DIR, name)) as f:
        return Template(f.read())


def _msg(role, text, images=None):
    """One conversation turn (role: 'user' | 'model'), with optional attached PIL images."""
    return {"role": role, "text": text, "images": images or []}


def _png_bytes(pil):
    import io
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return buf.getvalue()


class GeminiAgent(Agent):
    IMAGE_HISTORY_WINDOW = 2            # attach actual images only for the last N user turns

    def __init__(self, oneshot=False, model=None, temperature=0.7, max_tokens=8192,
                 history="window3", thinking=True):
        assert history in ("window3", "full")
        self.oneshot = oneshot
        self.history = history           # "window3": stateless call w/ last-3 summary each turn
        #                                  "full":    one accumulating conversation per object
        self.thinking = thinking
        if oneshot:
            self.name = "oneshot_gemini"
        else:
            self.name = "loop_gemini" if history == "window3" else "loop_gemini_full"
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature
        self.max_tokens = max_tokens     # high: with thinking ON the thinking tokens count here
        self._system_tmpl = _load("system.txt")
        self._system_img_tmpl = _load("system_image.txt")
        self._step_tmpl = _load("step.txt")
        self._client = None
        self._messages = []             # running transcript for history="full"

    def reset(self):
        self._messages = []

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
        tmpl = self._system_img_tmpl if getattr(env, "state_modality", "text") == "image" \
            else self._system_tmpl
        return tmpl.safe_substitute(
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
            if ev["PASS"]:
                crit = "PASS"
            else:
                parts = []
                if env.show_deviation and not ev["within_tol"]:
                    parts.append(f"off {ev['deviation_mm']:.0f}mm")
                if not ev["closes"]:
                    parts.append("jams")
                if ev["collides"]:
                    parts.append("collides")
                crit = "; ".join(parts) or "not yet correct"
            lines.append(f"  {h['action_str']} -> {crit}")
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

    def _obs_message(self, env, obs, budget_left):
        """A single turn's user message for history='full' (no re-injected history block -- the
        prior turns are already in the conversation)."""
        if budget_left <= 0:
            note = "\nNo SIMULATE calls left - COMMIT now (your best attempt if none has passed)."
        else:
            note = (f"\nSIMULATE calls remaining: {budget_left}. Keep simulating and refining until "
                    "one returns ALL PASS; do not commit before then.")
        return (f"{obs['text']}{note}\n\nOutput your next action now "
                "(one <think> block and one <act> block).")

    def act(self, ctx):
        env, obs = ctx["env"], ctx["obs"]
        system = self._system_prompt(env)

        if self.history == "full" and not self.oneshot:
            if ctx.get("retry_error"):
                # same turn, correcting an invalid reply: the bad reply is already in the transcript
                self._messages.append(_msg("user",
                    f"Your previous output was invalid: {ctx['retry_error']}. "
                    "Re-emit exactly one <think> and one <act> block with a valid action."))
            else:
                self._messages.append(_msg("user", self._obs_message(env, obs, ctx["budget_left"]),
                                           images=obs.get("images", [])))
            raw = self._generate_messages(system)
            self._messages.append(_msg("model", raw))
            return raw

        # window3 (bounded) and oneshot: stateless single-message call
        step = self._step_prompt(env, obs, ctx["budget_left"])
        if ctx.get("retry_error"):
            step += (f"\n\nYour previous output was invalid: {ctx['retry_error']}. "
                     "Re-emit exactly one <think> and one <act> block with a valid action.")
        raw = self._generate(system, step)
        if self.oneshot:                       # force a single commit, no matter what it emitted
            raw = re.sub(r"\bSIMULATE\b", "COMMIT", raw, flags=re.IGNORECASE)
        return raw

    def _cfg(self):
        from google.genai import types
        cfg = types.GenerateContentConfig(system_instruction=None, temperature=self.temperature,
                                          max_output_tokens=self.max_tokens)
        # thinking ON (dynamic budget) when enabled -- max_output_tokens is set high so the visible
        # <act> is not starved by thinking tokens. Attempted for 2.5 / 3.x / robotics-er; if a model
        # rejects the config, _call drops it and retries.
        if self.thinking and (self.model.startswith(("gemini-2.5", "gemini-3")) or
                              "robotics" in self.model):
            try:
                cfg.thinking_config = types.ThinkingConfig(thinking_budget=-1)
            except Exception:  # noqa: BLE001 - older SDKs without ThinkingConfig
                pass
        return cfg

    def _to_contents(self):
        """Serialize the running transcript to google-genai contents. Full TEXT history is kept;
        actual images are attached only for the last IMAGE_HISTORY_WINDOW user turns (older turns
        keep their text, with a note) so requests stay bounded."""
        from google.genai import types
        user_idxs = [i for i, m in enumerate(self._messages) if m["role"] == "user"]
        keep = set(user_idxs[-self.IMAGE_HISTORY_WINDOW:])
        contents = []
        for i, m in enumerate(self._messages):
            has_imgs = bool(m.get("images"))
            if m["role"] == "user" and has_imgs and i not in keep:
                parts = [types.Part.from_text(text=m["text"] +
                         "\n[earlier rendered views omitted to save space]")]
            else:
                parts = [types.Part.from_text(text=m["text"])]
                if m["role"] == "user" and has_imgs:
                    parts += [types.Part.from_bytes(data=_png_bytes(im), mime_type="image/png")
                              for im in m["images"]]
            contents.append(types.Content(role=("model" if m["role"] == "model" else "user"),
                                          parts=parts))
        return contents

    def _call(self, contents, system, retries=3):
        client = self._client_lazy()
        cfg = self._cfg()
        cfg.system_instruction = system
        last = None
        for i in range(retries):
            try:
                resp = client.models.generate_content(model=self.model, contents=contents, config=cfg)
                txt = resp.text or ""
                if txt.strip():
                    return txt
            except Exception as e:  # noqa: BLE001 - network/quota; back off and retry
                last = e
                # a model that rejects the thinking config -> drop it and retry without thinking
                if getattr(cfg, "thinking_config", None) is not None:
                    cfg.thinking_config = None
                time.sleep(1.5 * (i + 1))
        return f"<think>api error: {last}</think><act>COMMIT NO_FIX()</act>"

    def _generate_messages(self, system):
        return self._call(self._to_contents(), system)

    def _generate(self, system, step, retries=3):
        # single-message (window3 / oneshot) call; on failure returns a parseable fallback.
        return self._call(step, system, retries=retries)
