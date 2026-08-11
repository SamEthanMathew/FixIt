# Experiment (M7) — Where is Qwen's rung?

**Date:** 2026-08-10
**Author:** FixIt / Stage-1 closed-loop repair
**Status:** COMPLETE — 125/125 episodes
**Predecessor:** M6 `docs/EXPERIMENT_2026-08-10_two_fault_rung.md`
**Raw tables:** `runs/_analysis/m7_qwen_ladder.{md,json}`

---

## 1. Why

M6 put `Qwen/Qwen3-VL-8B-Instruct` at **0/60** on the n=2 rung with 145 invalid actions, and read that
as *compliance-bound*: the model could not reliably emit the action protocol, so repair skill was not
being measured. That reading left a confound — 0% could equally have meant the rung was simply too
hard — and the two have opposite consequences for Stage-2 (fix the format vs. build an easier rung).

M7 breaks the confound the cheap way: walk the SAME model down rungs that are **already calibrated
for the API models**, and watch the invalid-action rate as difficulty falls. No new instances, no API
cost, local GPU only.

## 2. Design

| run | set | τ | hard | n | API reference |
|---|---|---|---|---|---|
| `m7_qw_ctrl_batch_image` | hardened n=1 control | 1.5% | yes | 25 | er 20% / g3 20% (M5) |
| `m7_qw_ctrl_stack_image` | hardened n=1 control | 1.5% | yes | 25 | er 24% / g3 28% (M5) |
| `m7_qw_easy_batch_image` | original easy baseline | 2.5% | no | 75 | **er 57% / g3 49%** |

Image only — text is 0/120 across three models (M6), so it is spent compute. Budget 10, deviation
OFF, `loop_qwen_full`, prompts byte-identical to the API runs.

**Two reproducibility details that mattered.** The 41–57% baselines were not run on
`instances_test.jsonl` — their episode ids appear 0/75 in the test split and 75/75 in train. They
used `--split train --per-type 25 --seed 0`; that selection was reproduced offline and matches all 75
baseline ids exactly, so Qwen is scored on the *same instances*, not a comparable sample. Those runs
also predate manifest logging, so their config was reconstructed from the records themselves
(`deviation=off`, `budget=10`, `hard=False`, batch). The easy rung must be run at
**`FIXIT_TAU_FRAC=0.025`**: those instances predate the `tau_frac` field, carry no value for
`env.reset` to assert against, and would otherwise be silently scored at whatever tolerance the
process happened to inherit.

## 3. Result

| condition | N | solved | invalid | deviation closed | made worse | ever simulated a PASS |
|---|---|---|---|---|---|---|
| qw_ctrl_batch_image | 25 | **0** | 2% | −16% | 68% | 0 |
| qw_ctrl_stack_image | 25 | **0** | 11% | −16% | 60% | 0 |
| qw_easy_batch_image | 75 | **0** | 3% | −7% | 59% | 0 |

**0/125, including 0/75 on the easiest rung in the project** — the instances where robotics-er-2
scores 57% and gemini-3.1-pro 49%.

## 4. Diagnosis: exemplar anchoring, with a magnitude failure underneath

**Not difficulty.** Zero at every rung, including the easiest.

**Not compliance.** Invalid-action rate is 2–3% on batch — *lower* than several API cells, and it does
not fall as difficulty falls. **M6's compliance reading was wrong**: the 25% invalid rate there was an
artifact of the text modality, not a property of the model. Fixing the format would yield well-formed
wrong answers.

**It is grounding.** Over all 125 episodes:

- **90% of episodes open with the verbatim prompt example**, `TRANSLATE(P1, Y, -0.04000)`. The
  template's example line is `<act>SIMULATE TRANSLATE(P1, Y, -0.04)</act>`.
- **67% of all 1,246 actions use axis Y** — the exemplar's axis — against 6% for X.
- Yet the search is not blind: right action **type** in 97% of episodes, right **axis** in 74%, right
  **type+axis together in 56%**.
- When it found the right type and axis, the **largest magnitude it ever tried was a median 0.40× the
  ground truth**, and it typically *shrank* from there.
- Best score ever simulated across 125 episodes: **0.248** (mean 0.020), against ~0.37 merely to
  reach the tolerance boundary.

A representative easy-rung episode, ground truth `TRANSLATE(P1, X, 0.15)`:

```
TRANSLATE(P1, Y, -0.04)   score 0.041   <- verbatim prompt exemplar
ROTATE(P1, Z, -5.0)       score 0.045
SCALE(P1, Y, 0.95)        score 0.044
TRANSLATE(P1, Y, -0.02)   score 0.044
ROTATE(P1, Z, -2.0)       score 0.045
```

It cycles the exemplar's types and axes with shrinking magnitudes, never touches X, and the score is
flat to three decimals — the closed loop is doing nothing. Worse, it reads a too-small correction as
evidence to correct **less**.

So Qwen usually works out *what* to do and *where*, then attempts it at roughly a third of the
required size, anchored on the 4 cm number in the prompt while faults run 150 mm and up.

## 5. Consequences for Stage-2

- `ever_simulated_a_pass` is **0/185** across M6 and M7 combined. There is no positive reward event
  anywhere in the data to bootstrap from.
- `deviation_closed` is negative at every rung — the average episode ends worse than it started.
- Trace-SFT would fix the 2–11% format noise but not the anchoring; correct magnitudes would only be
  taught implicitly.

## 6. A structural limit this exposed

**The existing instance sets cannot be made easier by loosening tolerance.** Corruptions are
generated at ≥ `BROKEN_MARGIN`×τ with `BROKEN_MARGIN = 3.0`, so at a runtime tolerance of 4× the
generation value, 11 of 30 instances already pass unrepaired and `NO_FIX()` scores. k=3 is the
ceiling, and Qwen's best attempt clears it in only 7% of episodes.

Difficulty here is scale-invariant: the task is *estimate the magnitude*, and τ and fault size scale
together. Regenerating at a larger τ with the margin held changes nothing. **The lever is the
generation margin itself.** To land inside τ when the fault is D·τ, magnitude accuracy of ±1/D is
required — so a *smaller* D is a genuinely easier task. At Qwen's characteristic 0.4× undershoot the
residual is 0.6·D·τ, which clears tolerance only when **D < 1.67**.

That arithmetic designs the next rung (M8): a single-fault set generated at **margin 1.5**, where the
model's existing behaviour is just barely sufficient, paired with a prompt ablation that removes the
concrete exemplar and states the fault scale explicitly.
