#!/usr/bin/env python
"""
Batch evaluation + metrics report for the closed-loop fridge-repair task.

    python text_fixit/evaluate.py --agents random,oneshot_gemini,loop_gemini,oracle --split test

For each agent it runs every instance (run_episode), writes per-episode records to
runs/<run_id>/<agent>/records.jsonl, and aggregates the MILESTONE_1 sec.10 / paper sec.7 metrics
into reports/<run_id>.md (one row per agent). All metrics are on the held-out split given.
"""
import argparse
import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom  # noqa: E402
from env import FridgeRepairEnv  # noqa: E402
from run_episode import _make_agent, run_episode  # noqa: E402
from runlog import RunLogger  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return float("nan")
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def _bootstrap_ci(xs, stat=_mean, n=2000, seed=0):
    xs = [x for x in xs if x is not None]
    if not xs:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    reps = []
    for _ in range(n):
        sample = [xs[rng.randrange(len(xs))] for _ in range(len(xs))]
        reps.append(stat(sample))
    reps.sort()
    return (reps[int(0.025 * n)], reps[int(0.975 * n)])


def compute_metrics(records):
    n = len(records)
    succ = [1.0 if r["terminal_pass"] else 0.0 for r in records]
    scores = [r["terminal_score"] for r in records]
    solved = [r for r in records if r["terminal_pass"]]

    recov_pool = [r for r in records
                  if r["first_sim_score"] is not None and r["first_sim_score"] < 0.80]
    total_sims = sum(r["n_simulate"] for r in records)
    total_repeated = sum(r["n_repeated"] for r in records)
    total_invalid = sum(r["n_invalid"] for r in records)
    total_actions = total_sims + total_invalid + sum(1 for r in records if r["committed"])
    committed = [r for r in records if r["committed"]]

    s_lo, s_hi = _bootstrap_ci(succ)
    sc_lo, sc_hi = _bootstrap_ci(scores)
    return {
        "n": n,
        "success_rate": _mean(succ),
        "success_ci": (s_lo, s_hi),
        "mean_score": _mean(scores),
        "score_ci": (sc_lo, sc_hi),
        "efficiency_sims_per_solved": _mean([r["n_simulate"] for r in solved]) if solved else float("nan"),
        "sims_to_submit_mean": _mean([r["n_simulate"] for r in records]),
        "sims_to_submit_median": _median([r["n_simulate"] for r in records]),
        "committed_rate": _mean([1.0 if r["committed"] else 0.0 for r in records]),
        "recovery_rate": _mean([1.0 if r["terminal_pass"] else 0.0 for r in recov_pool]) if recov_pool else float("nan"),
        "recovery_n": len(recov_pool),
        "repeated_action_rate": (total_repeated / total_sims) if total_sims else 0.0,
        "invalid_action_rate": (total_invalid / total_actions) if total_actions else 0.0,
        "commit_precision": _mean([1.0 if r["terminal_pass"] else 0.0 for r in committed]) if committed else float("nan"),
        "over_budget_rate": _mean([0.0 if r["committed"] else 1.0 for r in records]),
        "resets_per_episode": _mean([r.get("n_reset", 0) for r in records]),
        "mean_actions_per_turn": _mean([h.get("n_actions") for r in records
                                        for h in r.get("history", []) if h.get("n_actions")]),
    }


def run_agent(agent_name, instances, run_dir, budget, modality, deviation, seed,
              contract="batch", hard=False, instances_path=None):
    """Run one agent over the instance list, logging EVERYTHING (see runlog.RunLogger): per-episode
    records, per-turn reasoning/raw output/prompts/images/API metadata, errors, and a readable
    trajectory per episode."""
    env = FridgeRepairEnv(budget=budget, state_modality=modality, show_deviation=deviation,
                          action_contract=contract, hard=hard)
    agent = _make_agent(agent_name, seed=seed)
    logger = RunLogger(run_dir, agent_name)
    logger.manifest(agent=agent_name, model=getattr(agent, "model", None), budget=budget,
                    modality=modality, show_deviation=deviation, contract=contract, hard=hard,
                    tau_frac=geom.TAU_FRAC, seed=seed, n_instances=len(instances),
                    instances_path=instances_path,
                    instance_ids=[i["id"] for i in instances],
                    temperature=getattr(agent, "temperature", None),
                    history_mode=getattr(agent, "history", None),
                    thinking=getattr(agent, "thinking", None))
    records = []
    for i, inst in enumerate(instances):
        rec = run_episode(env, agent, inst, logger=logger)
        records.append(rec)
        print(f"[{agent_name}] {i + 1}/{len(instances)} {inst['id'][:34]:34s} "
              f"PASS={rec['terminal_pass']} score={rec['terminal_score']:.2f} "
              f"sims={rec['n_simulate']}", flush=True)
    env.close()
    solved = sum(1 for r in records if r["terminal_pass"])
    logger.finish(n=len(records), solved=solved,
                  success_rate=(solved / len(records) if records else None))
    return records


def _fmt(x, pct=False):
    if x != x:  # nan
        return "n/a"
    return f"{100 * x:.0f}%" if pct else f"{x:.2f}"


def write_report(run_id, split, per_agent_metrics, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [f"# Fridge-repair evaluation - run `{run_id}` (split: {split})", "",
             "| agent | N | success | mean score | recovery | sims→submit (mean/med) | eff (solved) | committed | repeated | invalid | commit prec |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for agent, m in per_agent_metrics.items():
        sci = m["success_ci"]
        lines.append(
            f"| {agent} | {m['n']} | {_fmt(m['success_rate'], 1)} "
            f"[{_fmt(sci[0], 1)},{_fmt(sci[1], 1)}] | {_fmt(m['mean_score'])} | "
            f"{_fmt(m['recovery_rate'], 1)} (n={m['recovery_n']}) | "
            f"{_fmt(m['sims_to_submit_mean'])} / {_fmt(m['sims_to_submit_median'])} | "
            f"{_fmt(m['efficiency_sims_per_solved'])} | {_fmt(m['committed_rate'], 1)} | "
            f"{_fmt(m['repeated_action_rate'], 1)} | {_fmt(m['invalid_action_rate'], 1)} | "
            f"{_fmt(m['commit_precision'], 1)} |")
    lines += ["", "**Metrics** - success: terminal PASS (within tol & closes & no collision); "
              "recovery: of episodes whose first SIMULATE scored <0.80, fraction reaching PASS; "
              "sims→submit: SIMULATE tries before the final answer (mean/median over ALL episodes); "
              "eff(solved): mean tries among solved only; committed: fraction that chose COMMIT "
              "(rest auto-committed at budget); commit prec: of committed episodes, fraction PASS.", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def append_per_type(path, per_agent_records, types=("scale", "translate", "rotate"),
                    key="corruption_type", title="By fault type"):
    """Append a breakdown (success rate . mean score) grouped by `key` to the report.

    key="corruption_type" for the single-fault sets; key="level" for the hard benchmark, where the
    interesting split is composite_1door vs composite_2door vs control_single.
    """
    lines = ["", f"## {title}  (success rate · mean score)", "",
             "| agent | " + " | ".join(types) + " | overall |",
             "|---|" + "|".join(["---"] * (len(types) + 1)) + "|"]
    for agent, recs in per_agent_records.items():
        cells = []
        for t in types:
            sub = [r for r in recs if r.get(key) == t]
            if sub:
                sr = _mean([1.0 if r["terminal_pass"] else 0.0 for r in sub])
                ms = _mean([r["terminal_score"] for r in sub])
                cells.append(f"{_fmt(sr, 1)} · {_fmt(ms)} (n={len(sub)})")
            else:
                cells.append("n/a")
        sr = _mean([1.0 if r["terminal_pass"] else 0.0 for r in recs])
        ms = _mean([r["terminal_score"] for r in recs])
        cells.append(f"{_fmt(sr, 1)} · {_fmt(ms)}")
        lines.append(f"| {agent} | " + " | ".join(cells) + " |")
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")


def append_submit_histogram(path, per_agent_records, budget):
    """For each searching agent, distribution of tries-to-submit (n_simulate before COMMIT) and how
    many at each count were solved -- shows whether committing later converts to success."""
    lines = ["", f"## Tries to submit  (SIMULATE calls before final answer; hard cap {budget})", ""]
    for agent, recs in per_agent_records.items():
        if not any(r["n_simulate"] for r in recs):     # skip oneshot/oracle (no search)
            continue
        lines += [f"**{agent}**", "",
                  "| tries | episodes | solved | solve-rate |", "|---|---|---|---|"]
        by = defaultdict(list)
        for r in recs:
            by[r["n_simulate"]].append(r)
        for k in sorted(by):
            eps = by[k]
            ns = sum(1 for r in eps if r["terminal_pass"])
            note = " (auto-commit at cap)" if k >= budget else ""
            lines.append(f"| {k}{note} | {len(eps)} | {ns} | {_fmt(ns / len(eps), 1)} |")
        lines.append("")
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")


def load_split(split):
    if split == "all":
        out = []
        for s in ("test", "train"):
            out += [json.loads(l) for l in open(os.path.join(HERE, "data", f"instances_{s}.jsonl"))]
        return out
    return [json.loads(l) for l in open(os.path.join(HERE, "data", f"instances_{split}.jsonl"))]


def load_instances(path):
    return [json.loads(l) for l in open(path)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default="random,oracle")
    ap.add_argument("--split", default="test", help="test | train | all")
    ap.add_argument("--run", default="run1")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--per-type", type=int, default=None,
                    help="stratified: sample N instances of EACH corruption type (scale/translate/rotate)")
    ap.add_argument("--shuffle", action="store_true", help="seeded shuffle before --limit (spread across shapes)")
    ap.add_argument("--budget", type=int, default=6)
    ap.add_argument("--modality", default="text", choices=["text", "image"])
    ap.add_argument("--deviation", default="on", choices=["on", "off"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--instances", default=None,
                    help="explicit instances jsonl (e.g. data/instances_hard.jsonl); "
                         "overrides --split and disables --per-type stratification")
    ap.add_argument("--contract", default="batch", choices=["batch", "stack"],
                    help="batch = ordered action LIST applied fresh; stack = one action per turn "
                         "onto a persisted working state (+RESET)")
    ap.add_argument("--hard", action="store_true",
                    help="hard benchmark: hide the part table's fixable/role columns and render "
                         "doors in one neutral colour from a less favourable yaw")
    ap.add_argument("--model", default=None, help="sets GEMINI_MODEL for this run")
    ap.add_argument("--shard", default=None, metavar="I/N",
                    help="run only instances i where i %% N == I (0-indexed). Episodes are "
                         "independent, so a condition can be split across processes and merged; "
                         "each shard writes runs/<run>/<agent>/ under its own --run name")
    ap.add_argument("--report-only", action="store_true",
                    help="rebuild the report from existing runs/<run>/<agent>/records.jsonl, no runs")
    args = ap.parse_args()

    if args.model:
        os.environ["GEMINI_MODEL"] = args.model

    instances_path = args.instances
    if instances_path:
        if not os.path.isabs(instances_path):
            instances_path = os.path.join(HERE, instances_path)
        instances = load_instances(instances_path)
        args.per_type = None                 # explicit lists are used whole, in file order
    else:
        instances = load_split(args.split)
    rng = random.Random(args.seed)
    if args.per_type:
        pool = defaultdict(list)
        for r in instances:
            pool[r["corruption"]["type"]].append(r)
        sel = []
        for t in ("scale", "translate", "rotate"):
            g = list(pool.get(t, []))
            rng.shuffle(g)
            take = g[:args.per_type]
            if len(take) < args.per_type:
                print(f"WARNING: only {len(take)} '{t}' instances available (wanted {args.per_type})")
            sel += take
        rng.shuffle(sel)                       # interleave types so progress shows all kinds
        instances = sel
    else:
        if args.shuffle:
            rng.shuffle(instances)
        if args.limit:
            instances = instances[:args.limit]
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        instances = [inst for k, inst in enumerate(instances) if k % n == i]
        print(f"shard {i}/{n}: {len(instances)} instances", flush=True)

    run_dir = os.path.join(HERE, "runs", args.run)
    os.makedirs(run_dir, exist_ok=True)

    per_agent = {}
    per_agent_records = {}
    for agent_name in [a.strip() for a in args.agents.split(",") if a.strip()]:
        if args.report_only:
            path = os.path.join(run_dir, agent_name, "records.jsonl")
            records = [json.loads(l) for l in open(path)]
        else:
            records = run_agent(agent_name, instances, run_dir, args.budget, args.modality,
                                (args.deviation == "on"), args.seed,
                                contract=args.contract, hard=args.hard,
                                instances_path=instances_path)
        per_agent[agent_name] = compute_metrics(records)
        per_agent_records[agent_name] = records
        print(f"  -> {agent_name}: success={per_agent[agent_name]['success_rate']:.2f} "
              f"score={per_agent[agent_name]['mean_score']:.2f}", flush=True)

    report = write_report(args.run, (instances_path or args.split), per_agent,
                          os.path.join(HERE, "reports", f"{args.run}.md"))
    append_per_type(report, per_agent_records)
    levels = sorted({r.get("level") for recs in per_agent_records.values() for r in recs
                     if r.get("level") and r["level"] != "single"})
    if levels:
        append_per_type(report, per_agent_records, types=tuple(levels), key="level",
                        title="By difficulty level")
    append_submit_histogram(report, per_agent_records, args.budget)
    print(f"\nreport -> {report}")
    print(json.dumps({a: {k: v for k, v in m.items() if not k.endswith("_ci")}
                      for a, m in per_agent.items()}, indent=2))
