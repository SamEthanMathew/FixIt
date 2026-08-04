#!/usr/bin/env python
"""
Drive one agent through one instance and log the trajectory.

Loop (matches MILESTONE_1 sec.8):
  reset -> repeat [ agent.act -> parse (1 reparse retry on malformed) -> env.step ] until COMMIT
  or the SIMULATE budget is exhausted, then auto-commit the best simulated fix.

Per-episode record captures everything evaluate.py needs for the metrics.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import action_parser  # noqa: E402
from env import FridgeRepairEnv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def run_episode(env, agent, instance, prompts=None, verbose=False):
    obs = env.reset(instance)
    agent.reset()
    prompts = prompts or {}
    oneshot = getattr(agent, "oneshot", False)
    turns = 0
    max_turns = 1 if oneshot else env.budget + 5   # one-shot = a single commit decision
    seen_sims = set()
    repeated = 0
    first_sim_score = None

    while not env.terminal and turns < max_turns:
        budget_left = env.budget - env.sim_count
        ctx = {"env": env, "obs": obs, "step": turns, "budget_left": budget_left,
               "system_prompt": prompts.get("system"), "step_prompt": prompts.get("step"),
               "history": env.history, "retry_error": None}
        raw = agent.act(ctx)
        parsed = action_parser.parse(raw, env.id_map)
        if not parsed["valid"]:
            ctx["retry_error"] = parsed["error"]          # 1 reparse retry, error echoed
            raw = agent.act(ctx)
            parsed = action_parser.parse(raw, env.id_map)

        # A SIMULATE with no budget left -> auto-commit the best simulated fix.
        if parsed["valid"] and parsed["mode"] == "SIMULATE" and budget_left <= 0:
            obs, _ = env.auto_commit_best()
            break

        obs, terminal, info = env.step(parsed)
        turns += 1

        # bookkeeping on accepted SIMULATE steps
        if parsed["valid"] and parsed["mode"] == "SIMULATE" and not obs.get("invalid"):
            astr = env.history[-1]["action_str"]
            if first_sim_score is None:
                first_sim_score = env.history[-1]["eval"]["score"]
            if astr in seen_sims:
                repeated += 1
            seen_sims.add(astr)
        if verbose:
            print(f"[turn {turns}] {raw.strip()[:80]}")

    if not env.terminal:                                  # ran out of turns (e.g. invalid storm)
        obs, _ = env.auto_commit_best()

    terminal = env.history[-1]
    ev = terminal["eval"]
    committed = terminal["mode"] in ("COMMIT",)
    return {
        "id": instance["id"],
        "base": instance["base"],
        "agent": agent.name,
        "state_modality": env.state_modality,
        "show_deviation": env.show_deviation,
        "corruption_type": instance["corruption"]["type"],
        "terminal_pass": bool(ev["PASS"]),
        "terminal_score": float(ev["score"]),
        "terminal_deviation_mm": float(ev["deviation_mm"]),
        "terminal_mode": terminal["mode"],
        "committed": committed,
        "n_simulate": env.sim_count,
        "n_invalid": env.invalid_count,
        "n_repeated": repeated,
        "first_sim_score": first_sim_score,
        "first_sim_pass": (first_sim_score is not None and first_sim_score >= 0.80),
        "history": [{"mode": h["mode"], "action": h["action_str"],
                     "pass": bool(h["eval"]["PASS"]), "score": round(h["eval"]["score"], 4),
                     "deviation_mm": round(h["eval"]["deviation_mm"], 1)} for h in env.history],
    }


def _make_agent(name, seed=0):
    if name == "random":
        from agents.random_agent import RandomAgent
        return RandomAgent(seed=seed)
    if name == "oracle":
        from agents.oracle_agent import OracleAgent
        return OracleAgent()
    if name in ("gemini", "loop_gemini"):
        from agents.gemini import GeminiAgent
        return GeminiAgent(oneshot=False, history="window3")
    if name == "loop_gemini_full":
        from agents.gemini import GeminiAgent
        return GeminiAgent(oneshot=False, history="full")
    if name in ("oneshot_gemini", "oneshot"):
        from agents.gemini import GeminiAgent
        return GeminiAgent(oneshot=True)
    raise ValueError(f"unknown agent {name!r}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="oracle")
    ap.add_argument("--split", default="test")
    ap.add_argument("--index", type=int, default=0, help="which instance in the split")
    ap.add_argument("--budget", type=int, default=6)
    ap.add_argument("--modality", default="text", choices=["text", "image"])
    ap.add_argument("--deviation", default="on", choices=["on", "off"])
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    insts = [json.loads(l) for l in open(os.path.join(HERE, "data", f"instances_{args.split}.jsonl"))]
    inst = insts[args.index]
    env = FridgeRepairEnv(budget=args.budget, state_modality=args.modality,
                          show_deviation=(args.deviation == "on"))
    agent = _make_agent(args.agent)
    rec = run_episode(env, agent, inst, verbose=args.verbose)
    env.close()
    print(json.dumps(rec, indent=2))
