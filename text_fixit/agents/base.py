#!/usr/bin/env python
"""Agent interface. act(ctx) returns the raw TAGGED text for ONE turn; run_episode parses it
uniformly for every agent (scripted or LLM), so there is a single action pathway.

ctx keys: env, obs (last observation dict), step (int), budget_left (int),
          system_prompt, step_prompt (str, for LLM agents), retry_error (str|None)."""


class Agent:
    name = "base"

    def reset(self):
        pass

    def act(self, ctx):
        raise NotImplementedError
