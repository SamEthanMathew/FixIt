# Stage-2: Supervised Fine-Tuning

> **SUPERSEDED 2026-08-18 by [`STAGE2_ASTRO_PLAN.md`](STAGE2_ASTRO_PLAN.md).** Three commits landed
> after this was written (`ece5a80`, `72795dd`, `c852058`) and invalidate its premise: Qwen3-VL-8B is
> at 11/30 image / 7/30 text under `one_error_search`, not 0–1/30, and the magnitude gate described
> in §1 and §12 is closed (ratio 1.00x, not 0.15x). Its §5 gold target — `SIMULATE <gt_fix>` at every
> turn — is ASTRO's *Direct-SFT control* and is demoted to ablation 1. See §8 of the new plan for the
> full list of what carries over. Kept for the record.

**Status:** plan only — not implemented.
**Date:** 2026-08-16
**Supersedes:** `Fixit_RL.pdf` §6 (model choice) — see "Divergence from the proposal".

---

## 1. Why Stage 2

`Fixit_RL.pdf` defines three stages: (1) off-the-shelf baseline, (2) SFT on traces, (3) RL.
**Stage 1 is complete, and its result is what makes Stage 2 necessary.**

On std30 — 30 single-fault problems, 30 distinct fridges, τ = 1.5%:

| condition | solved |
|---|---|
| robotics-er-2 (image) | 19/30 |
| gemini-3.1-pro (image) | 16/30 |
| **Qwen3-VL-8B (image)** | **0–1/30** |
| oracle / broken-as-given | 30/30 · 0/30 |

Prompt engineering on the 8B is exhausted. Format compliance was fixed (parse errors 203 → 4), image
delivery verified behaviourally, an axis→image legend added, a mislabelled size column corrected, and
worked examples balanced. Success moved 0/30 → 1/30.

### The bottleneck is diagnostic, and it is measured

Scoring every emitted action against ground truth:

| | right part | right TYPE | right AXIS | all three | magnitude |
|---|---|---|---|---|---|
| Qwen3-VL-8B | 70% (= chance) | **39%** (chance 33) | **36%** (chance 33) | 9% | 0.15–0.57× |
| robotics-er-2 | 79% | 62% | 61% | 43% | 1.01× |

The model is guessing which of translate/rotate/scale is wrong and along which axis. There is a
**second independent gate**: conditional on naming the right (op, part, axis), its magnitude is also
at chance — 0/29 such turns passed, against robotics-er-2's 47%.

`solved = P(diagnosis) × P(magnitude | diagnosis)`, and both factors are coins.

SFT is the right lever precisely because it supplies what in-context prompting cannot: paired
(rendered view → correct diagnosis) supervision. **Whether that transfers is an empirical question,
and this plan is built to answer it cleanly — including in the negative.**

---

## 2. The insight that shapes the whole design

Every std30 run uses `contract: batch, max_actions: 1`. In `env.py:231-233`, a batch action **is**
the whole candidate, applied **fresh to the original broken object** — attempts do not stack.

> **Therefore the correct action is identical at every turn of an episode, regardless of what the
> model did before.**

This collapses the hard part of multi-turn SFT. Recovery examples need no per-state search: after any
failed attempt, the gold response is still `gt_fix`. Targets are correct by construction, and already
simulator-verified per instance by `instances_hard.oracle_roundtrip` (`instances_hard.py:108`).

---

## 3. Decisions

| decision | choice | reason |
|---|---|---|
| Base model | **Model-agnostic**, default `Qwen/Qwen3-VL-8B-Instruct` | Swappable via config; see §8 |
| Fault scope | **Single-fault only** | Matches std30 and the measured bottleneck exactly |
| Held-out split | **By base object** | No fridge seen in training appears in eval |
| Method | **LoRA**, ViT frozen | Fits in ~21 GB; full FT is unnecessary and destabilises the tower |

---

## 4. Phase 0 — Unblock (cheap; two of these are blockers)

1. **Eval statistical power.** `EXPERIMENT_2026-08-11_qwen_scale_ladder.md` §7 flags this and it is
   still live. At n = 28 held-out, Wilson 95% for 17% is [8, 36] and for 30% is [15, 47] — fully
   overlapping. A moderate SFT gain would be **unmeasurable**. Build a held-out set of **n ≥ 90**
   (13 test shapes × ~7 seeds × 3 fault types) via `instances_hard.build_control`, chaining disjoint
   seeds (ids embed the seed, so `--seed 0, 6, 12…` do not collide).

   | n | 17% | 30% | 40% |
   |---|---|---|---|
   | 28 | [8, 36] | [15, 47] | [24, 58] |
   | 90 | [11, 27] | [22, 40] | [30, 51] |

2. **Disk.** `/` is **97% full, 66 GB free**; `/data` is not writable by us. Every generated instance
   writes a permanent `_hard_*.urdf` into `assets/partnet_mobility/<base>/` (146 already present).
   Budget this and add cleanup for rejected candidates before generating ~1k instances.

3. **Fix `perception_probe.py:133`** — `CALL.search(inst.get("gt_fix"))` raises `TypeError`; `gt_fix`
   is a **dict**, not a string. Use `inst["faults"][0]["spec"]`.

4. **Baseline the probe** pre-SFT on Qwen3-VL-8B and Gemini, for a reference line.

---

## 5. Phase 1 — Data generation

New module: `text_fixit/sft/build_dataset.py`.

### Instance pool

Train from the **30 train-split shapes only** (`data/fridge_ids.json`: 30 train / 13 test, split by
shape); eval from the 13 test shapes. Target ~600–900 train instances.

`--set easy` caps at ~180 per type per seed (`instances_hard.py:466`), so chain seeds.
`instances_easy75.jsonl` already demonstrates the pattern: 75 instances, 26 bases, 3 per base,
train/test base overlap **0**.

### Four example types

| type | prompt state | target action | teaches | mix |
|---|---|---|---|---|
| **Direct** | turn 1 (annotated view + broken view) | `SIMULATE <gt_call>` | the diagnosis itself | 40% |
| **Recovery** | turn *k* after a deliberately wrong prior attempt | `SIMULATE <gt_call>` (identical) | not perseverating on a wrong hypothesis | 40% |
| **Commit** | after a passing SIMULATE | `COMMIT <gt_call>` | the pass→commit protocol | 15% |
| **No-fix** | healthy URDF | `COMMIT NO_FIX()` | not damaging a working object | 5% |

Wrong prior attempts come from a **controlled taxonomy** — wrong axis, wrong sign, wrong type,
magnitude too small, magnitude too large — so recovery coverage is balanced rather than incidental.
This maps onto `Fixit_RL.pdf` §7 ablations 1–4 (final-answer-only → traces with failed branches →
traces with explicit backtrack labels).

### Response format

Reuse `agents/qwen_vl.py:38 _normalize()` — its docstring already states that the canonical
`<think>…</think>[<backtrack/>]<act>…</act>` shape exists *for this SFT stage*. Action text from
`action_parser.format_call(spec, pid)` (`action_parser.py:50`), proven sufficient by the per-instance
oracle round-trip gate.

### Reasoning text: templated from ground truth, not distilled

Compute the real numbers and state the diagnostic chain explicitly:

> *"P1 is mis-sized: its Y extent is 2.53 m against the body opening's 1.85 m, a ratio of 1.37, so
> scale Y by 0.73."*

Deterministic, correct by construction, and it teaches exactly the part → type → axis → magnitude
chain that is failing. **Do not distil Gemini traces** — its reasoning is frequently post-hoc and
cannot be verified.

### Magnitude precision

Round gold magnitudes to **3 significant figures**. Tolerance is ±1/D ≈ ±14% at median difficulty,
so `format_call`'s `%.5f` is label noise that costs tokens and teaches spurious digits.

### Prompt rendering must be byte-identical to eval

Call `GeminiAgent._system_prompt(env)` / `._step_prompt(env, obs, budget_left)` directly against a
real `FridgeRepairEnv` — that is literally the code path `agent.act` uses.

**Pin `FIXIT_PROMPT_SET`, `FIXIT_PROMPT_VARIANT`, `FIXIT_TAU_FRAC=0.015`, `FIXIT_THINKING_BUDGET`.**
`safe_substitute` ships an unresolved `$var` silently into training data — this has already happened
once in production (`prompts/README.md:59-61`).

### Sharp edge

Candidate URDF filenames must be **unique per evaluation**. PyBullet caches parsed geometry by
filename; reuse silently freezes `closes`/`collides` while `deviation` keeps updating (defect D2,
`audit_validity.py:19`). Replicate the `_eval_seq`/`_tok` scheme.

### Output

JSONL in TRL vision-conversational format + images on disk. ~2,500–3,500 examples.

---

## 6. Phase 2 — Training

New module: `text_fixit/sft/train_lora.py`, plus `prepare_env.sh`.

### Environment

**Neither existing env can train** — both lack `peft`, `accelerate`, `datasets`, `trl`.

- Clone `qwenvl` (already correct: torch 2.9.1, transformers 4.57.6; `Qwen3VLForConditionalGeneration`
  imports cleanly) → add `peft accelerate datasets trl liger-kernel` (~200 MB).
- **Do not touch `fixing`** — its torch 2.5.1+cu121 pin is load-bearing for the compiled point-cloud ops.
- **Do not source-build flash-attn** (20–40 GB transient on 66 GB free). Use `sdpa`, or a prebuilt
  FA2 wheel — RTX 6000 Ada is SM 8.9, so **FA2 only, never FA3**.

### Configuration

| setting | value | why |
|---|---|---|
| LoRA | r=16, α=32, LLM linears **named explicitly** | `target_modules="all-linear"` silently adapts the vision tower and re-enables its activation graph |
| Vision tower | frozen | Saves 3–5 GB; tuning it destabilises features without a large multimodal corpus |
| `max_length` | **10240** | p50 3,888 / p99 8,117 recorded prompt tokens; 768×768 → **576 image tokens** |
| Batch | bs=1 + grad accum, grad-checkpointing on, bf16 | |

**Truncation that clips an image span is the most common failure in this stack** — it produces
`Image features and image tokens do not match`. Do not set `max_length` to the default 4096.

### Memory (measured arithmetic, not estimated)

weights 16.33 GiB + LoRA/optimizer 0.7 + activations 2.2 + fused-CE 0.1 + ctx 2.0 ≈ **21 GB**
(~26 GB with naive cross-entropy). Comfortable on a 48 GiB card.

### GPU allocation

- **GPU0**: our vLLM server (29.4 GB, pre-allocated) + desktop (~1.4 GB).
- **GPU1**: **another user's job** (13.5 GB, can grow under us).

**Stop vLLM and train on GPU0.** SFT and eval are sequential phases, the server restarts in ~2 min
from `serve_qwen.sh`, and it removes the co-tenancy risk entirely. Set
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

### Non-negotiable checks before any full run

1. `model.print_trainable_parameters()` — confirm the ViT is untouched.
2. Labels `-100` on all prompt tokens **and** every `image_token_id = 151655` placeholder.
3. **Overfit 32 samples to near-zero loss.** If it cannot, the collator or masking is wrong — not the LR.
4. One forward+backward with `q_proj`/`k_proj` in `target_modules`, to settle a reported (unconfirmed)
   interaction with Qwen3's QK-norm. 30 seconds; drop q/k if it errors.
5. Save the processor alongside the adapter, or inference rebuilds a different chat template.

---

## 7. Phase 3 — Evaluation

Reuses the existing harness unchanged: serve the adapter with vLLM, run
`run_trials.py --agent loop_qwen --model <path>`.

Report the `Fixit_RL.pdf` §7 metrics — success rate, sims per solved episode, **recovery rate after a
wrong first fix**, repeated-failure rate, invalid-action rate — plus the two that measure the actual
bottleneck:

- **`funnel.py`** — part / type / axis / all-three against chance. **This is the primary endpoint.**
  If axis% does not clear 33%, SFT has not fixed perception, whatever the success rate does.
- **`perception_probe.py`** — single-turn diagnosis, isolating perception from search and format.

Held-out shapes only, n ≥ 90. Also re-run std30 for continuity, reporting its 11 test-split instances
separately, since its 30 bases span both splits (19 train / 11 test).

---

## 8. Model-agnostic design, and the Qwen3.8-27B option

The base model is a config value. Everything above holds for any OpenAI-compatible VLM the harness
can serve; only `prepare_env.sh` and the LoRA target-module names are model-specific.

**Qwen3.8-27B** (evaluated 2026-08-16) is a genuine candidate:

| | Qwen3-VL-8B (current) | Qwen3.8-27B |
|---|---|---|
| Vision input | yes | **yes** — `vision_config` in config.json, `Qwen3VLProcessor`, pipeline `image-text-to-text` |
| Architecture | dense 8.8B | dense 27.78B, hybrid (3 Gated-DeltaNet : 1 full attention), 64 layers |
| Size on disk | 17 GB | **55.6 GB BF16 / 30.9 GB FP8** |
| Context | 32k served | 262k native |
| Licence | Apache-2.0 | Apache-2.0 |
| Serving | vLLM 0.16.0 ✓ | **needs vLLM ≥ 0.17.0** — our env has 0.16.0 |

Notes that matter:
- It reuses the **same processor family** as Qwen3-VL, so the existing `image_url` harness transfers
  unchanged.
- There is no "Qwen3.8-VL": the mainline absorbed the VL line at Qwen3.5.
- The 2.4T **Max** open weights are **text-only** (`license: other`) — do not confuse the two.
- BF16 (55.6 GB) does **not** comfortably fit 66 GB free disk; FP8 (30.9 GB) does.
- Vision scores are **vendor self-report with no independent replication** (ERQA 65.5). ERQA is the
  closest published proxy to our task, and it still says nothing direct about naming the axis of a
  3 cm translation in a render.

**Recommended sequencing:** run `perception_probe.py` against a hosted Qwen3.8 endpoint on our actual
renders *before* downloading 31–56 GB. That is a direct test of the bottleneck for near-zero cost. The
repo's own precedent is that 4× parameters (8B → 32B) bought **nothing** on this rung (0/25 vs 1/25),
so the burden of proof is on the new model.

---

## 9. Phase 4 — On-policy round 2 (DAgger), if round 1 shows signal

`Fixit_RL.pdf` acknowledges the turn-*k*-depends-on-turn-*k−1* problem only obliquely and offers no
solution. Round 1's synthetic wrong attempts are **off-policy** — they are not the states the model
actually reaches.

Round 2: roll out the round-1 model on train shapes, take the states it genuinely produces, relabel
each with the gold action, retrain. This is the standard fix for distribution shift, and it is cheap
here **because the gold label is state-independent** (§2).

---

## 10. Divergence from the proposal

`Fixit_RL.pdf` §6 recommends starting text-only with Qwen2.5-7B / Qwen3-8B, and treats "rendered
object views + Qwen-VL" as a §9 stretch goal. The implementation is already past that point — it is
PyBullet with rendered views and Qwen3-VL. This plan keeps §5.2 (trace content: failed attempts,
state feedback, backtracking, final success) and §7 (metrics and ablations) and supersedes §6.

---

## 11. Verification

1. `build_dataset.py --limit 5 --dry-run` → inspect 5 rendered prompts and targets by eye; grep for
   unresolved `$vars`; confirm every target parses via `action_parser.parse`.
2. Re-verify a 20-example sample end-to-end in PyBullet: applying the target must PASS.
3. Overfit 32 examples; loss → ~0.
4. Pre/post `perception_probe.py` and `funnel.py` on held-out shapes.
5. Full `run_trials.py --sweep` on the held-out set; compare to the pre-SFT baseline with Wilson
   intervals.

---

## 12. Risks, stated honestly

- **SFT may teach output priors rather than perception.** The model could learn the marginal
  distribution of gold actions without ever reading the image. *Detection:* the probe and funnel
  measure diagnosis directly, and the held-out-shape split catches memorisation. **A null result here
  is a real finding and should be reported as one.**
- **Statistical power** — mitigated by Phase 0 item 1. Do not skip it to save time; without it the
  experiment cannot conclude anything.
- **Disk at 97%** — the binding physical constraint.
- **Another user's job on GPU1** — avoided by training on GPU0 with vLLM stopped.
- **Two gates.** Even perfect diagnosis leaves magnitude at chance. **Expect the funnel to move before
  the success rate does, and treat that as progress rather than failure.**
