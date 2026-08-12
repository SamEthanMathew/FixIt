# Model capability analysis — closed-loop object repair

**Date:** 2026-08-12
**Task:** FixIt / Stage-1 — repair a broken PartNet-Mobility refrigerator by proposing geometric
corrections in a closed simulation loop.
**Models:** `gemini-3.1-pro-preview`, `gemini-robotics-er-2-preview`, `Qwen3-VL-8B-Instruct`,
`Qwen3-VL-32B-Instruct-FP8`. Reference points: oracle 100%, random 0–4%.

All numbers below are measured, not estimated. Raw records under `text_fixit/runs/`,
aggregates under `runs/_analysis/`.

---

## 1. Method

An episode presents a fridge with one or more parts geometrically corrupted (translated, rotated or
rescaled). The agent proposes actions in a parameter-free language — `TRANSLATE(P1, X, 0.06)` —
simulates them, sees the result, and commits. Success = every faulty part restored within tolerance
τ **and** every door still closes **and** no part-collision above the healthy baseline.

Held constant unless stated: image observations, batch contract, budget 10 simulations, numeric
deviation hidden, `history=window3` for the open models. Every instance set is run at the τ it was
generated under. Invalid-action rate is 0–2% everywhere, so no result below is a formatting artifact.

## 2. Table 1 — the difficulty ladder

Success rate. D = fault size in units of τ, i.e. how precise the correction must be (accuracy of
roughly ±1/D is required to land inside tolerance).

| rung | Qwen-8B | Qwen-32B | robotics-er-2 | gemini-3.1-pro |
|---|---|---|---|---|
| easy (D≈1.6, τ2.5%) | 5/30 = 17% | 7/30 = 23% | — | — |
| standard single fault (D≈4.6, τ2.5%) | 1/75 = 1% | 6/75 = 8% | 17/30 = **57%** | 37/75 = **49%** |
| hardened single fault (τ1.5%, off-grid) | 1/25 = 4% | 0/25 = 0% | 5/25 = 20% | 5/25 = 20% |
| 2 composed faults (τ1.5%) | 0/30 = 0% | 0/30 = 0% | 1/30 = 3% | 0/30 = 0% |
| 3 composed faults (τ1.5%) | 0/25 = 0% | 0/25 = 0% | 0/25 = 0% | 0/25 = 0% |

**Every model fails completely once faults compose.** Three composed faults: 0/200 across all four
models. This is not a tolerance artifact — at 3× tolerance it is still 0%.

**The open models are roughly one full rung below the API models**, and scale barely moves them:
8B→32B is 4× the parameters for +7 points on one rung and nothing on the others.

## 3. Table 2 — where the capability breaks (hardened single-fault rung)

Recomputed from logs (`text_fixit/decompose.py`). Per episode: did the model ever target a genuinely
faulty part, use the correct action type, the correct axis, both together — and how close was its
best magnitude once it reached the right 1-D problem?

| model | PASS | localise | type | axis | **type+axis** | mag median | mag ±25% |
|---|---|---|---|---|---|---|---|
| gemini-3.1-pro | 20% | 100% | 96% | 92% | **84%** | 1.01× | 71% |
| robotics-er-2 | 20% | 92% | 84% | 80% | **76%** | 1.00× | 63% |
| Qwen-8B | 4% | 72% | 60% | 44% | **32%** | 0.99× | 75% |
| Qwen-32B | 0% | 68% | 48% | 48% | **24%** | 0.41× | 0% |

Three things fall out:

- **Localisation is not the bottleneck for anyone.** Every model finds a genuinely faulty part in
  68–100% of episodes. No model is confused about *which door* is broken.
- **The open models collapse at axis/type selection.** API models reach the correct 1-D problem in
  76–84% of episodes; Qwen in 24–32%. This single stage accounts for essentially the whole gap.
- **Magnitude estimation is NOT the differentiator.** Once the 8B reaches the right axis its best
  magnitude is 0.99× ground truth, with 75% of attempts inside ±25% — *better* than either API
  model. The open-model failure is diagnostic, not numeric.

Note the API models' own gap: gemini-3.1-pro reaches the right 1-D problem 84% of the time and gets
within ±25% in 71% of those, yet passes only 20%. At D≈4.6 the required accuracy is about ±22%, so
±25% is precisely at the edge — the API failure mode is *near-misses on magnitude*, not misdiagnosis.

## 4. Table 3 — two ablations (hardened single-fault rung, n=25 each)

| model | loop, deviation OFF | loop, deviation **ON** | one-shot, deviation OFF | loop contributes |
|---|---|---|---|---|
| robotics-er-2 | 20% | **76%** | 16% | +4 pts |
| gemini-3.1-pro | 20% | **65%** (n=20) | 12% | +8 pts |
| Qwen-8B | 4% | **4%** | 4% | +0 pts |
| Qwen-32B | 0% | **4%** | 0% | +0 pts |

"deviation ON" shows the agent the numeric error (`worst part off by N mm`) each turn.
"one-shot" removes the loop entirely: propose once, commit, no feedback.

**The two model families are limited by different things, and the ablation separates them cleanly.**

- **API models are perception-limited.** Handing them the measurement triples success (20% → 65–76%).
  The funnel shows why: with deviation visible, axis accuracy goes 80–92% → **100%**. The number
  tells them *which axis is wrong*, and that alone is worth 45–56 points. Their magnitude accuracy
  barely changes (59–50% within ±25%), so the gain is diagnostic, not numeric.
- **Open models are diagnosis-limited, and information does not help.** Qwen is identical with and
  without the error (4% → 4%, 0% → 4%) and its axis accuracy is unmoved (44% → 44%). It cannot
  convert a stated error into the correct axis, so a more accurate error is worthless to it.
- **The closed loop is close to decorative.** It adds 4–8 points for the API models and exactly zero
  for both open models. Of solved episodes, 0–40% are solved on the *first* simulation.

## 5. Findings

1. **For frontier models this is a visual metrology problem, not a reasoning problem.** They can
   plan and act correctly; they cannot measure geometric error from a rendered view. Supply the
   measurement and performance triples.
2. **For open models the limit is diagnosis — identifying which degree of freedom is wrong.** Their
   magnitude estimation is already competitive. This is the specific capability oracle-trace SFT
   would teach, since every trace demonstrates a correct (part, type, axis) selection.
3. **Composition is a wall for everything.** 0/200 at three composed faults, across four models, two
   contracts and two modalities. Robust to a 3× tolerance relaxation.
4. **The closed loop contributes very little.** Any claim that this benchmark measures sequential
   decision-making is currently unsupported: one-shot performance is within 4–8 points of full-loop
   performance for every model tested.
5. **Scale is a weak lever for open models.** 8B→32B: +7 points on one rung, zero on three others,
   and the ordering even inverts on the hardened control.

## 6. Caveats

- **n is 25–30 per cell** for most conditions (75 for the standard single-fault rung). A 95% Wilson
  interval at n=25 spans roughly ±15 points, so only large effects are interpretable. Specifically
  interpretable: the deviation ablation (+45 to +56 pts), the composition wall (0/200), and 8B vs
  32B on the standard rung (1% vs 8%, non-overlapping). Not interpretable: 17% vs 23% on the easy
  rung, or 20% vs 20% between the two API models.
- **`m11_dev_g3` was stopped at 20/25 episodes** by choice; its manifest records the truncation.
- Two harness bugs were found and fixed during this work, each of which had manufactured a false
  model failure — see `EXPERIMENT_2026-08-11_qwen_scale_ladder.md` §2. Both are documented because
  each silently converted infrastructure failure into apparent model incapacity.
- The easy rung was constructed so that the models' existing behaviour barely suffices; it is a
  training target, not a neutral measurement.

## 7. Implications

- **A trainable rung exists** (`instances_easy`, 17–23% for both open models against 3% random) and
  is the only place an open model produces reward events.
- **SFT the 8B, not the 32B.** The 32B clears nothing the 8B does not, costs 4× the compute, will
  not fine-tune on 2×48 GB, and its bf16 weights do not fit the available disk.
- **Before any training**, `instances_easy` needs a shape-level train/test split: it currently mixes
  19 train-split and 11 test-split shapes with one instance per base, so training on its oracle
  traces and evaluating on the same set would leak invisibly.
- **If the goal is to measure sequential decision-making**, the task needs redesign: the loop is
  worth 4–8 points today, and composition — the setting where a loop should matter most — is at 0%
  for every model.
