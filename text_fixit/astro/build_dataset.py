#!/usr/bin/env python
"""
Assemble the ASTRO SFT dataset: replay each verbalized trace through a real FridgeRepairEnv and
emit (prompt, completion) pairs.

WHY REPLAY INSTEAD OF FORMATTING A STRING
-----------------------------------------
The turn prompt is not a static template. `$history`, `$untried`, `$targetable` and `$found_note`
are all computed from `env.history` at the moment of the call -- the harness keeps books the model
cannot, listing untried (operation, axis) pairs per part and deducing which parts its own probes
have proven healthy. A prompt written by hand would drift from the one the agent actually sees at
evaluation, and the model would be trained on inputs that never occur.

So every example here is produced by stepping a real environment and asking the REAL agent object
for its prompts -- `GeminiAgent._system_prompt` / `._step_prompt`, the exact methods
`QwenVLAgent.act()` calls on the window3 path. Prompt parity is structural, not asserted.

WHY EVERY TURN IS AN INDEPENDENT EXAMPLE
----------------------------------------
`loop_qwen` runs `history="window3"`, and in `GeminiAgent.act()` that path is a STATELESS
single-message call: system prompt + one step prompt, rebuilt from scratch each turn, with the
probe log injected as text. So a k-backtrack trace of n turns yields n independent
(system, user) -> assistant pairs. No multi-turn masking, no conversation collator, and the
backtracking behaviour still transfers because the evidence the model reflects on is in the
rendered `$history` block it is conditioned on.

OUTPUT
------
JSONL in TRL's prompt-completion conversational form, so the prompt is masked out of the loss
without depending on a chat template that supports `{% generation %}`:

    {"prompt":     [{"role": "system", ...}, {"role": "user", ...}],
     "completion": [{"role": "assistant", "content": "<think>...</think><act>...</act>"}],
     "meta":       {...}}

VERIFICATION, ENFORCED NOT ASSUMED
----------------------------------
  1. No unresolved `$var` reaches a prompt. `string.Template.safe_substitute` ships a typo silently
     (prompts/README.md:59-61 records this happening in production), so it is checked per example.
  2. Every completion parses under the SAME kwargs run_episode uses at evaluation, including the
     `ruled_out` enforcement -- an action this harness would reject must never be a training target.
  3. The trace's final COMMIT actually PASSes in PyBullet.
A trace failing any of these is dropped and counted, never silently repaired.

    FIXIT_TAU_FRAC=0.015 python text_fixit/astro/build_dataset.py \
        --instances data/instances_astro_train.jsonl \
        --out data/sft/astro_train.jsonl --report
"""
import argparse
import collections
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import action_parser                                   # noqa: E402
import geom                                            # noqa: E402
from astro.linearize import (DEFAULT_K_MIX, direct_trace, exhausted_trace,  # noqa: E402
                             sample_traces)
from astro.tree import build_tree                      # noqa: E402
from astro.verbalize import verbalize                  # noqa: E402
from env import FridgeRepairEnv                        # noqa: E402
from run_episode import _live_parse_kwargs             # noqa: E402

# A bare "$word" that survived safe_substitute. Excludes "$" followed by a digit or a delimiter so
# a literal dollar amount in prose is not flagged.
UNRESOLVED = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")

TARGET_TAU_FRAC = 0.015


def _agent(model_hint=None):
    """The real agent object, purely for its prompt-rendering half.

    QwenVLAgent subclasses GeminiAgent and overrides only the transport, so the prompts are
    identical; instantiating the Qwen one avoids any chance of a Gemini-only default leaking in.
    No network call is ever made -- `act()` is not used, only `_system_prompt` / `_step_prompt`.
    """
    from agents.qwen_vl import QwenVLAgent
    return QwenVLAgent(oneshot=False, history="window3", model=model_hint)


def _check_prompt(text, where, iid):
    bad = UNRESOLVED.findall(text or "")
    if bad:
        raise ValueError(f"{iid}: unresolved template vars in {where}: {sorted(set(bad))}")


def replay(instance, turns, agent, budget, modality, deviation, expect_pass=True):
    """Step the env through `turns`, returning one training example per turn.

    Returns (examples, error). `error` is None on success; on failure `examples` is discarded.
    expect_pass=False marks a budget-exhaustion trace (linearize.exhausted_trace), whose final
    COMMIT is the best failing attempt by design.
    """
    env = FridgeRepairEnv(budget=budget, state_modality=modality,
                          show_deviation=deviation, action_contract="batch", max_actions=1)
    try:
        obs = env.reset(instance)
        agent.reset()
        out = []
        for turn in turns:
            budget_left = env.budget - env.sim_count
            if turn["mode"] == "SIMULATE" and budget_left <= 0:
                return [], "trace longer than the SIMULATE budget"
            system = agent._system_prompt(env)
            step = agent._step_prompt(env, obs, budget_left)
            _check_prompt(system, "system", instance["id"])
            _check_prompt(step, "step", instance["id"])

            # Parse with EXACTLY the kwargs run_episode uses, ruled_out included: a target the live
            # harness would reject is not a usable label, however sensible it looks.
            pkw = _live_parse_kwargs(env)
            parsed = action_parser.parse(turn["text"], env.id_map, **pkw)
            if not parsed["valid"]:
                return [], f"target rejected by the parser: {parsed['error']}"

            out.append({"system": system, "user": step, "assistant": turn["text"],
                        "mode": turn["mode"], "backtrack": turn["backtrack"],
                        "backtrack_kind": turn["backtrack_kind"],
                        "budget_left": budget_left, "call": turn["call"]})
            obs, terminal, _ = env.step(parsed)
            if terminal:
                ev = obs.get("eval") or {}
                if expect_pass and not ev.get("PASS"):
                    return [], "final COMMIT does not PASS"
                if not expect_pass and ev.get("PASS"):
                    return [], "exhaustion trace unexpectedly PASSed"
                if turn is not turns[-1]:
                    return [], "episode terminated before the trace ended"
        if not env.terminal:
            return [], "trace never committed"
        return out, None
    finally:
        env.close()


def _example(row, r, j, n_turns, k, trace_backtracks, aux, trace_id=0):
    return {
        "prompt": [{"role": "system", "content": row["system"]},
                   {"role": "user", "content": row["user"]}],
        "completion": [{"role": "assistant", "content": row["assistant"]}],
        "meta": {"instance": r["id"], "base": r["base"], "split": r.get("split"),
                 # trace_id disambiguates the multiple traces one instance yields (two k=1 draws
                 # are otherwise indistinguishable in meta, which broke a review audit).
                 "trace_id": trace_id,
                 "fault_type": r["fault_types"][0], "k": k,
                 "trace_backtracks": trace_backtracks, "turn": j + 1,
                 "n_turns": n_turns, "mode": row["mode"], "backtrack": row["backtrack"],
                 "backtrack_kind": row["backtrack_kind"], "call": row["call"], "aux": aux,
                 "D_over_tau": round(r["broken_deviation_mm"] / r["tau_mm"], 2)},
    }


def build(instances, agent, k_mix, budget, modality, deviation, seed,
          max_refine=4, top_m=3, arm="astro", aux=True, verbose=False):
    """arm "astro": ASTRO trace mix (k_mix) plus, when `aux`, one budget-exhaustion trace per
    UNSOLVED tree (review finding M2: without them, late-budget still-failing states and the
    commit-best-attempt rule have zero training mass while 19% of real eval turns live there).
    arm "direct": the clean count-controlled Direct arm (linearize.direct_trace) -- no failed
    probes, no flips, no aux; match training STEPS to the astro arm via --epochs, not by
    duplicating rows."""
    examples, stats = [], collections.Counter()
    per_instance = []
    for r in instances:
        t0 = time.time()
        root, st = build_tree(r, max_refine=max_refine, top_m=top_m)
        stats["trees"] += 1
        if not st["ok"]:
            stats["trees_invalid"] += 1
            # M2: an unsolved tree still supervises the states hard episodes actually reach.
            if arm == "astro" and aux and "faulty_pid" in st:
                steps, best = exhausted_trace(root, budget)
                if steps is not None:
                    turns = verbalize(steps, root.dev, st["faulty_pid"],
                                      commit_mode="best", best_node=best)
                    rows, err = replay(r, turns, agent, budget, modality, deviation,
                                       expect_pass=False)
                    if err:
                        stats["aux_dropped"] += 1
                        stats[f"drop:{err[:44]}"] += 1
                    else:
                        stats["aux_traces"] += 1
                        for j, row in enumerate(rows):
                            examples.append(_example(row, r, j, len(rows), k=None,
                                                     trace_backtracks=None, aux=True,
                                                     trace_id=-1))
                            stats["examples"] += 1
            per_instance.append({"id": r["id"], "ok": False, "reason": st["reason"]})
            continue
        stats["trees_valid"] += 1
        kept = 0
        if arm == "direct":
            traces = [{"k": 0, "steps": direct_trace(root), "n_backtracks": 0,
                       "n_part_backtracks": 0, "n_probes": 0}]
            traces = [t for t in traces if t["steps"]]
        else:
            traces = sample_traces(root, k_mix=k_mix, seed=seed)
        for ti, tr in enumerate(traces):
            # root.dev, not st["dev0_mm"]: the stats value is rounded to 2 decimals, and the
            # review measured 10 turns where that rounding broke the think text's "exactly as
            # before" equality against the numbers in the model's own observation.
            turns = verbalize(tr["steps"], root.dev, st["faulty_pid"])
            rows, err = replay(r, turns, agent, budget, modality, deviation)
            if err:
                stats["traces_dropped"] += 1
                stats[f"drop:{err[:44]}"] += 1
                continue
            stats["traces"] += 1
            stats["direct" if tr["n_backtracks"] == 0 else "search"] += 1
            stats["backtracks"] += tr["n_backtracks"]
            stats["part_backtracks"] += tr["n_part_backtracks"]
            kept += 1
            for j, row in enumerate(rows):
                examples.append(_example(row, r, j, len(rows), k=tr["k"],
                                         trace_backtracks=tr["n_backtracks"], aux=False,
                                         trace_id=ti))
                stats["examples"] += 1
                if row["backtrack"]:
                    stats["backtrack_turns"] += 1
        per_instance.append({"id": r["id"], "ok": True, "traces": kept,
                             "sims": st["n_sims"], "seconds": round(time.time() - t0, 1)})
        if verbose:
            print(f"  {r['id']}: {kept} traces, tree {st['n_sims']} sims, "
                  f"{time.time() - t0:.1f}s", flush=True)
    return examples, stats, per_instance


def report(examples, stats):
    print("\n" + "=" * 72)
    print("ASTRO SFT dataset")
    print("=" * 72)
    v, t = stats["trees_valid"], stats["trees"]
    print(f"  trees built            {t}")
    print(f"  trees valid            {v}  ({100.0 * v / max(1, t):.0f}%)   "
          f"[ASTRO: 14.0K/20.7K = 68%]")
    print(f"  traces kept            {stats['traces']}   "
          f"(direct k=0: {stats['direct']}, search k>=1: {stats['search']})")
    print(f"  traces dropped         {stats['traces_dropped']}")
    for k in sorted(k for k in stats if k.startswith("drop:")):
        print(f"      {k[5:]:48} {stats[k]}")
    print(f"  aux exhaustion traces  {stats['aux_traces']}  (dropped {stats['aux_dropped']})")
    print(f"  examples (turns)       {stats['examples']}")
    print(f"  backtracks             {stats['backtracks']}  "
          f"(to part_selection: {stats['part_backtracks']})")
    print(f"  turns carrying <backtrack/>  {stats['backtrack_turns']}")
    if examples:
        by_type = collections.Counter(e["meta"]["fault_type"] for e in examples)
        by_mode = collections.Counter(e["meta"]["mode"] for e in examples)
        bases = len({e["meta"]["base"] for e in examples})
        splits = collections.Counter(e["meta"]["split"] for e in examples)
        print(f"  by fault type          {dict(by_type)}")
        print(f"  by mode                {dict(by_mode)}")
        print(f"  distinct bases         {bases}    splits {dict(splits)}")


def main():
    ap = argparse.ArgumentParser()
    # Default is the TRAIN set, not std30: std30 mixes splits (19 train / 11 test shapes), and the
    # review found nothing between instance file and adapter stopped test shapes entering training.
    ap.add_argument("--instances", default="data/instances_astro_train.jsonl")
    ap.add_argument("--expect-split", default="train", choices=["train", "test", "any"],
                    help="refuse rows outside this split ('any' only for validation builds that "
                         "will never be trained on)")
    ap.add_argument("--arm", default="astro", choices=["astro", "direct"],
                    help="astro = ASTRO trace mix + budget-exhaustion aux; direct = the clean "
                         "count-controlled Direct ablation arm (no failures, no flips, no aux)")
    ap.add_argument("--no-aux", dest="aux", action="store_false",
                    help="astro arm only: skip the budget-exhaustion traces from unsolved trees")
    ap.add_argument("--out", default=None, help="JSONL destination (omit for a dry run)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--budget", type=int, default=10, help="must match the eval budget")
    ap.add_argument("--modality", default="text", choices=["text", "image"])
    ap.add_argument("--deviation", default="on", choices=["on", "off"],
                    help="must match the eval setting; the search procedure needs the number")
    ap.add_argument("--k-mix", default=",".join(str(k) for k in DEFAULT_K_MIX),
                    help="ASTRO sec.3.1 mix: one direct (k=0) plus three search solutions")
    ap.add_argument("--max-refine", type=int, default=4)
    ap.add_argument("--top-m", type=int, default=3)
    ap.add_argument("--prompt-set", default=None, help="overrides FIXIT_PROMPT_SET")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--show", type=int, default=0, help="print N rendered examples in full")
    ap.add_argument("--allow-default-tau", action="store_true")
    args = ap.parse_args()

    if args.prompt_set:
        os.environ["FIXIT_PROMPT_SET"] = args.prompt_set
    # Pin the two switches that silently change every prompt in the set. FIXIT_PROMPT_VARIANT
    # swaps whole template files when set, so an inherited value would produce a dataset that
    # matches no evaluation run.
    os.environ.setdefault("FIXIT_PROMPT_SET", "one_error_search")
    variant = os.environ.get("FIXIT_PROMPT_VARIANT", "")
    if not args.allow_default_tau and abs(geom.TAU_FRAC - TARGET_TAU_FRAC) > 1e-12:
        raise SystemExit(f"TAU_FRAC is {geom.TAU_FRAC}; run with FIXIT_TAU_FRAC={TARGET_TAU_FRAC}")

    path = args.instances if os.path.isabs(args.instances) else os.path.join(HERE, args.instances)
    rows = [json.loads(l) for l in open(path)]
    if args.limit:
        rows = rows[:args.limit]
    if args.expect_split != "any":
        bad = sorted({r["id"] for r in rows if r.get("split") != args.expect_split})
        if bad:
            raise SystemExit(
                f"{len(bad)} instances are not split={args.expect_split!r} (e.g. {bad[:4]}). "
                f"Training on test-split shapes voids the held-out eval. Use a split-pure "
                f"instance file (astro/make_sets.py), or --expect-split any for a validation "
                f"build that will never be trained on.")
    k_mix = tuple(int(x) for x in args.k_mix.split(","))

    print(f"instances {len(rows)} from {path}")
    print(f"prompt_set={os.environ['FIXIT_PROMPT_SET']!r} variant={variant!r} "
          f"tau_frac={geom.TAU_FRAC} modality={args.modality} deviation={args.deviation} "
          f"budget={args.budget} k_mix={k_mix}", flush=True)

    agent = _agent()
    t0 = time.time()
    examples, stats, per_instance = build(rows, agent, k_mix, args.budget, args.modality,
                                          args.deviation == "on", args.seed,
                                          max_refine=args.max_refine, top_m=args.top_m,
                                          arm=args.arm, aux=args.aux, verbose=args.verbose)
    print(f"\nbuilt in {time.time() - t0:.0f}s")

    for e in examples[:args.show]:
        print("\n" + "-" * 72)
        print("### SYSTEM\n" + e["prompt"][0]["content"])
        print("\n### USER\n" + e["prompt"][1]["content"])
        print("\n### ASSISTANT\n" + e["completion"][0]["content"])

    if args.report or not args.out:
        report(examples, stats)

    if args.out:
        out = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            for e in examples:
                f.write(json.dumps(e) + "\n")
        side = os.path.splitext(out)[0] + ".manifest.json"
        with open(side, "w") as f:
            json.dump({"instances_path": path, "n_instances": len(rows),
                       "arm": args.arm, "aux": args.aux, "expect_split": args.expect_split,
                       "prompt_set": os.environ["FIXIT_PROMPT_SET"], "prompt_variant": variant,
                       "tau_frac": geom.TAU_FRAC, "modality": args.modality,
                       "deviation": args.deviation, "budget": args.budget, "k_mix": list(k_mix),
                       "seed": args.seed, "max_refine": args.max_refine, "top_m": args.top_m,
                       "stats": dict(stats), "per_instance": per_instance}, f, indent=2)
        print(f"\nwrote {len(examples)} examples -> {out}")
        print(f"      manifest              -> {side}")


if __name__ == "__main__":
    main()
