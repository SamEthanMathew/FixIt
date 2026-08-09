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
    def __init__(self, oneshot=False, model=None, temperature=0.7, max_tokens=1536,
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
        (window3 / oneshot), matching how GeminiAgent's two _generate paths call in."""
        requests = self._client_lazy()
        messages = [{"role": "system", "content": system}]
        messages += contents if isinstance(contents, list) \
            else [{"role": "user", "content": contents}]
        payload = {"model": self.model, "messages": messages,
                   "temperature": self.temperature, "max_tokens": self.max_tokens}
        last = None
        for i in range(retries):
            try:
                r = requests.post(f"{self.base_url}/chat/completions", json=payload,
                                  timeout=self.timeout)
                r.raise_for_status()
                txt = (r.json()["choices"][0]["message"]["content"] or "")
                if txt.strip():
                    return _normalize(txt)
                last = "empty completion"
            except Exception as e:  # noqa: BLE001 - server not up / OOM / timeout; back off and retry
                last = e
                time.sleep(1.5 * (i + 1))
        # Same parseable fallback as GeminiAgent so a dead server scores as a failed episode
        # rather than crashing the sweep.
        return f"<think>server error: {last}</think><act>COMMIT NO_FIX()</act>"
