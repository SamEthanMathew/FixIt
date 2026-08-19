# ASTRO-style SFT on Text-FixIt: training report and results

**Date:** 2026-08-19 (training ran overnight 08-18 → 08-19)
**Question:** does SFT on search traces — failed probes, backtracking, recovery — improve a
Qwen3-VL-8B agent's ability to repair broken fridges in the closed loop?
**Method:** `docs/STAGE2_ASTRO_PLAN.md` (ASTRO, arXiv:2507.00417, adapted to a continuous action
space). Pipeline hardened by the adversarial review in that plan's §8b before anything ran.
**Status:** complete — both arms trained and evaluated. Headline: **base 6.7% → direct-SFT 36.5% → astro-SFT 78.1%** on held-out shapes.

---

## 1. Setup in one paragraph

The agent repairs a broken PartNet-Mobility fridge in PyBullet by proposing one
`TRANSLATE/ROTATE/SCALE(part, axis, value)` per turn; each action applies fresh to the broken
object, the simulator reports the residual error in mm, and the episode PASSes only if the faulty
part lands within tolerance (τ = 1.5% of the door diagonal), the door still closes, and nothing
interpenetrates. Budget: 10 SIMULATEs, then commit. The model is `Qwen/Qwen3-VL-8B-Instruct`
served by vLLM, prompted with the `one_error_search` set (text modality, deviation on, stateless
window3). Pre-SFT baseline on the std30 dev benchmark: **7/30 text**.

## 2. Training data

Built by a deterministic expert (no LLM anywhere in data generation) that runs the prompt's own
search procedure — probe each part, sweep (operation, axis) cells, flip the sign when the error
rises, refine by `V·A/(A−B)` — reading only simulator observations, never ground truth. Trees are
linearized ASTRO-style (failed branches merged before the passing terminal; ancestor jump =
backtrack) and verbalized with ASTRO's reflection phrases plus the `<backtrack/>` tag.

| | value |
|---|---|
| train instances | 300 (100/fault type), **25 train-split shapes only** |
| held-out instances | 105 (35/type), **11 test-split shapes, seed 100** (disjoint from every dev set) |
| held-out difficulty | D = deviation/τ: min 3.0, median 6.1, max 18.4 |
| valid trees (expert solves) | 233/300 (78%; ASTRO's own yield was 68%) |
| traces (astro arm) | 898 = 233 direct (k=0) + 665 search (k≥1) + **66 budget-exhaustion aux** |
| examples (astro arm) | **5,346** turns; 898 carry `<backtrack/>` (204 `part_selection`) |
| examples (direct arm) | **531** turns from the same 233 trees — clean: winning cell only, no failures, no flips |
| tokens | max 3,310/example → `max_length` 4096, zero truncation |

Supervision-quality gates, all verified on a full build: COMMIT targets byte-match the prompt's
own `found_note` demand 101/101; off-procedure probe orderings 0/96; no-op `SCALE(…,1.0)` probes 0;
"exactly as before" rounding mismatches 0; every target parses under the live harness's own
parser including `ruled_out` enforcement (0 rejects).

## 3. What each arm tests

- **astro arm** — traces *with* failed branches, reflection language, `<backtrack/>` labels, and
  budget-exhaustion examples. This is Fixit_RL §7 ablation 4.
- **direct arm** — clean correct-path-only traces from the *same trees*, steps-matched by epochs
  (531 × 10 ≈ 5,346 × 1). This is ASTRO's Direct-SFT control / Fixit_RL ablation 2.
- Both against the **base model**, all three evaluated on the same 105 held-out instances,
  3 sampling seeds each (temperature 0.7), same server, same prompts.

## 4. Training configuration

| | |
|---|---|
| method | LoRA r=16, α=32, dropout 0.05, on all 252 language-tower linears (7 suffixes × 36 layers); vision tower excluded and frozen (verified: 0 trainable vision params) |
| trainable | 43.6M / 8.81B = 0.495% |
| loss | completion-only (prompt masked); ASTRO's no-masking kept as an unused ablation flag |
| schedule | 1 epoch (astro) / 10 epochs (direct, steps-matched), AdamW, cosine, LR 1e-4, warmup 3% |
| batch | bs 1 × grad-accum 8; bf16; grad checkpointing; sdpa attention; max_length 4096 |
| hardware | 1× RTX 6000 Ada (GPU0), ~26 GB resident, ~15.3 s/step |
| val split | by *shape* (never by turn) — 5% of bases held out for eval_loss |

**Overfit gate** (required before any real run): 32 examples, 30 epochs → loss 1.57 → 0.003,
token accuracy 99.8%. Collator, masking, and adapter wiring confirmed correct.

## 5. Training results

| | astro arm | direct arm |
|---|---|---|
| steps | 639 | 640 |
| wall time | 2 h 46 m | ~2 h 55 m (incl. a crash + resume, §6) |
| final train loss | ~0.02 (avg 0.074) | **0.0025** |
| **eval_loss, held-out shapes** | **0.0216** | **0.133** |
| val token accuracy | 99.1% | 97.4% |
| wandb (r-pad/fixit-astro-sft) | `aaoeenpm` | `9rayeuxa` (steps 0–448) + resumed run (448–640) |
| adapter | `text_fixit/runs_sft/astro_qwen8_text` | `text_fixit/runs_sft/direct_qwen8_text` |

The pre-eval headline: the direct arm fits its data **8× harder** (0.0025 vs 0.02) yet
generalizes **6× worse** across geometry (eval_loss 0.133 vs 0.022). Same trees, same step count —
the only difference is whether the traces contain failure and recovery. A memorize-vs-learn
signature, though the val split is small (1–2 shapes); the env sweeps below are the real test.

Loss-curve caveat, stated before results were known: the traces are heavily templated, so ~99%
token accuracy is mostly template recall; the decisive tokens (part id, operation, axis, sign,
magnitude digits) are a small minority that token-level metrics cannot isolate. Success rate and
the funnel are the endpoints.

## 6. Incidents (for the record)

1. **Shared-env collision.** At 23:24, a robometer-related process on this box (same account,
   `~/Code/tup-b9/`) ran a package sync in the `qwenvl2` conda env that *removed* `trl` and
   downgraded `datasets` under the live direct-arm run; it crashed at the epoch-8 checkpoint
   save. Repaired (`trl==1.10.0`, `datasets==5.0.1`), `--resume` added to `train_lora.py`, resumed
   from checkpoint-448 — ~50 min lost, no data loss. The same neighbor later took port 8001, which
   the serving preflight caught; evaluation moved to port 8003. Recommendation: a dedicated
   `fixitsft` env before the next training run.
2. **wandb key** was truncated on first paste (36 < 40 chars); the astro run logged offline and
   was synced afterwards — full metric history preserved.

## 7. Held-out evaluation — final results (astro vs base)

Protocol: 105 held-out instances (11 test-split shapes, seed 100, never seen by training or by any
prompt iteration) × 3 sampling seeds × arm, all against one vLLM process serving the base and the
adapter, so the arms differ in nothing but the weights. 630 episodes.

### Success rate

| seed | astro SFT | base |
|---|---|---|
| r1 | 82/105 (78%) | 9/105 (9%) |
| r2 | 83/105 (79%) | 7/105 (7%) |
| r3 | 81/105 (77%) | 5/105 (5%) |
| **pooled** | **246/315 = 78.1%** | **21/315 = 6.7%** |

**+71.4 points.** Paired McNemar over the 315 shared (instance, seed) pairs: **astro-only wins
225, base-only wins 0** — not a single episode anywhere that the base solved and the adapter did
not — χ² = 223, p ≈ 0. The effect is uniform across shapes, not carried by a few: per-shape success
59–93% (median 77%) for astro vs 0–23% (median 4%) for base.

### By fault type (pooled)

| | translate | rotate | scale |
|---|---|---|---|
| astro | **105/105 (100%)** | **86/105 (82%)** | **55/105 (52%)** |
| base | 12/105 (11%) | 7/105 (7%) | 2/105 (2%) |

Scale remains the hardest type — mirroring both the expert's own weakness (7/10 valid scale trees)
and the deviation-metric local minimum documented in the plan §5. The model inherits its teacher's
profile, at scale.

### The capability funnel (every emitted action vs ground truth)

| run | part% | type% | axis% | all3% | mag ratio | best dev (τ) |
|---|---|---|---|---|---|---|
| chance | ~50 | 33.3 | 33.3 | ~5.6 | 1.00 | — |
| astro (r1/r2/r3) | 94.3–94.5 | 65.4–70.1 | 51.6–54.7 | **40.0–42.1** | **1.00** | **0.12** |
| base (r1/r2/r3) | 87.2–87.8 | 35.8–37.4 | 38.4–40.2 | 14.1–15.1 | 1.09–1.14 | 3.4–4.1 |

Full-diagnosis rate (right part + type + axis in one action) nearly tripled, 14→41%; median
best-achieved deviation went from ~3.7 τ (never close) to **0.12 τ** (well inside tolerance).

### Search behaviour (the Fixit_RL §7 metrics this stage was designed to move)

| | astro | base |
|---|---|---|
| **recovery after a failed first probe** | **234/303 (77%)** | 18/312 (6%) |
| sims per solved episode (mean/med) | 5.1 / 5 | 5.4 / 5 |
| `<backtrack/>` tags emitted at eval | 621 | 0 |
| parse errors per run | 2–4 | 3–8 |

Recovery rate is the headline behavioural change: the base almost never converts a wrong first
hypothesis into a solve; the SFT model does so 77% of the time — precisely the capability the
failed-branch traces supervise. The trained model also *uses* the backtrack grammar unprompted
(621 tags across 315 episodes; the base emits none).

### Reading the result

- The astro arm's 78.1% matches the expert's own 78% coverage almost exactly: SFT cloned the
  search procedure roughly to its teacher's ceiling. Further gains likely require a better expert
  (the scale local-minimum fix) or RL — which now has a real search prior to amplify.
- The power worry from the review (§8b) is moot at this effect size: +71 points against a
  detectability floor of ~+18–33.
- Contamination is excluded by construction: held-out shapes were never trained on, and seed-100
  corruptions are byte-disjoint from every set prompt engineering ever touched.

### The direct arm — and the dissociation that explains everything

Steps-matched clean-traces control (ASTRO's Direct-SFT): 33/41/41 across seeds =
**115/315 = 36.5%**. The three-way ordering is unambiguous —

| | base | **direct SFT** | **astro SFT** |
|---|---|---|---|
| success (pooled, n=315) | 6.7% | **36.5%** | **78.1%** |
| translate | 11% | **16%** | **100%** |
| rotate | 7% | **19%** | **82%** |
| scale | 2% | **74%** | 52% |
| recovery after failed 1st probe | 6% | 27% | **77%** |
| sims per solve | 5.4 | **2.7** | 5.1 |
| `<backtrack/>` emitted | 0 | 0 | 621 |
| funnel all3% / mag ratio / best dev | 14 / 1.1 / 3.7τ | **60** / 1.2 / 3.2τ | 41 / **1.00** / **0.12τ** |

McNemar astro vs direct: astro-only wins 167, direct-only 36, χ² = 83.

**The per-type inversion is the finding.** The direct arm — trained only on winning actions — is
*better than astro on scale* (74% vs 52%) and near-useless on translate/rotate (16%/19%). Its
funnel shows why: it names the right repair type almost perfectly (type% ≈ 98, all3% ≈ 60 — higher
than astro's 41!) and commits fast (2.7 sims), but its magnitudes are off (ratio 1.15–1.34, best
deviation stuck at ~3.2 τ) and it cannot recover when the first shot misses (27%).

The two arms learned two different repair strategies, each matching what its traces contained:

- **Scale faults are *readable***: the size ratio sits in the geometry block, so a clean
  answer-shaped trace teaches "read the ratio, scale by it" — pattern-based repair. Direct excels.
- **Translate/rotate faults must be *measured***: the magnitude only exists in probe feedback
  (the error in mm, the sign flip, the secant step). Clean traces show the final answer with the
  measurement process amputated, so the direct model diagnoses correctly and still misses.
  The astro traces teach the measurement procedure itself — and there, search wins by 5–6×.

This is a sharper version of ASTRO's own Table-4 claim: failed-branch traces beat clean traces
(here +42 points, not +4), *and* the decomposition shows the boundary — the search prior pays
precisely where the answer is not readable from the state and must be obtained by experiment.

### Bottom line

SFT on verifier-grounded search traces took a 7% agent to **78%** on fully held-out shapes and
corruptions, with recovery behaviour (6% → 77%) and calibrated magnitudes (ratio 1.00) that the
same data stripped of its failures does not produce. The astro arm sits at its teacher's ceiling
(expert coverage: 78%), which locates the next gains in a better expert on scale faults and in
RL — for which this model, unlike the base, now has a search prior to amplify.

## 8. How to reproduce

```bash
# data (CPU): text_fixit/astro/make_sets.py + build_dataset.py — see STAGE2_ASTRO_PLAN.md §7
# gate:  train_lora.py --data data/sft/astro_train.jsonl --overfit 32 --epochs 30 --yes
# train: train_lora.py --data data/sft/astro_train.jsonl --out runs_sft/astro_qwen8_text --wandb --yes
# serve: PORT=8003 bash text_fixit/astro/serve_lora.sh text_fixit/runs_sft/astro_qwen8_text
# eval:  QWEN_BASE_URL=http://127.0.0.1:8003/v1 FIXIT_TAU_FRAC=0.015 FIXIT_PROMPT_SET=one_error_search \
#        run_trials.py --agent loop_qwen --model astro --modality text --deviation on \
#          --instances data/instances_astro_heldout.jsonl --sweep --budget 10 --max-actions 1 --run <name>
```
