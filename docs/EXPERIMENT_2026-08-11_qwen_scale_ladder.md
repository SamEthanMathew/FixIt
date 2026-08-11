# Experiment (M9 + M10) — The Qwen scale ladder

**Date:** 2026-08-11
**Author:** FixIt / Stage-1 closed-loop repair
**Status:** COMPLETE (one cell at n=21/30, noted inline)
**Predecessors:** M7 `EXPERIMENT_2026-08-10_qwen_ladder.md`, M8 (in the M7+M8 commit)
**Raw tables:** `runs/_analysis/m9_scale_ladder.{md,json}`, `runs/_analysis/m10_*.{md,json}`

---

## 1. Why

M8 found the first rung where an open model produces reward events: `instances_easy.jsonl`
(median D=1.6), where Qwen3-VL-8B scores 17%. Two questions followed, and Stage-2 depends on both:

1. **Is the failure elsewhere capacity-bound?** If a larger open model clears the harder rungs, the
   answer is "buy parameters". If not, the answer is "the task needs something these models lack".
2. **Where exactly is the cliff?** M8 measured one easy rung and M7 measured two hard ones, but no
   model had been run across the whole difficulty range under a single consistent config.

`Qwen/Qwen3-VL-32B-Instruct-FP8` was chosen for the comparison. The bf16 32B (66.7 GB) does not fit
— 103 GB free on a disk at 94% — while FP8 (35.5 GB) does, and RTX 6000 Ada is sm_89 so vLLM runs
FP8 natively. Dense was preferred over the similarly-sized 30B-A3B MoE: the MoE activates ~3B params
per token (a weak test of capacity) and MoE fine-tuning is markedly more finicky than dense LoRA.

## 2. Two harness discoveries, both of which faked model failures

These belong in the record. Each one silently converted infrastructure failure into apparent model
failure, and each was caught only because the `gave_up` / invalid-action counters exist.

### 2.1 `history="full"` makes the 32B stop emitting `<act>` tags

The 32B's first runs showed 98 errors in 153 turns. Not context truncation (max prompt 11,371 of
16,384, zero truncations) and not output truncation (`finish_reason` was `stop` on every turn, max
completion 1,660 of a 4,096 cap). The model was writing a **complete plan in prose** and never
converting it to syntax:

> "I will adjust both doors: translate P1 inward along X to reduce overlap, scale P2 along Y … I will
> now simulate this repair."

No `<act>` tag in any of 91 failing turns; no formal call at all in 62 of them, so no parser fix
could have wrapped it. Post-retry invalid rate **58% of actions**, reparse recovering only 9%,
episodes averaging 5.3 SIMULATEs against a budget of 10.

**Cause: the accumulating conversational transcript.** Switching to `window3` — a stateless
single-message call that restates the instruction every turn, already a first-class mode in the
codebase — gave **0% invalid across 30 SIMULATEs**. Every M9/M10 run therefore uses `window3`.

Had this not been probed, the write-up would have read *"Qwen3-VL-32B cannot follow the action
protocol; scale makes compliance worse."* That would have been clean, plausible and false.

**The 8B is insensitive to the same flag** (hardened control: 1/25 under `window3` vs 0/25 under
`full`; easy image 17% both ways), so the M6–M8 8B results stand as written.

### 2.2 `QwenVLAgent` hardcoded a 180s client timeout

On TEXT observations the 32B writes ~790 completion tokens over per-part coordinate tables, against
~275 on images, pushing p90 latency to 402s and max to 549s. **20% of turns exceeded the 180s
timeout** → ReadTimeout → 3 retries → `gave_up` → fallback `COMMIT NO_FIX()`. Four of twelve
episodes in that arm were scored as the model declining to repair.

Fixed via a `QWEN_TIMEOUT` env override; the arm was rerun at 900s. The corrected score is **~3x the
contaminated one** (4/20 vs 1/12). The contaminated run is preserved at
`runs/_contaminated_m9_qw32_easy_text_timeout` (leading underscore keeps it out of the `m9_*` glob).

## 3. Design

Both models, five rungs, one config: `loop_qwen` (window3), batch contract, image modality, budget
10, deviation OFF. Each set is run at the τ it was generated under — 0.025 for the two easy rungs,
0.015 for the three hard ones. (`env.reset` only asserts this when the instance records a
`tau_frac`, and the older sets do not, so it is enforced by the launch command.)

## 4. Results

Invalid-action rate is **0% on every cell**. 95% Wilson intervals in brackets.

| rung | Qwen3-VL-8B | Qwen3-VL-32B-FP8 | API reference |
|---|---|---|---|
| easy (D≈1.6, τ2.5%) | 5/30 = **17%** [7,34] | 7/30 = **23%** [12,41] | — |
| M7 baseline (D≈4.6, τ2.5%) | 1/75 = 1% [0,7] | 6/75 = **8%** [4,16] | er 57 / g3 49 |
| hardened control (τ1.5%) | 1/25 = 4% [1,20] | **0/25** [0,13] | er 20 / g3 20 |
| n=2 composite (τ1.5%) | **0/30** [0,11] | **0/30** [0,11] | g3 10 best |
| n=3 composite (τ1.5%) | **0/25** [0,13] | **0/25** [0,13] | both 0/200 |

Easy rung, text modality: 8B 4/30 = 13%; 32B 4/21 = 19% (n=21/30 at time of writing).

## 5. What it says

**The cliff is a property of the task, not the model.** Both models produce signal only on the two
τ=2.5% rungs and score exactly zero across all three τ=1.5% rungs — **0/160 combined**. Scale lifts
the easy rungs a few points and moves nothing below them.

**Scale helps on one rung, and does not generalise.** The 32B is clearly better on the M7 baseline
(8% vs 1%, non-overlapping intervals) and modestly better on the easy rung (23% vs 17%, overlapping).
But on the hardened control it scores **0/25 against the 8B's 1/25** — the ordering inverts, both at
noise level. "4x the parameters helps" is true of exactly one cell.

**The frontier gap is widest where the task is simplest.** On the hardened control — a SINGLE fault,
no composition, no multi-part reasoning — both Gemini models score 20% and both Qwens score 0–4%.
Whatever the API models do to estimate a magnitude from a rendered view, neither open model does it
at either size. This is the central negative result of the ladder.

**Modality: the 32B closes the text gap.** 22–19% on text against 23% on image, where every prior
result had text strictly worse (M4 composite, M6's 0/120, M7, and the 8B here at 13% vs 17%). Held
loosely at n=21, but it suggests the symbolic channel becomes usable once the model can parse the
coordinate tables, rather than being a bad observation format per se.

**`ever_simulated_a_pass` tracks the success rate exactly on every cell.** These are search failures,
not commit-policy failures: the models never produce a passing state to commit.

## 6. Implication for Stage-2

The only rung with a trainable signal is `instances_easy` — deliberately built so the model's
existing step size roughly suffices — and it is the same rung for both models. So:

- **SFT the 8B.** The 32B clears nothing the 8B does not, costs 4x the compute, cannot be fine-tuned
  on 2x48 GB, and its bf16 weights do not fit on the disk.
- **Do not buy a bigger open base.** The slope from 8B to 32B recovers roughly an eighth of the
  distance to the API models on one rung and none of it on the others.

## 7. Blocking item before any SFT

`instances_easy.jsonl` is **19 train-split shapes and 11 test-split shapes, mixed**, one instance per
base, n=30. Training on oracle traces drawn from these instances and evaluating on the same set would
leak, invisibly. Before Stage-2 it needs a **shape-level split** (train shapes → trace pool, test
shapes → held-out eval) and multiple instances per shape for n; at n=30 the 8B's 17% carries a CI of
[7,34] that overlaps random's [1,17], which is too loose to measure a post-SFT delta against.

The generator already supports this: `build_control` seeds on `(base, ctype, seed)`, so varying the
seed yields genuinely different corruptions per shape. Two changes needed — relax the distinct-bases
assertion for multi-instance sets, and add a split filter.
