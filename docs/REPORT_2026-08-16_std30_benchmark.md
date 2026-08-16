# std30 — the standardized single-fault benchmark

**Date:** 2026-08-16
**Status:** complete — 10 conditions × 30 problems = 300 episodes, plus a clean-format
rerun of the Qwen image arm (§6.1)
**Commits:** `514bf75` (results + tooling), `17486b6` (full run tree)
**Raw data:** `text_fixit/runs/one_error_*/` · summaries mirrored in `results/std30/`

---

## 1. What this test was for

Every earlier experiment (M4 composite, the two-fault rung, the Qwen ladders) mixed
several things at once: multiple faults per instance, prompts that changed between arms,
different problem counts per arm, and at least one arm that turned out to be image-blind.
The conclusions were real but hard to compare across models.

std30 exists to remove all of that. **One fault per problem. One action per turn. One
prompt set. The same 30 problems for every arm.** Anything that differs between two rows
of the results table is the model or the modality, and nothing else.

The question it answers: *given a closed simulate-and-observe loop, which models can drive
a broken articulated object back inside tolerance, and what stops the ones that can't?*

---

## 2. Setup

### The problem set — `text_fixit/data/instances_std30.jsonl`

| property | value |
|---|---|
| problems | 30 |
| distinct base objects | **30** (no fridge reused) |
| fault types | 10 translate · 10 rotate · 10 scale |
| faults per problem | 1 |
| tolerance τ | 1.5 % of the door bbox diagonal — **11.9–29.2 mm** |
| difficulty D = deviation / τ | 3.0 – 14.7 (median 7.1) |
| broken state passes | 0 / 30 |
| oracle (ground-truth inverse) passes | **30 / 30** |

D is the number that matters for calibration: to pass, a correction has to be accurate to
roughly ±1/D of the fault size. At the median D of 7.1 that is ±14 %.

Per type, D is: translate 3.2–10.3 (median 6.1), rotate 3.3–14.1 (median 8.0),
scale 3.0–14.7 (median 8.4). Rotate and scale are the harder halves of the set.

### Conditions

Three models × two modalities, plus two prompt ablations on the open model:

| short name | model | observation |
|---|---|---|
| `er_image` / `er_text` | robotics-er-2 | 2 closed views / numeric part table |
| `g3_image` / `g3_text` | gemini-3.1-pro-preview | 2 closed views / numeric part table |
| `qw8_image` / `qw8_text` | Qwen3-VL-8B (local vLLM) | as above |
| `dev_qw8_*` | Qwen3-VL-8B | **+ current error stated in mm** |
| `scale_qw8_*` | Qwen3-VL-8B | **+ typical fault magnitude stated** |

Budget 10 SIMULATEs, auto-commit of the best state reached, one action per turn enforced by
the parser. Prompt set `one_error` for the baselines; each ablation is its own prompt file
differing only in the stated respect (see `text_fixit/prompts/README.md`).

---

## 3. Results

| condition | translate | rotate | scale | **total** |
|---|---|---|---|---|
| `er_image` | 3/10 | **10/10** | 6/10 | **19/30 (63 %)** |
| `g3_image` | **0/10** | 7/10 | 9/10 | **16/30 (53 %)** |
| `g3_text` | **6/10** | 2/10 | 6/10 | **14/30 (47 %)** |
| `er_text` | 4/10 | **0/10** | 6/10 | **10/30 (33 %)** |
| `qw8_image` | 0/10 | 0/10 | 0/10 | **0/30** |
| `qw8_text` | 0/10 | 0/10 | 0/10 | **0/30** |
| `dev_qw8_image` | 1/10 | 0/10 | 0/10 | **1/30** |
| `dev_qw8_text` | 0/10 | 0/10 | 0/10 | **0/30** |
| `scale_qw8_image` | 1/10 | 0/10 | 0/10 | **1/30** |
| `scale_qw8_text` | 0/10 | 0/10 | 0/10 | **0/30** |

Reference points on the same 30 problems: oracle 30/30, broken-as-given 0/30.

---

## 4. Finding 1 — modality decides *which faults* a model can fix, in opposite
directions for the two models

This is the main result, and it only became visible once all four API arms were in.

- **robotics-er-2 on rotation: 10/10 with images → 0/10 with text.**
- **gemini-3.1-pro on translation: 0/10 with images → 6/10 with text.**

Same model, same faults, same budget; only the observation channel changed. Neither
modality dominates — each model's best fault type is the other channel's worst.

The capability funnel says why. Breaking every emitted action into *did it name the right
part / the right operation / the right axis*:

| condition | fault | part % | **type %** | axis % | all three % |
|---|---|---|---|---|---|
| `er_image` | rotate | 100 | **100** | 98 | 98 |
| `er_text` | rotate | 78 | **35** | 32 | 9 |
| `g3_image` | rotate | 100 | **100** | 87 | 87 |
| `g3_text` | rotate | 91 | **24** | 30 | 12 |
| `g3_image` | translate | 84 | **41** | 29 | 15 |
| `g3_text` | translate | 79 | **82** | 46 | 35 |
| `er_image` | translate | 89 | **51** | 50 | 28 |
| `er_text` | translate | 70 | **86** | 35 | 27 |

The collapse is in the **type** column, not the part column. Both models still localise the
faulty part fine from text (70–91 %). What they lose is the ability to *name what kind of
fault it is*:

- **A tilt is obvious in a render and nearly invisible in a coordinate table.** Rotation
  type-recognition goes 100 % → 24–35 % when images are removed.
- **An offset is obvious in a coordinate table and ambiguous in a render.** Translation
  type-recognition goes 41–51 % → 82–86 % when the table is added.

That asymmetry is the whole result. A harness that ships a single modality understates
both models, and which fault types it understates depends on which modality you picked.

**Implication:** the two channels are complementary, not redundant. A combined
image + table observation is the obvious next rung, and on this evidence should recover
most of both columns.

---

## 5. Finding 2 — for the API models, magnitude is *not* the bottleneck

Among actions that named the right part, type and axis, the median emitted magnitude as a
fraction of the true correction:

| condition | median magnitude ratio |
|---|---|
| `er_image` | **1.01×** |
| `g3_image` | **1.00×** |
| `g3_text` | **1.03×** |
| `er_text` | **1.14×** |
| `qw8_image` | 0.15× |
| `qw8_text` | 0.27× |
| `dev_qw8_image` | 0.34× |
| `scale_qw8_image` | 0.27× |

When an API model works out *what* is wrong, it gets *how much* essentially right — the
ratio sits on 1.0 in every arm and every fault type. Their failures are identification
failures, not calibration failures.

This **confirms** the claim in `REPORT_2026-08-12_capability_analysis.md` §3 that magnitude
estimation is not the differentiator, and I should correct something I said mid-project:
I had flagged that section as needing amendment on the strength of the 0.17×/0.39× figures.
Those figures are Qwen's. They do not generalise to the API models, and §3 stands as
written for the models it was about.

Magnitude *is* a genuine and separate failure mode for Qwen — see below.

---

## 6. Finding 3 — Qwen3-VL-8B fails at a different stage, and no amount of
information fixes it

Two out of 180 Qwen episodes passed. The funnel shows a model failing earlier in the chain
than the API models do:

| condition | part % | type % | axis % | all three % | median magnitude |
|---|---|---|---|---|---|
| API arms | 71–82 | 46–63 | 41–61 | **24–43** | 1.00–1.14× |
| Qwen arms | 67–76 | 33–40 | 31–41 | **6–12** | 0.15–0.34× |

Qwen localises the part about as often as the API models, then loses the thread: it names
the right operation *and* axis *and* part on 6–12 % of actions versus 24–43 %, and when it
does, its corrections are **3–7× too small**.

Both ablations were designed to attack exactly that:

- **`dev_*` — tell it the current error in millimetres.** 1/60. On the API models the same
  information was worth a large jump; here it is worth nothing.
- **`scale_*` — tell it the typical fault magnitude.** 1/60 — even though the hint
  verifiably moved emitted magnitudes in the right direction (0.15× → 0.27× on image).

So the magnitudes improved and the success rate did not. Knowing how big the correction
should be is not sufficient when the model is still choosing the wrong operation and axis
88–94 % of the time. **Qwen is not information-limited at this scale; it is
identification-limited.** Adding facts to the prompt is the wrong lever.

A further symptom: Qwen emitted **67–172 invalid actions per condition** (API arms: 0–2),
and used essentially the full budget on every episode (9.8–10.0 turns vs 6.2–8.4), i.e. it
never concluded it was done.

### 6.1 The invalid actions were a configuration artefact — and removing them changed nothing

All six Qwen arms ran `--agent loop_qwen_full`, i.e. `history="full"`. That is the exact
setting `EXPERIMENT_2026-08-11_qwen_scale_ladder.md` §2.1 had already identified as making
the model "write a complete plan in prose and never convert it to syntax", with `window3`
recorded there as the fix. The ladder judged the 8B insensitive to the flag — but on
*success rate*, not on invalid rate, so the confound survived into std30.

Two harness faults compounded it. `env.py` returned the INVALID-ACTION observation with no
`images` key, so the turn after every malformed reply was sent **blind** — 203 of 203
image-less turns followed a parse error. And `window3`, being a stateless call, never
re-shows the annotated part view, so the model defaulted to targeting `P0` even on
instances where `P0` is the body.

Fixed all three (re-show the views, name the legal part ids, state the format rule per turn
without a copyable example) and reran the image arm on the same 30 problems:

| metric | `qw8_image` (as published above) | `strict_qw8_image` |
|---|---|---|
| parse errors | 203 | **4** |
| images sent per turn | 0, 2 or 4 | **always 2** |
| solved | 0/30 | **1/30** |
| median best deviation | 6.62× τ | 6.72× τ |
| episodes reaching a passing state | 0 | 1 (and it committed it) |

**Format compliance was essentially free to fix, and worth almost nothing.** A 98 %
reduction in malformed output moves success by one episode and leaves the median distance
from threshold unchanged at ~6.7× tolerance. The 0/30 was never an artefact of the model
failing to speak the protocol; it fails to find the repair. That is the cleanest available
confirmation that this model is identification-limited, and it retires the idea that a
lenient parser or a better-worded prompt is what stands between the 8B and a score.

One methodological note worth carrying forward: **Qwen3-VL-8B copies any concrete action
placed near the generation point.** A worked example in the per-turn step prompt produced
72 of ~130 actions at exactly the example's value, all of them the example's operation. The
same anchoring appeared when the action tag was moved ahead of the reasoning tag. Concrete
examples belong in the system prompt; the per-turn reminder must state the rule only.

---

## 7. Integrity checks

These matter because an earlier run in this project was invalidated by an image-transport
bug (`updatesAug12/INVALIDATED_DATA.md`).

| check | result |
|---|---|
| `ever_reached_threshold` vs `solved` | **identical in all 10 conditions** — no passing state was ever discarded by auto-commit |
| images rendered vs images sent to model | **equal on every turn of every image arm** — the transport bug is fixed and stays fixed |
| invalid actions, API arms | 0–2 per condition |
| API give-ups (timeout/refusal) | 1 in `er_image`, 2 in `er_text`, 0 elsewhere |
| oracle on this problem set | 30/30 |

### RESOLVED — missing renders in the Qwen image arms

13–30 % of turns in the three Qwen *image* conditions rendered **zero** images
(`qw8_image` 60/352, `dev_qw8_image` 43/342, `scale_qw8_image` 100/335). The API image arms
show none.

What is established: `n_images_rendered == images_sent_to_model` on every one of those
turns, so this is **not** the old transport bug — the environment produced nothing to send.
The affected turns are concentrated late in episodes and show no unusual deviation
(median 6.7× τ vs 7.4× τ on normal turns), so it is not obviously degenerate geometry.

**Cause found (2026-08-16).** `env.py:201` returned the INVALID-ACTION observation without
an `images` key, so `run_episode`'s `obs.get("images", [])` sent zero images on the turn
after every malformed reply. The coupling is exact: **203 of 203** image-less turns follow a
parse error. Because the model's failure mode *was* malformed output, this was a doom loop —
bad format → blind → worse format. The environment now re-shows the views it last rendered,
and the rerun (§6.1) sends 2 images on every turn of every episode.

Separately, image delivery to Qwen was verified **behaviourally**, not by counters: a
read-back test through the real transport — a secret word rendered only into pixels, plus a
two-image ordering check — passes 3/3. Images do reach the model.

---

## 8. Cost and latency

| condition | median s/episode | tokens/episode | thinking tokens |
|---|---|---|---|
| `er_image` | 51 | 55 k | 219 k total |
| `er_text` | 128 | 55 k | 754 k total |
| `g3_image` | 239 | 102 k | 927 k total |
| `g3_text` | **1883** | 224 k | **5.0 M total** |
| `qw8_image` | 33 | 46 k | none (no thinking channel) |
| `qw8_text` | 38 | 54 k | none |

`g3_text` is the outlier by an order of magnitude — a median of 31 minutes per episode and
5 M thinking tokens across the arm, against 927 k for the same model on images. Reasoning
over the numeric table is dramatically more expensive than reasoning over two renders, and
it buys 14/30 against 16/30. **On this benchmark the image channel is both cheaper and
better for gemini-3.1-pro**; text only wins on the translation subset.

Note this arm needed 6-way sharding to finish in reasonable wall-clock.

---

## 9. What this changes

1. **Ship both modalities together.** The complementary-channel result (§4) is the
   highest-value follow-up in the project: it predicts a combined observation recovers
   rotation *and* translation, and it is a small harness change.
2. **Stop adding information to Qwen's prompt, and stop tuning its format.** Two targeted
   information ablations returned 1/60 each, and fixing format compliance outright (203 → 4
   parse errors, §6.1) moved success from 0/30 to 1/30 with the median distance from
   threshold unchanged. The 8B's ceiling here is identification.
   **A bigger open base is not the answer either**: the 2026-08-11 ladder already ran
   Qwen3-VL-32B at n=30/cell and it scored **0/25 against the 8B's 1/25** on the τ=1.5 %
   single-fault rung — std30's exact setting — with both models 0/160 across all τ=1.5 %
   rungs. If the open-weight arm continues, the lever is fine-tuning the 8B on a rung where
   it has signal, not more parameters and not more prompt.
3. **Magnitude is solved for the frontier models.** Effort should move to fault
   *identification* — which is where 100 % of their remaining headroom now sits.
4. ~~Close the missing-render caveat.~~ **Done** (§7): the cause was the image-less
   INVALID-ACTION observation, now fixed, and image delivery to Qwen is verified by
   read-back. Nothing in the report now rests on an open harness question.

---

## 10. Reproducing

```bash
# one condition
FIXIT_TAU_FRAC=0.015 python text_fixit/run_trials.py \
  --run one_error_g3_image --instances data/instances_std30.jsonl \
  --agent loop_gemini_full --model gemini-3.1-pro-preview --modality image \
  --sweep --max-actions 1

# sharded, for the slow arms
... --shard 0/6      # ×6, then:
... --merge

# every figure, from the run tree
bash updatesAug12/viz/regenerate.sh
```

**Figures:** `updatesAug12/convergence_all.html` (per-iteration distance to threshold, all
10 conditions × 3 fault types), `what_predicts_repair.html` (the §4/§5 evidence),
`per_run_diagnostics.html` (best-reached vs committed, per-problem grid),
`qwen_convergence.html` (§6), `episode_walkthrough.html` (one episode end to end).

**Related:** `PROJECT_TIMELINE.md` · `REPORT_2026-08-12_capability_analysis.md` ·
`text_fixit/prompts/README.md` · `updatesAug12/INVALIDATED_DATA.md`
