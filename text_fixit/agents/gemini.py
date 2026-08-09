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
import geom  # noqa: E402
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

# How many faults the agent should expect. The hard benchmark says the SAME thing for its composite
# and its single-fault control set -- naming the fault vocabulary without leaking the count or which
# doors -- so the two are prompt-identical and directly comparable.
FAULT_HINT_SINGLE = "Exactly one part may be faulty."
FAULT_HINT_MULTI = ("One or more parts may be faulty, and a faulty part may have more than one "
                    "thing wrong with it - its position, its orientation and its size can all be "
                    "wrong at once.")
# The observation sentence differs by modality only; it is injected INTO the shared contract block
# so the batch/stack prompts differ in nothing else.
SIM_RETURNS = {"text": "SIMULATE returns the resulting part states at the start and end of the "
                       "doors' activation, plus the criteria that failed.",
               "image": "SIMULATE returns new rendered views."}


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

    # Composite instances make the model think much harder: gemini-3.1-pro was observed spending
    # ~15.7k thought tokens on a single turn. With max_output_tokens=8192 the visible <act> was then
    # starved and the call came back empty / MALFORMED_FUNCTION_CALL, so the cap has to clear the
    # thinking budget by a wide margin.
    def __init__(self, oneshot=False, model=None, temperature=0.7, max_tokens=32768,
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
        self._contract_tmpl = {"batch": _load("contract_batch.txt"),
                               "stack": _load("contract_stack.txt")}
        self._client = None
        self._messages = []             # running transcript for history="full"
        # last-call telemetry, drained by run_episode into the turn log (see runlog.py)
        self.last_meta = {}
        self.last_prompt = None
        self.last_raw = None

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
        modality = getattr(env, "state_modality", "text")
        hard = getattr(env, "hard", False)
        contract = getattr(env, "action_contract", "batch")
        tmpl = self._system_img_tmpl if modality == "image" else self._system_tmpl

        # `hard` doubles as "the fixable column is hidden" and "faults may be composite" -- both are
        # properties of the hard benchmark, and gating on it reproduces the legacy prompt exactly.
        fixable_note = ("" if hard else
                        "Only parts marked fixable=yes may be targeted.\n")
        contract_block = self._contract_tmpl[contract].safe_substitute(
            value_grid=VALUE_GRID_STR, angle_grid=ANGLE_GRID_STR, scale_grid=SCALE_GRID_STR,
            K=(0 if self.oneshot else env.budget), fixable_note=fixable_note,
            sim_returns=SIM_RETURNS[modality])

        return tmpl.safe_substitute(
            category=cat, instance_id=env.instance["id"],
            function_text=FUNCTION_TEXT.get(cat, ""), success_text=SUCCESS_TEXT.get(cat, ""),
            part_table=env.table_text, fault_hint=(FAULT_HINT_MULTI if hard else FAULT_HINT_SINGLE),
            tol_pct=f"{geom.TAU_FRAC * 100:.1f}%", contract_block=contract_block,
            value_grid=VALUE_GRID_STR, angle_grid=ANGLE_GRID_STR, scale_grid=SCALE_GRID_STR,
            K=(0 if self.oneshot else env.budget))

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
                "(one <think> block and one <act> block). Write the action as literal TEXT inside "
                "the <act> tags - it is not a tool or function call.")

    def act(self, ctx):
        env, obs = ctx["env"], ctx["obs"]
        system = self._system_prompt(env)

        if self.history == "full" and not self.oneshot:
            if ctx.get("retry_error"):
                # same turn, correcting an invalid reply: the bad reply is already in the transcript
                user = (f"Your previous output was invalid: {ctx['retry_error']}. "
                        "Re-emit exactly one <think> and one <act> block with a valid action.")
                self._messages.append(_msg("user", user))
            else:
                user = self._obs_message(env, obs, ctx["budget_left"])
                self._messages.append(_msg("user", user, images=obs.get("images", [])))
            self.last_prompt = {"system": system, "user": user,
                                "transcript_turns": len(self._messages)}
            raw = self._generate_messages(system)
            self._messages.append(_msg("model", raw))
            self.last_raw = raw
            return raw

        # window3 (bounded) and oneshot: stateless single-message call
        step = self._step_prompt(env, obs, ctx["budget_left"])
        if ctx.get("retry_error"):
            step += (f"\n\nYour previous output was invalid: {ctx['retry_error']}. "
                     "Re-emit exactly one <think> and one <act> block with a valid action.")
        self.last_prompt = {"system": system, "user": step, "transcript_turns": 1}
        raw = self._generate(system, step)
        if self.oneshot:                       # force a single commit, no matter what it emitted
            raw = re.sub(r"\bSIMULATE\b", "COMMIT", raw, flags=re.IGNORECASE)
        self.last_raw = raw
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
        """One model call, with retries. Everything about the call -- latency, token usage, finish
        reason, every failed attempt and its error -- lands in self.last_meta, which run_episode
        drains into turns.jsonl / raw/<id>.jsonl so no API detail is lost."""
        client = self._client_lazy()
        cfg = self._cfg()
        cfg.system_instruction = system
        last = None
        meta = {"model": self.model, "temperature": self.temperature,
                "max_output_tokens": self.max_tokens, "history_mode": self.history,
                "thinking": bool(getattr(cfg, "thinking_config", None)),
                "attempts": [], "errors": [], "usage": None, "finish_reason": None,
                "latency_s": None}
        self.last_meta = meta
        t0 = time.time()
        for i in range(retries):
            a0 = time.time()
            try:
                resp = client.models.generate_content(model=self.model, contents=contents, config=cfg)
                txt = resp.text or ""
                um = getattr(resp, "usage_metadata", None)
                usage = {k: getattr(um, k, None) for k in
                         ("prompt_token_count", "candidates_token_count", "thoughts_token_count",
                          "total_token_count")} if um else None
                fr = None
                try:
                    fr = str(resp.candidates[0].finish_reason)
                except Exception:  # noqa: BLE001 - shape varies by SDK version
                    pass
                meta["attempts"].append({"i": i, "ok": bool(txt.strip()), "usage": usage,
                                         "finish_reason": fr, "seconds": round(time.time() - a0, 2),
                                         "empty": not txt.strip()})
                meta["usage"], meta["finish_reason"] = usage, fr
                if txt.strip():
                    meta["latency_s"] = round(time.time() - t0, 2)
                    return txt
                meta["errors"].append({"i": i, "error": "empty reply", "finish_reason": fr})
            except Exception as e:  # noqa: BLE001 - network/quota; back off and retry
                last = e
                meta["attempts"].append({"i": i, "ok": False, "error": str(e),
                                         "seconds": round(time.time() - a0, 2)})
                meta["errors"].append({"i": i, "error": str(e), "type": type(e).__name__})
                # a model that rejects the thinking config -> drop it and retry without thinking
                if getattr(cfg, "thinking_config", None) is not None:
                    cfg.thinking_config = None
                    meta["thinking"] = False
                time.sleep(1.5 * (i + 1))
        meta["latency_s"] = round(time.time() - t0, 2)
        meta["gave_up"] = True
        return f"<think>api error: {last}</think><act>COMMIT NO_FIX()</act>"

    def _generate_messages(self, system):
        return self._call(self._to_contents(), system)

    def _generate(self, system, step, retries=3):
        # single-message (window3 / oneshot) call; on failure returns a parseable fallback.
        return self._call(step, system, retries=retries)
