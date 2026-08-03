#!/usr/bin/env python
"""Oracle: commit the stored exact-inverse gt_fix immediately. Ceiling that also validates the
whole pipeline (parse -> canonical inject -> apply -> contract must PASS on every instance)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from action_parser import format_action  # noqa: E402
from agents.base import Agent  # noqa: E402


class OracleAgent(Agent):
    name = "oracle"

    def act(self, ctx):
        env = ctx["env"]
        return "<think>apply the exact inverse</think>" + \
            format_action(env.instance["gt_fix"], env.target_pid, mode="COMMIT")
