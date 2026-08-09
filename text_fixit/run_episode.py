#!/usr/bin/env python
"""
Drive one agent through one instance and log the trajectory.

Loop (matches MILESTONE_1 sec.8):
  reset -> repeat [ agent.act -> parse (1 reparse retry on malformed) -> env.step ] until COMMIT
  or the SIMULATE budget is exhausted, then auto-commit the best simulated fix.

The parse is contract-aware (env.action_contract): "batch" accepts an ordered LIST of actions in one
turn, "stack" accepts one action per turn plus RESET() and a bare COMMIT.

Per-episode record captures everything evaluate.py needs for the metrics; if a RunLogger is passed,
every TURN is additionally logged verbatim (reasoning, raw model output, exact prompt, images sent,
per-part evaluation, latency, tokens) -- see runlog.py.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import action_parser  # noqa: E402
from env import FridgeRepairEnv  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def _parse_kwargs(env):
    return {"multi": env.action_contract == "batch",
            "allow_reset": env.action_contract == "stack",
            "allow_bare_commit": env.action_contract == "stack",
            "reveal_fixable": not env.hard}


def _gt_fix_actions(env):
    """The ground-truth repair rendered in the agent's own action language (for the trajectory log)."""
    seq = env.instance.get("gt_fix_sequence")
    if not seq:
        gt = env.instance.get("gt_fix")
        if not gt:
            return "n/a"
        seq = [{"link": env.instance["link"], "spec": gt}]
    out = []
    for f in seq:
        pid = env.pid_of_link.get(f["link"], "P?")
        out.append(action_parser.format_call(f["spec"], pid))
    return "; ".join(out)


def run_episode(env, agent, instance, prompts=None, verbose=False, logger=None):
    obs = env.reset(instance)
    agent.reset()
    prompts = prompts or {}
    oneshot = getattr(agent, "oneshot", False)
    turns = 0
    max_turns = 1 if oneshot else env.budget + 5   # one-shot = a single commit decision
    seen_sims = set()
    repeated = 0
    first_sim_score = None
    pkw = _parse_kwargs(env)
    turn_log = []
    api_giveups = 0     # turns where the API never returned usable text (see below)

    while not env.terminal and turns < max_turns:
        budget_left = env.budget - env.sim_count
        ctx = {"env": env, "obs": obs, "step": turns, "budget_left": budget_left,
               "system_prompt": prompts.get("system"), "step_prompt": prompts.get("step"),
               "history": env.history, "retry_error": None}
        images_sent = list(obs.get("images", []))
        raw = agent.act(ctx)
        parsed = action_parser.parse(raw, env.id_map, **pkw)
        reparse = None
        if not parsed["valid"]:
            reparse = {"first_raw": raw, "error": parsed["error"]}
            if logger:
                logger.error({"episode": instance["id"], "turn": turns, "kind": "parse",
                              "error": parsed["error"], "raw": raw})
            ctx["retry_error"] = parsed["error"]          # 1 reparse retry, error echoed
            raw = agent.act(ctx)
            parsed = action_parser.parse(raw, env.id_map, **pkw)

        # A SIMULATE with no budget left -> auto-commit the best simulated fix.
        if parsed["valid"] and parsed["mode"] == "SIMULATE" and budget_left <= 0:
            obs, _ = env.auto_commit_best()
            break

        # An exhausted-retries API call falls back to "COMMIT NO_FIX()", which would otherwise be
        # indistinguishable from the model genuinely giving up. Count it so infrastructure failures
        # can be separated from model failures when reading the results.
        if (getattr(agent, "last_meta", {}) or {}).get("gave_up"):
            api_giveups += 1

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

        if logger is not None:
            meta = getattr(agent, "last_meta", {}) or {}
            ev = obs.get("eval") or {}
            entry = {
                "episode": instance["id"], "turn": turns, "budget_left": budget_left,
                "mode": parsed["mode"], "invalid": bool(obs.get("invalid")),
                "parse_error": parsed["error"], "reparse": reparse,
                "think": parsed.get("think", ""), "backtrack": parsed.get("backtrack", False),
                "raw_output": raw,
                "actions": [{"type": a["type"], "part_id": a.get("part_id"),
                             "axis": (a["spec"] or {}).get("axis"),
                             "value": (a["spec"] or {}).get("value"),
                             "raw_value": a.get("raw_value")} for a in parsed["actions"]],
                "action_str": env.history[-1]["action_str"] if env.history else None,
                "state_specs": env.history[-1].get("state_specs") if env.history else None,
                "pass": bool(ev.get("PASS")) if ev else None,
                "score": round(ev["score"], 4) if ev else None,
                "deviation_mm": round(ev["deviation_mm"], 1) if ev else None,
                "closes": ev.get("closes"), "collides": ev.get("collides"),
                "per_part": {k: {"deviation_mm": v["deviation_mm"], "within_tol": v["within_tol"],
                                 "closes": v["closes"]}
                             for k, v in (ev.get("per_part") or {}).items()},
                "image_paths": logger.images(instance["id"], turns, images_sent),
                "latency_s": meta.get("latency_s"), "usage": meta.get("usage"),
                "finish_reason": meta.get("finish_reason"), "attempts": meta.get("attempts"),
            }
            turn_log.append(entry)
            logger.turn(entry)
            pr = getattr(agent, "last_prompt", None)
            if pr:
                logger.prompt(instance["id"], turns, pr.get("system"), pr.get("user"))
            if meta:
                logger.raw(instance["id"], dict(meta, turn=turns))
            for err in meta.get("errors", []) or []:
                logger.error({"episode": instance["id"], "turn": turns, "kind": "api", **err})

        if verbose:
            print(f"[turn {turns}] {raw.strip()[:80]}")

    if not env.terminal:                                  # ran out of turns (e.g. invalid storm)
        obs, _ = env.auto_commit_best()

    terminal = env.history[-1]
    ev = terminal["eval"]
    committed = terminal["mode"] in ("COMMIT",)
    rec = {
        "id": instance["id"],
        "base": instance["base"],
        "agent": agent.name,
        "contract": env.action_contract,
        "hard": env.hard,
        "state_modality": env.state_modality,
        "show_deviation": env.show_deviation,
        "level": instance.get("level", "single"),
        "n_faults": instance.get("n_faults", 1),
        "fault_types": instance.get("fault_types", []),
        "faulty_links": instance.get("faulty_links", [instance.get("link")]),
        "corruption_type": instance["corruption"]["type"],
        "gt_fix_actions": _gt_fix_actions(env),
        "terminal_pass": bool(ev["PASS"]),
        "terminal_score": float(ev["score"]),
        "terminal_deviation_mm": float(ev["deviation_mm"]),
        "terminal_per_part": {k: {"deviation_mm": v["deviation_mm"],
                                  "within_tol": v["within_tol"], "closes": v["closes"]}
                              for k, v in (ev.get("per_part") or {}).items()},
        "initial_deviation_mm": float(env.reset_eval["deviation_mm"]),
        "terminal_mode": terminal["mode"],
        "committed": committed,
        "n_simulate": env.sim_count,
        "n_invalid": env.invalid_count,
        "n_reset": env.reset_count,
        "n_repeated": repeated,
        "n_api_giveup": api_giveups,
        "first_sim_score": first_sim_score,
        "first_sim_pass": (first_sim_score is not None and first_sim_score >= 0.80),
        "history": [{"mode": h["mode"], "action": h["action_str"],
                     "think": h.get("think", ""), "backtrack": h.get("backtrack", False),
                     "n_actions": h.get("n_actions"), "state_specs": h.get("state_specs"),
                     "pass": bool(h["eval"]["PASS"]), "score": round(h["eval"]["score"], 4),
                     "deviation_mm": round(h["eval"]["deviation_mm"], 1)} for h in env.history],
    }
    if logger is not None:
        logger.episode(rec)
        logger.trajectory(rec, turn_log)
    return rec


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
    if name in ("qwen", "loop_qwen"):
        from agents.qwen_vl import QwenVLAgent
        return QwenVLAgent(oneshot=False, history="window3")
    if name == "loop_qwen_full":
        from agents.qwen_vl import QwenVLAgent
        return QwenVLAgent(oneshot=False, history="full")
    if name == "oneshot_qwen":
        from agents.qwen_vl import QwenVLAgent
        return QwenVLAgent(oneshot=True)
    raise ValueError(f"unknown agent {name!r}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="oracle")
    ap.add_argument("--split", default="test")
    ap.add_argument("--instances", default=None, help="explicit jsonl path (overrides --split)")
    ap.add_argument("--index", type=int, default=0, help="which instance in the split")
    ap.add_argument("--budget", type=int, default=6)
    ap.add_argument("--modality", default="text", choices=["text", "image"])
    ap.add_argument("--deviation", default="on", choices=["on", "off"])
    ap.add_argument("--contract", default="batch", choices=["batch", "stack"])
    ap.add_argument("--hard", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    path = args.instances or os.path.join(HERE, "data", f"instances_{args.split}.jsonl")
    insts = [json.loads(l) for l in open(path)]
    inst = insts[args.index]
    env = FridgeRepairEnv(budget=args.budget, state_modality=args.modality,
                          show_deviation=(args.deviation == "on"),
                          action_contract=args.contract, hard=args.hard)
    agent = _make_agent(args.agent)
    rec = run_episode(env, agent, inst, verbose=args.verbose)
    env.close()
    print(json.dumps(rec, indent=2))
