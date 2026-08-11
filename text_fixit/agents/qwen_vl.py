#!/usr/bin/env python
"""
Local Qwen3-VL agent (open-weight counterpart to the Gemini ceiling).

Only the TRANSPORT differs from GeminiAgent: the provider-agnostic half -- system/step template
filling, window3 vs full history, the image-history window, the oneshot COMMIT rewrite -- is
inherited unchanged, so a loop_qwen run is prompt-identical to loop_gemini and the two are directly
comparable. (If a third backend lands, lift that half of GeminiAgent into a shared base.)

Talks to a vLLM OpenAI-compatible server rather than importing transformers in-process: this env
pins torch 2.5.1+cu121 for the compiled point-cloud ops, while Qwen3-VL needs transformers>=4.57.
Start the server first:  bash text_fixit/serve_qwen.sh

Endpoint via env QWEN_BASE_URL (default http://127.0.0.1:8001/v1 -- 8000 is taken by another
user's service on this box), model via QWEN_MODEL (default Qwen/Qwen3-VL-8B-Instruct). No API key
is used or needed.
"""
import base64
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.gemini import GeminiAgent, _png_bytes  # noqa: E402

DEFAULT_BASE_URL = "http://127.0.0.1:8001/v1"
DEFAULT_MODEL = "Qwen/Qwen3-VL-8B-Instruct"


def _data_url(pil):
    return "data:image/png;base64," + base64.b64encode(_png_bytes(pil)).decode("ascii")


_ACT_RE = re.compile(r"<act>", re.IGNORECASE)
_THINK_TAG_RE = re.compile(r"</?think>", re.IGNORECASE)
_TOOLCALL_RE = re.compile(r"</?tool_call>", re.IGNORECASE)


def _normalize(raw):
    """Rewrite one Qwen turn into the canonical <think>..</think>[<backtrack/>]<act>..</act> shape.

    Qwen3-VL-Instruct reliably emits <act>...</act> -- action_parser only needs that, so actions
    already work -- but it is loose about the rest: it usually drops the opening <think> and writes
    bare prose, sometimes closes a </think> it never opened, and intermittently emits a stray
    <tool_call> marker (a Qwen3 chat-template artifact; we pass no tools). Left alone the reasoning
    logs as "" and the <backtrack/> marker the trace-SFT stage in Fixit_RL depends on is invisible.

    Rebuilding unconditionally -- rather than only when <think> is absent -- is what makes this
    idempotent: a well-formed turn round-trips unchanged, and a half-tagged one can't be
    double-wrapped."""
    raw = _TOOLCALL_RE.sub("", raw)
    m = _ACT_RE.search(raw)
    if not m:
        return raw                                    # no action to anchor on; let the parser reject
    head, tail = raw[:m.start()], raw[m.start():]
    # <backtrack/> is a sibling of <think>, not part of the reasoning -- lift it out first.
    bt = "<backtrack/>" if "<backtrack/>" in head else ""
    head = _THINK_TAG_RE.sub("", head.replace("<backtrack/>", "")).strip()
    return f"<think>{head}</think>{bt}{tail}"


class QwenVLAgent(GeminiAgent):
    # 4096, not the original 1536: Qwen3-VL-Instruct has no separate thinking channel, so the
    # <think> block the prompt asks for competes for the SAME output budget as the <act> line. On a
    # multi-fault instance 1536 is a plausible truncation point, and a truncated turn scores as an
    # INVALID ACTION -- i.e. as a model failure when it is really a harness cap (the same trap M4
    # hit with Gemini at max_output_tokens=8192). Not raised further because the server runs at
    # --max-model-len 32768 TOTAL: with image observations and history="full" the prompt grows for
    # ten turns, and output tokens have to leave room for it.
    def __init__(self, oneshot=False, model=None, temperature=0.7, max_tokens=4096,
                 history="window3", base_url=None, timeout=180):
        # thinking=False: Qwen3-VL-Instruct has no separate thinking channel; the <think> block the
        # prompt asks for is ordinary output text.
        super().__init__(oneshot=oneshot, model=model or os.environ.get("QWEN_MODEL", DEFAULT_MODEL),
                         temperature=temperature, max_tokens=max_tokens, history=history,
                         thinking=False)
        self.base_url = (base_url or os.environ.get("QWEN_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout
        if oneshot:
            self.name = "oneshot_qwen"
        else:
            self.name = "loop_qwen" if history == "window3" else "loop_qwen_full"

    # ------------------------------------------------------------------ transport
    def _client_lazy(self):
        # No SDK client: a plain HTTP endpoint. requests is already a dependency of this env.
        import requests
        return requests

    def _to_contents(self):
        """Running transcript -> OpenAI chat messages. Mirrors GeminiAgent._to_contents: full TEXT
        history is kept, but actual images ride only on the last IMAGE_HISTORY_WINDOW user turns so
        the request stays bounded."""
        user_idxs = [i for i, m in enumerate(self._messages) if m["role"] == "user"]
        keep = set(user_idxs[-self.IMAGE_HISTORY_WINDOW:])
        out = []
        for i, m in enumerate(self._messages):
            role = "assistant" if m["role"] == "model" else "user"
            imgs = m.get("images") or []
            if role == "user" and imgs and i not in keep:
                out.append({"role": role,
                            "content": m["text"] + "\n[earlier rendered views omitted to save space]"})
            elif role == "user" and imgs:
                parts = [{"type": "text", "text": m["text"]}]
                parts += [{"type": "image_url", "image_url": {"url": _data_url(im)}} for im in imgs]
                out.append({"role": role, "content": parts})
            else:
                out.append({"role": role, "content": m["text"]})
        return out

    def _call(self, contents, system, retries=3):
        """contents is either the OpenAI message list (history='full') or a single step string
        (window3 / oneshot), matching how GeminiAgent's two _generate paths call in.

        Populates self.last_meta exactly as GeminiAgent._call does. This is not bookkeeping polish:
        run_episode reads `last_meta["gave_up"]` to count API give-ups, and drains latency / usage /
        finish_reason into turns.jsonl and raw/<id>.jsonl. Without it the fallback below --
        `COMMIT NO_FIX()` -- is INDISTINGUISHABLE from the model genuinely giving up, so a dead or
        OOM'd vLLM server would score a whole condition as a legitimate 0% instead of as broken
        infrastructure.
        """
        requests = self._client_lazy()
        messages = [{"role": "system", "content": system}]
        messages += contents if isinstance(contents, list) \
            else [{"role": "user", "content": contents}]
        payload = {"model": self.model, "messages": messages,
                   "temperature": self.temperature, "max_tokens": self.max_tokens}
        last = None
        meta = {"model": self.model, "temperature": self.temperature,
                "max_output_tokens": self.max_tokens, "history_mode": self.history,
                "base_url": self.base_url, "thinking": False,
                "attempts": [], "errors": [], "usage": None, "finish_reason": None,
                "latency_s": None}
        self.last_meta = meta
        t0 = time.time()
        for i in range(retries):
            a0 = time.time()
            try:
                r = requests.post(f"{self.base_url}/chat/completions", json=payload,
                                  timeout=self.timeout)
                r.raise_for_status()
                body = r.json()
                choice = body["choices"][0]
                txt = (choice["message"]["content"] or "")
                um = body.get("usage") or None
                usage = {k: um.get(k) for k in
                         ("prompt_tokens", "completion_tokens", "total_tokens")} if um else None
                fr = choice.get("finish_reason")
                meta["attempts"].append({"i": i, "ok": bool(txt.strip()), "usage": usage,
                                        "finish_reason": fr, "seconds": round(time.time() - a0, 2),
                                        "empty": not txt.strip()})
                meta["usage"], meta["finish_reason"] = usage, fr
                if txt.strip():
                    # "length" means the reply was cut off mid-emission -- the <act> block may be
                    # missing, which the parser will report as an invalid action. Record it so a
                    # truncation is never silently read as a model mistake (see max_tokens above).
                    if fr == "length":
                        meta["errors"].append({"i": i, "error": "truncated at max_tokens",
                                               "finish_reason": fr})
                        meta["truncated"] = True
                    meta["latency_s"] = round(time.time() - t0, 2)
                    return _normalize(txt)
                last = "empty completion"
                meta["errors"].append({"i": i, "error": "empty completion", "finish_reason": fr})
            except Exception as e:  # noqa: BLE001 - server not up / OOM / timeout; back off and retry
                last = e
                meta["attempts"].append({"i": i, "ok": False, "error": str(e),
                                        "seconds": round(time.time() - a0, 2)})
                meta["errors"].append({"i": i, "error": str(e), "type": type(e).__name__})
                time.sleep(1.5 * (i + 1))
        # Same parseable fallback as GeminiAgent so a dead server scores as a failed episode
        # rather than crashing the sweep -- but flagged, so it is counted as an infrastructure
        # failure (record["n_api_giveup"]) and not as the model choosing NO_FIX.
        meta["latency_s"] = round(time.time() - t0, 2)
        meta["gave_up"] = True
        return f"<think>server error: {last}</think><act>COMMIT NO_FIX()</act>"
