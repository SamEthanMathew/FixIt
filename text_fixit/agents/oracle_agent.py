#!/usr/bin/env python
"""Oracle: apply the stored exact-inverse repair. The ceiling, and also the end-to-end pipeline test
(parse -> canonical inject -> sequential apply -> multi-part contract must PASS on every instance).

Composite instances carry `gt_fix_sequence` -- the corruption list REVERSED with each spec inverted.
How that sequence is delivered depends on the contract under test:

  batch  one COMMIT carrying the whole ordered list (attempts do not stack, so the list IS the fix)
  stack  one action per turn, SIMULATE-ing each and COMMITting on the last (the working state
         accumulates, so the same sequence arrives incrementally)

If the oracle scores 100% under both contracts, the composed break is provably solvable inside the
agent's parameter-free action space -- no hidden geometry, no privileged parameters.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from action_parser import format_call  # noqa: E402
from agents.base import Agent  # noqa: E402


class OracleAgent(Agent):
    name = "oracle"

    def __init__(self):
        self.step_i = 0

    def reset(self):
        self.step_i = 0

    def _sequence(self, env):
        """[(part_id, spec), ...] in application order, for either instance schema."""
        seq = env.instance.get("gt_fix_sequence")
        if not seq:
            return [(env.target_pid, env.instance["gt_fix"])]
        return [(env.pid_of_link.get(f["link"], env.target_pid), f["spec"]) for f in seq]

    def act(self, ctx):
        env = ctx["env"]
        seq = self._sequence(env)

        if env.action_contract == "batch":
            calls = "; ".join(format_call(spec, pid) for pid, spec in seq)
            body = f"[{calls}]" if len(seq) > 1 else calls
            return (f"<think>apply the exact inverse sequence ({len(seq)} action(s))</think>"
                    f"<act>COMMIT {body}</act>")

        # stack: feed the sequence one action at a time onto the working state
        i = min(self.step_i, len(seq) - 1)
        pid, spec = seq[i]
        last = i >= len(seq) - 1
        self.step_i += 1
        mode = "COMMIT" if last else "SIMULATE"
        return (f"<think>exact inverse, step {i + 1} of {len(seq)}</think>"
                f"<act>{mode} {format_call(spec, pid)}</act>")
