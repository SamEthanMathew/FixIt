#!/usr/bin/env python
"""Random baseline: sample a legal (part, transform, axis, on-grid value) each turn and SIMULATE;
run_episode auto-commits the best simulated fix at budget. Establishes the task floor."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grids  # noqa: E402
from agents.base import Agent  # noqa: E402


class RandomAgent(Agent):
    name = "random"

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def act(self, ctx):
        env = ctx["env"]
        fixable = [pid for pid, pt in env.id_map.items() if pt["corruptible"]]
        pid = self.rng.choice(fixable)
        axis = self.rng.choice(["X", "Y", "Z"])
        ctype = self.rng.choice(["translate", "rotate", "scale"])
        if ctype == "translate":
            v = self.rng.choice(grids.VALUE_GRID) * self.rng.choice([-1, 1])
            op = f"TRANSLATE({pid}, {axis}, {v:.4f})"
        elif ctype == "rotate":
            v = self.rng.choice(grids.ANGLE_GRID) * self.rng.choice([-1, 1])
            op = f"ROTATE({pid}, {axis}, {v:.1f})"
        else:
            v = self.rng.choice(grids.SCALE_GRID)
            op = f"SCALE({pid}, {axis}, {v:.4f})"
        mode = "COMMIT" if ctx["budget_left"] <= 0 else "SIMULATE"
        return f"<think>random probe</think><act>{mode} {op}</act>"
