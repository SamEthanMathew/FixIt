#!/usr/bin/env python
"""
Repeated-trial runner: ONE problem, N independent attempts, one condition per invocation.

`evaluate.py` runs a list of instances once each. This runs the SAME instance N times, which is what
you need to see a model's *variance* rather than its average over a heterogeneous set — at
temperature 0.7 the same model on the same fridge can solve it on trial 3 and fail on trial 4, and
that spread is invisible when every episode is a different problem.

Layout — one self-contained folder per trial, so a single trial can be handed to someone whole:

    runs/<prompt>_<model>_<modality>/
        manifest.json            condition config: model, prompt set, contract, tolerance, instance
        trial_01/
            records.jsonl        the episode record
            turns.jsonl          per turn: reasoning, raw output, parsed action, evaluation, tokens
            prompts/*.txt        the exact system+user text sent each turn
            images/<id>/*.png    every image actually sent
            raw/*.jsonl          raw API metadata
            trajectories/*.md    readable rollout
        ...
        trial_10/
        summary.md / summary.json

    python text_fixit/run_trials.py --agent loop_gemini_full --model gemini-3.1-pro-preview \
        --instance 10685_ctrl_translate_0 --trials 10 --modality image --run one_error_g3_image
"""
import argparse
import json
import os
import statistics as st
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom                                    # noqa: E402
from env import FridgeRepairEnv                # noqa: E402
from run_episode import _make_agent, run_episode   # noqa: E402
from runlog import RunLogger                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_instance(path, iid):
    for line in open(path):
        r = json.loads(line)
        if r["id"] == iid:
            return r
    raise SystemExit(f"instance {iid!r} not found in {path}")


def _tok(turns, key):
    return sum((t.get("usage") or {}).get(key) or 0 for t in turns)


def summarize(cond, problems, trials, wall, args):
    """trials: list of {record, turns, seconds}."""
    inst = problems[0]
    tau = inst["tau_mm"]
    solved = [t for t in trials if t["record"]["terminal_pass"]]
    failed = [t for t in trials if not t["record"]["terminal_pass"]]

    # deviation trajectory: best-so-far per turn index, averaged across trials. Best-so-far rather
    # than raw, because a model that finds a good state then wanders should not look like it never
    # found one.
    maxlen = max((len(t["record"]["history"]) for t in trials), default=0)
    traj = []
    for i in range(maxlen):
        vals = []
        for t in trials:
            h = t["record"]["history"]
            if i < len(h):
                # best-so-far in units of THAT problem's tolerance -- tolerance varies per shape,
                # so raw millimetres are not comparable across a mixed set. <=1.0 means passing.
                vals.append(min(x["deviation_over_tau"] for x in h[:i + 1]))
        if vals:
            traj.append({"turn": i + 1, "n": len(vals),
                         "mean_best_over_tau": round(sum(vals) / len(vals), 2),
                         "best_single_over_tau": round(min(vals), 2),
                         "n_under_threshold": sum(1 for v in vals if v <= 1.0)})

    closest = [min(x["deviation_over_tau"] for x in t["record"]["history"]) for t in trials]
    all_turns = [x for t in trials for x in t["turns"]]
    lat = [x["latency_s"] for x in all_turns if x.get("latency_s")]
    # vLLM: prompt_tokens/completion_tokens. Gemini: prompt_token_count/candidates_token_count,
    # plus thoughts_token_count -- reasoning tokens, reported SEPARATELY but billed as output. On a
    # thinking model they dominate: ~3,000 thought tokens against ~25 visible ones per turn, so
    # counting only the visible ones understates output (and cost) by about 100x.
    tin = _tok(all_turns, "prompt_tokens") or _tok(all_turns, "prompt_token_count")
    tvis = _tok(all_turns, "completion_tokens") or _tok(all_turns, "candidates_token_count")
    tthink = _tok(all_turns, "thoughts_token_count")
    tout = tvis + tthink

    s = {
        "condition": cond,
        "prompt_set": args.prompt_set, "model": args.model, "agent": args.agent,
        "modality": args.modality, "contract": args.contract, "max_actions": args.max_actions,
        "budget": args.budget, "tau_frac": geom.TAU_FRAC,
        "problem_set": {"n": len(problems), "instances_path": args.instances,
                        "mean_difficulty_D": round(sum(q["broken_deviation_mm"] / q["tau_mm"]
                                                       for q in problems) / len(problems), 2)},
        "trials": len(trials),
        "solved": len(solved),
        "success_rate": round(len(solved) / len(trials), 4) if trials else None,
        "iterations_when_solved": _stats([t["record"]["n_simulate"] for t in solved]),
        "iterations_when_failed": _stats([t["record"]["n_simulate"] for t in failed]),
        "ever_reached_threshold": sum(1 for c in closest if c <= 1.0),
        "closest_approach_over_tau": {"best": round(min(closest), 2),
                                      "mean": round(sum(closest) / len(closest), 2),
                                      "median": round(st.median(closest), 2)},
        "by_fault_type": {ft: {
            "n": len([t for t in trials if t["record"]["corruption_type"] == ft]),
            "solved": len([t for t in trials if t["record"]["corruption_type"] == ft
                           and t["record"]["terminal_pass"]]),
            "mean_closest_over_tau": round(sum(
                min(x["deviation_over_tau"] for x in t["record"]["history"])
                for t in trials if t["record"]["corruption_type"] == ft)
                / max(1, len([t for t in trials if t["record"]["corruption_type"] == ft])), 2),
        } for ft in sorted({t["record"]["corruption_type"] for t in trials})},
        "deviation_trajectory": traj,
        "wall_clock_s": round(wall, 1),
        "seconds_per_trial": _stats([round(t["seconds"], 1) for t in trials]),
        "turn_latency_s": _stats([round(x, 1) for x in lat]),
        "tokens": {"prompt": tin, "completion_visible": tvis, "thinking": tthink,
                   "output_billed": tout, "total": tin + tout,
                   "per_trial": round((tin + tout) / max(1, len(trials)))},
        "integrity": {"invalid_actions": sum(t["record"]["n_invalid"] for t in trials),
                      "api_giveup_trials": sum(1 for t in trials if t["record"]["n_api_giveup"]),
                      "images_sent_per_turn": sorted({x.get("images_sent_to_model") for x in all_turns
                                                      if x.get("images_sent_to_model") is not None})},
        "per_problem": [{"slot": t["slot"], "id": t["record"]["id"],
                         "fault_type": t["record"]["corruption_type"],
                         "ground_truth": t["record"]["gt_fix_actions"],
                         "tau_mm": round(t["record"]["tau_mm"], 1),
                         "initial_deviation_mm": round(t["record"]["initial_deviation_mm"], 1),
                         "passed": t["record"]["terminal_pass"],
                         "iterations": t["record"]["n_simulate"],
                         "final_over_tolerance_mm": t["record"]["terminal_over_tolerance_mm"],
                         "final_over_tau": t["record"]["terminal_deviation_over_tau"],
                         "closest_over_tau": round(c, 2),
                         "seconds": round(t["seconds"], 1),
                         # every turn: what it did, and how far from PASSING that left it
                         "turns": [{"turn": k + 1, "action": h["action"],
                                    "over_tolerance_mm": h["over_tolerance_mm"],
                                    "over_tau": h["deviation_over_tau"], "pass": h["pass"]}
                                   for k, h in enumerate(t["record"]["history"])]}
                        for t, c in zip(trials, closest)],
    }
    if args.price_in and args.price_out:
        s["estimated_cost_usd"] = round(tin / 1e6 * args.price_in + tout / 1e6 * args.price_out, 4)
    return s


def _stats(xs):
    if not xs:
        return None
    return {"n": len(xs), "min": min(xs), "max": max(xs), "median": st.median(xs),
            "mean": round(sum(xs) / len(xs), 2)}


def render(s):
    ps, L = s["problem_set"], []
    f = lambda d: "—" if not d else f"{d['min']}–{d['max']} (median {d['median']:g}, mean {d['mean']:g})"  # noqa: E731
    L += [f"# {s['condition']}", "",
          f"**{s['solved']}/{s['trials']} solved ({100 * s['success_rate']:.0f}%)** — "
          f"{s['trials']} distinct problems, one attempt each.", "",
          "| | |", "|---|---|",
          f"| model | `{s['model']}` |", f"| prompt set | `{s['prompt_set']}` |",
          f"| agent / modality | `{s['agent']}` · {s['modality']} |",
          f"| contract | {s['contract']}, max {s['max_actions']} action(s)/turn, budget {s['budget']} |",
          f"| problems | {ps['n']} from `{ps['instances_path']}` |",
          f"| mean difficulty | **{ps['mean_difficulty_D']}× tolerance** at start |",
          f"| tolerance | τ = {100 * s['tau_frac']:.1f}% of each part's size |", "",
          "## By fault type", "",
          "| type | solved | mean closest (× tolerance) |", "|---|---|---|"] + [
          f"| {k} | {v['solved']}/{v['n']} | {v['mean_closest_over_tau']}× |"
          for k, v in s["by_fault_type"].items()] + ["",
          "## Outcome", "",
          f"- iterations when **solved**: {f(s['iterations_when_solved'])}",
          f"- iterations when **failed**: {f(s['iterations_when_failed'])}",
          f"- problems that ever got under threshold: **{s['ever_reached_threshold']}/{s['trials']}**",
          f"- closest approach (× tolerance): best **{s['closest_approach_over_tau']['best']}×**, "
          f"median {s['closest_approach_over_tau']['median']}×, "
          f"mean {s['closest_approach_over_tau']['mean']}×", "",
          "## Convergence — best distance from threshold by turn N (1.0× = passing)", "",
          "| turn | mean best (× tol) | best single (× tol) | problems under threshold |",
          "|---|---|---|---|"]
    for t in s["deviation_trajectory"]:
        L.append(f"| {t['turn']} | {t['mean_best_over_tau']}× | {t['best_single_over_tau']}× | "
                 f"{t['n_under_threshold']}/{t['n']} |")
    L += ["", "## Cost", "",
          f"- wall clock: **{s['wall_clock_s']:.0f}s** total, {f(s['seconds_per_trial'])} per trial",
          f"- per-turn latency: {f(s['turn_latency_s'])}",
          f"- tokens: {s['tokens']['prompt']:,} prompt + {s['tokens']['output_billed']:,} output "
          f"(of which {s['tokens']['thinking']:,} thinking, {s['tokens']['completion_visible']:,} "
          f"visible) = **{s['tokens']['total']:,}** ({s['tokens']['per_trial']:,}/trial)"]
    if "estimated_cost_usd" in s:
        L.append(f"- estimated cost: **${s['estimated_cost_usd']}**")
    L += ["", "## Integrity", "",
          f"- invalid actions: {s['integrity']['invalid_actions']}",
          f"- trials hit by an API give-up: {s['integrity']['api_giveup_trials']}",
          f"- images sent per turn: {s['integrity']['images_sent_per_turn'] or 'n/a (text)'}", "",
          "## Per problem", "",
          "| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |",
          "|---|---|---|---|---|---|---|"]
    for t in s["per_problem"]:
        L.append(f"| `{t['id']}` | {t['fault_type']} | {'**PASS**' if t['passed'] else 'fail'} | "
                 f"{t['iterations']} | {t['closest_over_tau']}× | "
                 f"{t['final_over_tolerance_mm']:+.0f} | `{t['ground_truth']}` |")
    return "\n".join(L) + "\n"


def merge(run, ipath, args):
    """Recombine <run>_s*/ into <run>/ and recompute one summary over all shards.

    Shards are disjoint by construction (index %% N), so episode folders never collide; they are
    MOVED rather than copied so the merged condition is the single source of truth afterwards.
    """
    import glob as _glob
    import shutil
    dest = os.path.join(HERE, "runs", run)
    os.makedirs(dest, exist_ok=True)
    shards = sorted(_glob.glob(os.path.join(HERE, "runs", f"{run}_s*")))
    if not shards:
        raise SystemExit(f"no shards found matching {run}_s*")
    trials, seen = [], set()
    for sd in shards:
        for ep in sorted(os.listdir(sd)):
            src = os.path.join(sd, ep)
            if not os.path.isdir(src) or not os.path.exists(os.path.join(src, "records.jsonl")):
                continue
            if ep in seen:
                print(f"  WARNING: {ep} appears in more than one shard; keeping the first")
                continue
            seen.add(ep)
            dst = os.path.join(dest, ep)
            if not os.path.exists(dst):
                shutil.move(src, dst)
            rec = json.loads(open(os.path.join(dst, "records.jsonl")).read().splitlines()[0])
            turns = [json.loads(x) for x in open(os.path.join(dst, "turns.jsonl"))]
            secs = 0.0
            mf = os.path.join(dst, "manifest.json")
            if os.path.exists(mf):
                secs = (json.load(open(mf)).get("summary") or {}).get("seconds") or 0.0
            trials.append({"record": rec, "turns": turns, "seconds": secs, "slot": ep})
    by_id = {q["id"]: q for q in (json.loads(l) for l in open(ipath))}
    problems = [by_id[t["record"]["id"]] for t in trials]
    s = summarize(run, problems, trials, sum(t["seconds"] for t in trials), args)
    s["sharded_from"] = [os.path.basename(x) for x in shards]
    json.dump(s, open(os.path.join(dest, "summary.json"), "w"), indent=2)
    open(os.path.join(dest, "summary.md"), "w").write(render(s))
    for sd in shards:
        if not os.listdir(sd):
            os.rmdir(sd)
    print(f"merged {len(shards)} shards -> {len(trials)} problems, "
          f"{s['solved']}/{s['trials']} solved -> {dest}/summary.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--instances", default="data/instances_control.jsonl")
    ap.add_argument("--instance", default=None,
                    help="run ONE problem --trials times (variance on a fixed problem)")
    ap.add_argument("--shard", default=None, metavar="I/N",
                    help="sweep only problems where index %% N == I (0-indexed). Problems are "
                         "independent, so a condition can be split across processes; each shard "
                         "writes to <run>_s<I> and --merge recombines them.")
    ap.add_argument("--merge", action="store_true",
                    help="combine <run>_s*/ into <run>/ and write the unified summary")
    ap.add_argument("--sweep", action="store_true",
                    help="run EVERY instance in --instances once (coverage across problems); "
                         "subfolders are keyed by episode id instead of trial number")
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--run", required=True)
    ap.add_argument("--modality", default="image", choices=["text", "image"])
    ap.add_argument("--contract", default="batch", choices=["batch", "stack"])
    ap.add_argument("--max-actions", dest="max_actions", type=int, default=1)
    ap.add_argument("--budget", type=int, default=10)
    ap.add_argument("--deviation", default="off", choices=["on", "off"])
    ap.add_argument("--hard", action="store_true")
    ap.add_argument("--reveal-fixable", dest="reveal_fixable", action="store_true", default=None)
    ap.add_argument("--price-in", type=float, default=None, help="USD per 1M prompt tokens")
    ap.add_argument("--price-out", type=float, default=None, help="USD per 1M completion tokens")
    args = ap.parse_args()

    if args.model:
        # Route to the env var the chosen agent actually reads. QwenVLAgent takes QWEN_MODEL and
        # GeminiAgent takes GEMINI_MODEL; setting only the latter meant `--agent loop_qwen --model X`
        # silently evaluated the BASE model, which would score a fine-tuned adapter as if training
        # had done nothing.
        if "qwen" in args.agent:
            os.environ["QWEN_MODEL"] = args.model
        else:
            os.environ["GEMINI_MODEL"] = args.model
    ipath = args.instances if os.path.isabs(args.instances) else os.path.join(HERE, args.instances)
    # --merge recombines finished shards and needs neither --instance nor --sweep, so it has to be
    # handled before the "give one or the other" validation below.
    if args.merge:
        args.prompt_set = os.environ.get("FIXIT_PROMPT_SET", "one_error")
        merge(args.run, ipath, args)
        return
    if args.sweep:
        problems = [json.loads(l) for l in open(ipath)]
        if args.shard:
            i, n = (int(x) for x in args.shard.split("/"))
            problems = [q for k, q in enumerate(problems) if k % n == i]
            print(f"shard {i}/{n}: {len(problems)} problems", flush=True)
    elif args.instance:
        problems = [load_instance(ipath, args.instance)] * args.trials
    else:
        raise SystemExit("give --instance (repeat one problem) or --sweep (run the whole set)")
    args.prompt_set = os.environ.get("FIXIT_PROMPT_SET", "one_error")

    for q in problems:
        tf = q.get("tau_frac")
        if tf is not None and abs(tf - geom.TAU_FRAC) > 1e-12:
            raise SystemExit(f"{q['id']} was generated at tau_frac={tf} "
                             f"but FIXIT_TAU_FRAC={geom.TAU_FRAC}")

    run_name = args.run if not args.shard else f"{args.run}_s{args.shard.split('/')[0]}"
    cond_dir = os.path.join(HERE, "runs", run_name)
    os.makedirs(cond_dir, exist_ok=True)
    trials, t0 = [], time.time()
    for i, inst in enumerate(problems, start=1):
        slot = inst["id"] if args.sweep else f"trial_{i:02d}"
        env = FridgeRepairEnv(budget=args.budget, state_modality=args.modality,
                              show_deviation=(args.deviation == "on"), action_contract=args.contract,
                              hard=args.hard, reveal_fixable=args.reveal_fixable,
                              max_actions=args.max_actions)
        agent = _make_agent(args.agent, seed=i)
        logger = RunLogger(cond_dir, slot)
        logger.manifest(agent=args.agent, model=getattr(agent, "model", None), trial=i,
                        budget=args.budget, modality=args.modality, contract=args.contract,
                        max_actions=args.max_actions, tau_frac=geom.TAU_FRAC,
                        prompt_set=args.prompt_set, instances_path=ipath,
                        instance_ids=[inst["id"]], n_instances=1,
                        show_deviation=(args.deviation == "on"),
                        history_mode=getattr(agent, "history", None),
                        temperature=getattr(agent, "temperature", None),
                        max_output_tokens=getattr(agent, "max_tokens", None))
        s0 = time.time()
        rec = run_episode(env, agent, inst, logger=logger)
        secs = time.time() - s0
        env.close()
        logger.finish(n=1, solved=int(rec["terminal_pass"]), seconds=round(secs, 1))
        turns = [json.loads(x) for x in open(os.path.join(cond_dir, slot, "turns.jsonl"))]
        trials.append({"record": rec, "turns": turns, "seconds": secs, "slot": slot})
        print(f"[{args.run}] {i}/{len(problems)} {slot[:30]:30s} PASS={rec['terminal_pass']} "
              f"sims={rec['n_simulate']} over_tol={rec['terminal_over_tolerance_mm']:+.0f}mm "
              f"({rec['terminal_deviation_over_tau']:.1f}x) {secs:.0f}s",
              flush=True)

    if args.shard:      # a shard is partial; --merge writes the real summary
        print(f"\nshard {args.shard} done: {sum(1 for x in trials if x['record']['terminal_pass'])}"
              f"/{len(trials)} solved -> {cond_dir}")
        return
    s = summarize(args.run, problems, trials, time.time() - t0, args)
    json.dump(s, open(os.path.join(cond_dir, "summary.json"), "w"), indent=2)
    open(os.path.join(cond_dir, "summary.md"), "w").write(render(s))
    print(f"\n{args.run}: {s['solved']}/{s['trials']} solved -> {cond_dir}/summary.md")


if __name__ == "__main__":
    main()
