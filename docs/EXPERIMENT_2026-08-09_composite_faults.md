# Experiment — Composite-Fault Hard Benchmark

**Date written:** 2026-08-09 (predictions below are pre-registered — recorded before any model was run)
**Author:** FixIt / Stage-1 closed-loop repair
**Code state:** `text_fixit/` at the commit recorded in each run's `manifest.json`

---

## 1. Why this experiment

The single-fault fridge-repair benchmark has stopped discriminating. Under the current standing
baseline (deviation OFF, budget 10, 25 instances per fault type):

| model | text | image |
|---|---|---|
| gemini-3.1-pro | ~41% | 49% |
| gemini-robotics-er-2 | 33% | 57% |

Two things are wrong with that regime.

**The loop is not load-bearing.** Successes arrive in a *median of one* SIMULATE (gemini-3.1-pro,
image; solved-episode range 1–6). A task solved on the first probe is one-shot regression over a
single `(type, part, axis, value)` tuple, not a sequential decision problem. There is nothing for
planning, credit assignment, or feedback to do — and therefore little headroom for a trained policy
to beat an off-the-shelf model.

**Part of the recent jump was a freebie.** Corruption magnitudes were sampled ON a discrete grid
(`grids.snap`) while the agent's action space had been made continuous, and the tolerance τ was a
loose 2.5% of the door's bbox diagonal. A model that recalls a plausible grid bin can land inside
tolerance without estimating anything.

This experiment makes the task hard along both axes at once, and — critically — is designed so the
two causes can be told apart afterwards.

## 2. What changed

### 2.1 Hardening knobs (applied to every new instance)

| knob | before | after |
|---|---|---|
| corruption magnitudes | on-grid (`grids.snap`), grown one grid step at a time | **continuous**, grown ×1.12 (`corruption.sample_corruption(continuous=True)`) |
| tolerance τ | 2.5% of door bbox diagonal (~20 mm) | **1.5%** (~12–29 mm), via `FIXIT_TAU_FRAC=0.015` |
| part table | shows `role` + `fixable=yes/no` | **both columns hidden** (`build_part_table(reveal_fixable=False)`) |
| rendered views | each door a distinct palette colour, yaw −45° | **all doors one neutral grey**, yaw +35° (`closed_view(hard=True)`) |

The labelled reset view keeps its distinct palette — it is the only grounding for the `P#`
vocabulary — so the agent must carry part identity across from the reference view by position rather
than colour. Flat recolouring is retained in hard mode: PartNet's own materials render near-black
under the tiny renderer, so removing it would make the views illegible rather than harder.

Two generator bugs were fixed while writing the new sampler:
- the corruption RNG seed omitted the base shape id, so all 36 fridges drew the *same* stream for a
  given `(link, ctype, index)` — 17% of the old instances were exact duplicate corruptions;
- scale always used the largest-extent axis, putting ~78% of scale faults on axis 1. Now 15/10.

### 2.2 Composite faults

`data/instances_hard.jsonl` — **25 instances, 25 distinct fridges**, each with **exactly 3
sub-faults** (one translate, one rotate, one scale):

- **10 × `composite_1door`** — all three on a single door
- **15 × `composite_2door`** — the three split across two doors (2 + 1)

Sub-fault *count* is held at 3 in both arms, so the only difference between them is the
diagnosis/assignment burden, and both need the same minimum number of actions.

`data/instances_control.jsonl` — **25 single-fault instances, 25 distinct fridges**, under the same
hardening knobs. This is what separates "the knobs got harder" from "composition got harder".

### 2.3 Two action contracts

The composite task cannot be expressed as one `(type, part, axis, value)` tuple, which forces a
choice about what an action *is*. Both options are built and both are run:

- **`batch`** — a turn carries an ordered LIST of up to 6 actions, applied in order to a fresh copy
  of the original broken object. Attempts never stack, so every turn must be the complete repair.
  The agent must plan all three magnitudes before seeing feedback on any of them.
- **`stack`** — one action per turn, applied on top of a persisted working state (the MDP framing).
  `RESET()` discards the working state (costing a budget step) so a bad step is recoverable; a bare
  `COMMIT` commits the working state as-is.

The two share every prompt line except one swapped `$contract_block`
(`prompts/contract_batch.txt` / `contract_stack.txt`); verified by diff — everything above
`ACTION SPACE` is byte-identical.

Both sets use the same fault hint, which names the fault vocabulary without leaking the count or
which doors: *"One or more parts may be faulty, and a faulty part may have more than one thing wrong
with it — its position, its orientation and its size can all be wrong at once."*

## 3. Why the composite task is still exactly solvable

Each URDF edit is exactly invertible given its pivot, and `canonical.part_centroid` /
`canonical.scale_pivot` are recomputable from current geometry. So for a break applied as
`[c1, c2, c3]`:

> **`gt_fix_sequence` = the corruption list REVERSED, each spec inverted.**

Applied in that order, each inverse acts on exactly the state its forward op produced.

**One ordering constraint is required, and it was found the hard way.** `corruption._edit_scale`
multiplies the `<mesh scale>`, which acts in the *mesh* frame — *before* the visual origin's `rpy`.
Once a rotation has put a non-zero `rpy` on a part, scaling "axis 1" no longer scales along
link-frame axis 1 and the pivot compensation stops fixing the link-frame edge; `scale_pivot` then
recomputes a pivot up to **0.13 m** away from the one the break used, and the oracle cannot restore
the part. The generator therefore applies **scale first on each part**, so its inverse runs last —
after every rotation has been undone, on geometry where the pivot is recomputable. With scale first
the recomputed pivot matches to 0.000000.

This is enforced, not assumed: **generation gate 6** replays the fix through the agent's own path
(render → parse → *recompute* canonical params → apply) and rejects any instance whose oracle
round-trip does not PASS. Checking the *stored* specs only proves mathematical invertibility; it
does not prove the inverse is expressible without privileged parameters, which is the property the
whole action space rests on.

## 4. A scoring bug this work exposed

`FridgeRepairEnv` wrote every candidate to the same temp path (`_cand_<id>_<tok>.urdf`). **PyBullet
caches parsed URDF and collision geometry by filename within a client**, so re-loading that path
returned the *first* candidate's bodies: `closes` and `collides` silently froze at their
first-candidate values, while `deviation_mm` (read from the XML by `geom`) kept updating correctly.

Under the single-action contract this was mostly invisible — with one candidate per episode
evaluated once, and ~78% of instances where neither healthy nor broken trips the physical gates, the
frozen values were usually right anyway. It became obvious under `stack`, where three candidates are
evaluated per episode: the oracle scored 92% batch but 64% stack on *identical* final geometry.

Fixed by giving every evaluation a unique candidate filename (`env._eval_seq`). **Caveat for the
earlier baselines:** those runs evaluated up to 10 candidates per episode through the same path, so
their `closes`/`collides` terms were stale after the first SIMULATE. The dominant `within_tol` term
was always correct, so headline numbers are directionally sound, but the ~22% `physics_verified`
subset of those runs should not be treated as precise.

## 5. Run matrix

Models: **`gemini-3.1-pro-preview`** (note `gemini-3-pro-preview` returns 404 "no longer available")
and **`gemini-robotics-er-2-preview`**. Deviation **OFF**, budget **10**, thinking dynamic, full
per-episode context.

| set | n | contract | modality | models | episodes |
|---|---|---|---|---|---|
| composite hard | 25 | batch + stack | text + image | 2 | **200** |
| single-fault control | 25 | batch only¹ | text + image | 2 | **100** |
| oracle | 25 + 25 | batch + stack | text | — | local |
| random | 25 + 25 | batch + stack | text | — | local |

¹ For a one-action fix `stack` and `batch` are the same contract, so running both is redundant.

`max_output_tokens` was raised 8192 → 32768: on composite instances gemini-3.1-pro was observed
spending ~15.7k thought tokens in a single turn, which starved the visible `<act>` and returned
empty / `MALFORMED_FUNCTION_CALL`. The prompts also now state explicitly that the action is literal
text and not a tool call.

## 6. Metrics

Per condition, and broken out by `level` (`composite_1door` / `composite_2door` / `control_single`)
and by contract: success rate (terminal PASS), mean score, tries-to-submit (mean/median/range),
commit precision, recovery rate, repeated/invalid action rates, resets per episode (stack), mean
actions per turn (batch), and per-part terminal deviation.

**Success** = every faulty part within τ **and** every faulty door closes **and** no part-collision
above the healthy baseline (`evaluation.evaluate_repair_multi`; worst-part aggregation —
`deviation = max_i`, `score = min_i exp(-dev_i/τ_i)`).

## 7. Pre-registered predictions

Written before any model run; recorded here so the results can refute them.

- **H1 — composition dominates.** Composite success falls below 20% for both models, from the 40–57%
  single-fault baseline.
- **H2 — `stack` beats `batch`** for the stronger model: per-step feedback makes credit assignment
  tractable, where batch must commit to all three magnitudes blind. Risks to watch: error
  accumulation, and budget wasted on `RESET`.
- **H3 — two-door < one-door**, isolating the assignment burden at constant sub-fault count.
- **H4 — the control set drops only modestly** (to ~25–40%), showing the hardening knobs are a real
  but secondary contributor, and that H1's drop is genuinely compositional.
- **H5 — the image advantage narrows or inverts** on composite: three superimposed defects in one
  closed view are much harder to disentangle than one.

## 8. Validation performed before running any model

All logged to `runs/_analysis/verify_hard.{log,json}`.

| gate | result |
|---|---|
| invertibility — `gt_fix_sequence` restores every faulty part | 50/50, max deviation **0.000000 mm** |
| necessity — dropping any one fix leaves ≥3τ residual | 25/25, min residual **3.02τ** |
| off-grid magnitudes | 50/50 |
| distinct bases per set | 25/25 and 25/25 |
| `tau_frac == 0.015` | 50/50 |
| part table hides `fixable`/`role` | confirmed by diff |
| contract prompts differ only in `$contract_block` | confirmed by diff |
| **oracle** (both sets × both contracts) | **100%** |
| **random** (both sets × both contracts) | 0–4% |

## 9. Logging

Every run writes, under `runs/<cond>/<agent>/`: `manifest.json` (model, contract, modality, τ, git
commit, instance sha256, versions, timings), `records.jsonl` (per episode), `turns.jsonl` (per model
turn: verbatim reasoning, verbatim raw output, parsed actions, per-part evaluation, latency, token
counts), `prompts/` (exact text sent each turn), `images/` (every view actually sent), `raw/` (API
response metadata and retries), `errors.jsonl`, and `trajectories/<id>.md` (readable rollouts).
All append-and-flush, so a killed run keeps everything up to that point.

## 10. Results

*To be filled in when the matrix completes. Predictions in §7 are frozen as of 2026-08-09.*
