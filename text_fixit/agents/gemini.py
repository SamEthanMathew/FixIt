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


def _magnitude_strings(instance):
    """Human-readable fault magnitude ranges for the $..._range slots in the ablated prompt.

    Read from the INSTANCE (instances_hard.py records `magnitude_ranges` per set), falling back to
    corruption.py's defaults. This must not be hardcoded: a set generated with --difficulty-scale
    has much smaller faults, and a prompt quoting the default ranges would push the model toward
    magnitudes several times too large -- worse than saying nothing at all.
    """
    import corruption as _corr
    r = instance.get("magnitude_ranges") or {}
    tr = r.get("translate", _corr.TRANSLATE_RANGE)
    ro = r.get("rotate_deg", _corr.ROTATE_RANGE_DEG)
    sc = r.get("scale", _corr.SCALE_RANGE)
    return {"translate_range": f"{tr[0]:.3f}-{tr[1]:.3f} m",
            "rotate_range": f"{ro[0]:.0f}-{ro[1]:.0f} degrees",
            "scale_range": f"{sc[0]:.2f}-{sc[1]:.2f}"}


BASE_PROMPT_SET = "one_error_search"   # fallback for any file an ablation set does not override
# The superseded one_error / one_error_dev / one_error_scale / one_error_strict sets moved to
# prompts/old_prompts/old_one_error_prompts/. one_error_search is self-contained (all four
# roles present), so it is both the active set and a valid fallback base.


def _load_set(prompt_set, role):
    """Load `<prompt_set>_<role>.txt`, falling back to the base set for files an ablation omits."""
    name = f"{prompt_set}_{role}.txt"
    if not os.path.isfile(os.path.join(_PROMPT_DIR, name)):
        name = f"{BASE_PROMPT_SET}_{role}.txt"
    return _load(name)


def _load(name):
    """Load a prompt template, honouring the FIXIT_PROMPT_VARIANT ablation switch.

    With FIXIT_PROMPT_VARIANT=ablate, `system.txt` resolves to `system_ablate.txt` IF that file
    exists, else falls back to the base file. This keeps an ablation from silently half-applying:
    every template that has a variant swaps, every one that does not stays byte-identical to the
    runs it is being compared against. The variant used is recorded in the run manifest.
    """
    variant = os.environ.get("FIXIT_PROMPT_VARIANT", "").strip()
    if variant:
        stem, ext = os.path.splitext(name)
        alt = os.path.join(_PROMPT_DIR, f"{stem}_{variant}{ext}")
        if os.path.isfile(alt):
            name = os.path.basename(alt)
    path = os.path.join(_PROMPT_DIR, name)
    if not os.path.isfile(path):
        # The previous generation was moved to prompts/old_prompts/ pending standardized
        # replacements. Fail with the requirement, not a bare path: a missing template is a
        # setup error, and the caller needs to know WHICH file and where the old one went.
        old = os.path.join(_PROMPT_DIR, "old_prompts", name)
        hint = (f" A previous version exists at {old} — copy or adapt it."
                if os.path.isfile(old) else "")
        raise FileNotFoundError(
            f"prompt template {name!r} not found in {_PROMPT_DIR}.{hint} "
            f"See prompts/README.md for the five required files and their variables.")
    with open(path) as f:
        return Template(f.read())


def _passing_action(env):
    """The action string of the first SIMULATE that returned ALL PASS, or None."""
    for h in env.history or []:
        if h.get("mode") == "SIMULATE" and h.get("eval") and h["eval"].get("PASS"):
            return h.get("action_str")
    return None


def _found_note(env):
    """Unmissable instruction once a passing repair exists.

    env.auto_commit_best() only fires when a SIMULATE is attempted with no budget left; an explicit
    COMMIT of a worse action is taken at face value. So a found pass has to be surfaced, loudly."""
    won = _passing_action(env)
    if not won:
        return ""
    # Hand over BOTH lines, tags included. An earlier version showed only the <act> line and said
    # "emit exactly this"; the model supplied a <think> sentence from elsewhere in the prompt and
    # emitted it as bare prose with no tags at all -- 10 parse failures in one run.
    return (f"\n*** ALL PASS ALREADY ACHIEVED with {won} ***\n"
            f"The search is finished. Your entire reply must be exactly these two lines, tags "
            f"included, and nothing else:\n"
            f"<think>A SIMULATE reported ALL PASS, so this is the repair.</think>\n"
            f"<act>COMMIT {won}</act>\n"
            f"Do not probe anything further. Any other action throws away a solved episode.\n")


def _healthy_by_probe(env):
    """Parts the SIMULATOR has already proven healthy, deduced from the run's own history.

    Exactly one part is faulty, and the reported error is the WORST part's error. So if two or more
    probes that moved part P left that number bit-identical, P is not the worst part and cannot be
    the faulty one. Qwen will not draw this inference itself -- in pilots it spent 5 of 11 probes on
    a part whose error had already read the same value five times -- so the harness draws it and
    narrows the candidate list. This deduces from observed outputs only; it never consults the
    ground truth."""
    import re as _re
    from collections import defaultdict
    seen = defaultdict(list)
    for h in env.history:
        if h.get("mode") != "SIMULATE" or not h.get("eval"):
            continue
        pids = set(_re.findall(r"\((P\d+),", h.get("action_str") or ""))
        if len(pids) != 1:
            continue                      # a multi-part action attributes nothing
        seen[pids.pop()].append(round(float(h["eval"]["deviation_mm"]), 4))
    base = round(float(env.reset_eval["deviation_mm"]), 4) if getattr(env, "reset_eval", None) else None
    ruled = set()
    for pid, devs in seen.items():
        if len(devs) >= 2 and len(set(devs)) == 1 and (base is None or devs[0] == base):
            ruled.add(pid)
    return ruled


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
                 history="window3", thinking=True, thinking_budget=None):
        assert history in ("window3", "full")
        self.oneshot = oneshot
        self.history = history           # "window3": stateless call w/ last-3 summary each turn
        #                                  "full":    one accumulating conversation per object
        self.thinking = thinking
        # None => dynamic (-1), the baseline setting. An integer CAPS per-turn thinking, and when it
        # is capped the model is TOLD its budget in the system prompt ($thinking_note): a model that
        # does not know it is on a budget will happily spend the whole allowance reasoning and get
        # cut off before it emits <act>, which scores as an invalid turn rather than a wrong answer.
        env_tb = os.environ.get("FIXIT_THINKING_BUDGET")
        if thinking_budget is None and env_tb:
            thinking_budget = int(env_tb)
        self.thinking_budget = thinking_budget
        if oneshot:
            self.name = "oneshot_gemini"
        else:
            self.name = "loop_gemini" if history == "window3" else "loop_gemini_full"
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature
        self.max_tokens = max_tokens     # high: with thinking ON the thinking tokens count here
        # A prompt SET is a family of files sharing a prefix: <set>_text.txt, <set>_image.txt,
        # <set>_step.txt. Every ablation is its own set, so a run's prompt is identified by one
        # name in the manifest rather than reconstructed from flags. Files the ablation does not
        # change fall back to BASE_PROMPT_SET, so an ablation ships only what it actually alters.
        self.prompt_set = os.environ.get("FIXIT_PROMPT_SET", BASE_PROMPT_SET)
        self._system_tmpl = _load_set(self.prompt_set, "text")
        self._system_img_tmpl = _load_set(self.prompt_set, "image")
        self._step_tmpl = _load_set(self.prompt_set, "step")
        # history="full" builds its own per-turn message; templating it keeps the WHOLE prompt in
        # the prompt set instead of half of it living in Python.
        self._obs_tmpl = _load_set(self.prompt_set, "obs")
        # The one_error sets are self-contained: no $contract_block, one action per turn.
        self._contract_tmpl = None
        if os.path.isfile(os.path.join(_PROMPT_DIR, "contract_batch.txt")):
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

        # These two are independent switches on the env (see FridgeRepairEnv.__init__); `hard` is
        # only their default, so a run can reveal the fixable column while keeping the composite
        # fault hint, or vice versa.
        reveal_fixable = getattr(env, "reveal_fixable", not hard)
        multi_hint = getattr(env, "multi_fault_hint", hard)
        fixable_note = ("Only parts marked fixable=yes may be targeted.\n" if reveal_fixable
                        else "")
        contract_block = "" if self._contract_tmpl is None else self._contract_tmpl[contract].safe_substitute(
            value_grid=VALUE_GRID_STR, angle_grid=ANGLE_GRID_STR, scale_grid=SCALE_GRID_STR,
            K=(0 if self.oneshot else env.budget), fixable_note=fixable_note,
            sim_returns=SIM_RETURNS[modality])

        return tmpl.safe_substitute(
            category=cat, instance_id=env.instance["id"],
            function_text=FUNCTION_TEXT.get(cat, ""), success_text=SUCCESS_TEXT.get(cat, ""),
            part_table=env.table_text,
            fault_hint=(FAULT_HINT_MULTI if multi_hint else FAULT_HINT_SINGLE),
            tol_pct=f"{geom.TAU_FRAC * 100:.1f}%", contract_block=contract_block,
            # The set's real generation margin, so the prompt never misstates how broken the
            # instance is. Defaults to 3 -> renders byte-identical to every pre-M8 run.
            margin_x=f"{env.instance.get('broken_margin', 3.0):g}",
            # self-contained sets reference $fixable_note directly; it used to live only in the
            # contract block, so omitting it here shipped the literal "$fixable_note" to the model.
            fixable_note=fixable_note, targetable=self._targetable(env),
            legal_pid=self._legal_pid(env),
            axis_legend=(getattr(env, 'axis_legend', None) or ''),
            untried=self._untried(env), found_note=self._found_note(env),
            deviation_note=self._deviation_note(env),
            **_magnitude_strings(env.instance),
            thinking_note=self._thinking_note(),
            value_grid=VALUE_GRID_STR, angle_grid=ANGLE_GRID_STR, scale_grid=SCALE_GRID_STR,
            K=(0 if self.oneshot else env.budget))

    # A search agent needs its FULL experiment log, not a sliding window. With the last-3 window,
    # Qwen probed the same non-faulty part eight times and read the identical error every time --
    # the flat response that identifies a wrong part -- but could never see the pattern, and re-ran
    # two probes verbatim. HISTORY_TURNS caps it only to bound the prompt.
    HISTORY_TURNS = 3

    def _history_text(self, env):
        hist = [h for h in env.history if h["mode"] == "SIMULATE"][-self.HISTORY_TURNS:]
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

    @staticmethod
    def _found_note(env):
        return _found_note(env)

    @staticmethod
    def _untried(env):
        """(operation, axis) pairs not yet probed, as literal text.

        Qwen3-VL-8B cannot enumerate a search space on its own: across pilots it emitted axis Z zero
        times in 11 probes even with Z in the worked examples, and silently dropped whole operations.
        The harness already knows every probe run, so it lists what remains instead of relying on the
        model to notice the gap. This is bookkeeping, not the answer -- which pair is correct is
        still the model's to find."""
        import re as _re
        # A passing repair ends the search. Listing untried combinations after that actively invites
        # the model to keep sweeping -- in the text run it found ALL PASS at turn 4, swept five more
        # combinations, then committed the last (failing) one.
        won = _passing_action(env)
        if won:
            return f"(none - a PASSING repair has already been found: {won}. Commit it.)"
        done = {}
        for h in env.history:
            if h.get("mode") != "SIMULATE":
                continue
            for m in _re.finditer(r"(TRANSLATE|ROTATE|SCALE)\((P\d+),\s*([XYZ])", h.get("action_str") or ""):
                done.setdefault(m.group(2), set()).add((m.group(1), m.group(3)))
        # Per PART: probing ROTATE/Z on a healthy part says nothing about the faulty one, so a
        # global set silently marked the correct answer as already-tried and it was never probed.
        out = []
        for pid, pt in env.id_map.items():
            if not pt.get("corruptible"):
                continue
            seen = done.get(pid, set())
            left = [f"{op}/{ax}" for op in ("TRANSLATE", "ROTATE", "SCALE") for ax in "XYZ"
                    if (op, ax) not in seen]
            out.append(f"{pid}: " + (", ".join(left) if left else "all nine probed"))
        return " | ".join(out) if out else "(none)"

    @staticmethod
    def _targetable(env):
        """The part ids an action may legally name, as literal text ("P1, P2").

        history="window3" is a STATELESS call, so the annotated part view -- which ships only in the
        first message -- is never seen again, and the fixable column of the table has to carry the
        whole job. Qwen3-VL-8B then defaults to "P0" regardless: on the two std30 pilots where P0 is
        the body it spent 27 turns targeting it. Naming the legal ids costs a few tokens and removes
        the guess."""
        ids = [pid for pid, pt in env.id_map.items() if pt.get("corruptible")]
        ruled = _healthy_by_probe(env)
        live = [p for p in ids if p not in ruled] or ids
        # Exactly one fault: once every other candidate is ruled out, the faulty part is DETERMINED,
        # not merely likely. Saying so removes the choice. Qwen otherwise keeps re-selecting a part
        # its own probes disproved -- 67 of 69 first-attempt parse failures in the text run were
        # exactly this, each costing a retry call.
        if ruled and len(live) == 1:
            return (f"{live[0]}  <-- CONFIRMED FAULTY. Probing ruled out "
                    f"{', '.join(sorted(ruled))}: moving them left the error unchanged, and only one "
                    f"part is faulty. Every remaining action MUST target {live[0]}.")
        if ruled and len(live) < len(ids):
            return (", ".join(live) +
                    f"  (ruled out by probe, do not target again: {', '.join(sorted(ruled))})")
        return ", ".join(live) if live else "(none)"

    @staticmethod
    def _deviation_note(env):
        """The 'observations report the error in mm' sentence -- ONLY when they actually do.

        env.show_deviation gates that line in env._render. The strict prompt inherited the claim
        from the dev ablation and asserted it unconditionally, so on a show_deviation=False run it
        promised a number that appeared in 87 of 320 prompts, and told the model to do arithmetic
        on two values it was never given."""
        if not getattr(env, "show_deviation", False):
            return ""
        return ("Each observation also reports how far the worst faulty part still is from correct, "
                "in millimetres, together with the tolerance it has to get under.\n"
                "USE THAT NUMBER. If value V took the error from A down to B, then V closed (A - B) "
                "of the gap, so the value that closes all of A is about V * A / (A - B).\n")

    @staticmethod
    def _legal_pid(env):
        """A part id that is actually targetable on THIS instance, for the worked example.

        The example cannot hardcode P0: on instances where P0 is the body, showing
        `TRANSLATE(P0, ...)` teaches exactly the illegal action the model already defaults to."""
        for pid, pt in env.id_map.items():
            if pt.get("corruptible"):
                return pid
        return "P1"

    def _step_prompt(self, env, obs, budget_left):
        if self.oneshot:
            note = " -- you get NO simulations; output a single COMMIT action now"
        elif budget_left <= 0:
            note = " -- budget exhausted, you MUST COMMIT now"
        else:
            note = ""
        return self._step_tmpl.safe_substitute(
            observation=obs["text"], budget_left=(0 if self.oneshot else budget_left),
            commit_note=note, history=self._history_text(env),
            targetable=self._targetable(env), legal_pid=self._legal_pid(env),
            untried=self._untried(env), found_note=self._found_note(env))

    def _obs_message(self, env, obs, budget_left):
        """A single turn's user message for history='full' (no re-injected history block -- the
        prior turns are already in the conversation)."""
        if budget_left <= 0:
            note = "No SIMULATE calls left - COMMIT now (your best attempt if none has passed)."
        else:
            note = (f"SIMULATE calls remaining: {budget_left}. Keep simulating and refining until "
                    "one returns ALL PASS; do not commit before then.")
        return self._obs_tmpl.safe_substitute(observation=obs["text"], commit_note=note)

    # The retry is the one moment we KNOW the model just got the format wrong, so it is the highest
    # -leverage place to show the format rather than name it. Naming it ("with a valid action") left
    # Qwen3-VL-8B dropping the SIMULATE keyword on 21 of 33 retries; the corrected shape is spelled
    # out literally instead.
    _RETRY_HINT = ("Your previous output was invalid: {err}.\n"
                   "Re-emit exactly one <think> block and one <act> block, in this shape:\n"
                   "  <think>one sentence</think>\n"
                   "  <act>SIMULATE TRANSLATE(P0, X, -0.06)</act>\n"
                   "The word SIMULATE (or COMMIT) is literal and must be the first word inside "
                   "<act>; only the call after it changes.")

    def act(self, ctx):
        env, obs = ctx["env"], ctx["obs"]
        system = self._system_prompt(env)

        if self.history == "full" and not self.oneshot:
            if ctx.get("retry_error"):
                # same turn, correcting an invalid reply: the bad reply is already in the transcript
                user = self._RETRY_HINT.format(err=ctx["retry_error"])
                self._messages.append(_msg("user", user))
            else:
                user = self._obs_message(env, obs, ctx["budget_left"])
                self._messages.append(_msg("user", user, images=obs.get("images", [])))
            self.last_prompt = {"system": system, "user": user,
                                "transcript_turns": len(self._messages)}
            raw = self._generate_messages(system)
            if isinstance(self.last_meta, dict):
                self.last_meta["images_sent"] = getattr(self, "_images_attached", None)
            self._messages.append(_msg("model", raw))
            self.last_raw = raw
            return raw

        # window3 (bounded) and oneshot: stateless single-message call
        step = self._step_prompt(env, obs, ctx["budget_left"])
        if ctx.get("retry_error"):
            step += "\n\n" + self._RETRY_HINT.format(err=ctx["retry_error"])
        imgs = list(obs.get("images", []))
        self.last_prompt = {"system": system, "user": step, "transcript_turns": 1,
                            "n_images": len(imgs)}
        raw = self._generate(system, step, images=imgs)
        # What the MODEL received, as distinct from what the environment rendered. run_episode
        # logs the latter (image_paths); without this there is no evidence the two agree.
        if isinstance(self.last_meta, dict):
            self.last_meta["images_sent"] = len(imgs)
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
                cfg.thinking_config = types.ThinkingConfig(
                    thinking_budget=(-1 if self.thinking_budget is None else self.thinking_budget))
            except Exception:  # noqa: BLE001 - older SDKs without ThinkingConfig
                pass
        return cfg

    def _thinking_note(self):
        """Told to the model whenever thinking is CAPPED, so it can ration its reasoning instead of
        being truncated mid-thought and losing the <act> block entirely."""
        if self.thinking_budget is None or not self.thinking:
            return ""
        return (f"REASONING BUDGET\n"
                f"You have a thinking budget of {self.thinking_budget} tokens per turn, out of "
                f"{self.max_tokens} total output tokens. Reason concisely enough to fit inside it: "
                f"if you exhaust the budget before emitting your <act> block, the turn is wasted "
                f"and counts as an invalid action. When the problem needs more thought than the "
                f"budget allows, spend a SIMULATE call to test a partial hypothesis rather than "
                f"trying to solve it all in one turn.\n")

    def _to_contents(self):
        """Serialize the running transcript to google-genai contents. Full TEXT history is kept;
        actual images are attached only for the last IMAGE_HISTORY_WINDOW user turns (older turns
        keep their text, with a note) so requests stay bounded."""
        from google.genai import types
        user_idxs = [i for i, m in enumerate(self._messages) if m["role"] == "user"]
        keep = set(user_idxs[-self.IMAGE_HISTORY_WINDOW:])
        # Count what is ACTUALLY attached: older turns keep their text but lose their images, so
        # this is not len(obs["images"]). Reported as images_sent_to_model.
        self._images_attached = sum(len(self._messages[i].get("images") or []) for i in keep)
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

    def _call(self, contents, system, retries=5):
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
                time.sleep(min(60.0, 2.0 * (2 ** i)))     # exponential backoff for 429s/5xx
        meta["latency_s"] = round(time.time() - t0, 2)
        meta["gave_up"] = True
        return f"<think>api error: {last}</think><act>COMMIT NO_FIX()</act>"

    def _generate_messages(self, system):
        return self._call(self._to_contents(), system)

    def _single_turn(self, text, images):
        """One stateless user turn WITH its images attached.

        The window3 and oneshot paths used to pass the step text alone, so in image modality the
        model was told "(attached: the ORIGINAL BROKEN object ... )" and received no pixels at all.
        Every image-modality run on those paths was effectively blind. Returns provider-native
        content; a bare string when there is nothing to attach, so the text path is unchanged.
        """
        if not images:
            return text
        from google.genai import types
        return ([types.Part.from_text(text=text)] +
                [types.Part.from_bytes(data=_png_bytes(im), mime_type="image/png")
                 for im in images])

    def _generate(self, system, step, images=None, retries=3):
        # single-message (window3 / oneshot) call; on failure returns a parseable fallback.
        return self._call(self._single_turn(step, images), system, retries=retries)
