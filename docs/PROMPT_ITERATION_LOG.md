# Qwen3-VL-8B prompt iteration log

**Goal:** ≥20% overall success on std30 (≥6/30) **and** ≥2 successes in each of translate, rotate,
scale. Prompt must stay general to fridge repair — no per-instance or per-fault-type hacks.

**Baseline to beat:** `strict_qw8_image` = **1/30** (translate 0, rotate 0, scale 1), under
`window3` + `one_error_strict`, parse errors 4.

**Method.** Each iteration states a hypothesis, changes ONE thing, tests, compares, and records the
verdict. Two instruments:
- `perception_probe.py` — one question per problem (which part / type / axis), no loop, no action
  grammar, no magnitude. ~2 min for 30 problems. Isolates *diagnosis*.
- `run_trials.py --sweep` + `funnel.py` — the full loop. ~30–60 min. Measures *success*.

---

## Iteration 0 — restore the baseline

**Change.** Reverted `one_error_strict_{image,step}.txt` to commit `e6598c2` (the version that scored
1/30). Commit `aa9fb53` had changed seven things at once and scored **0/19** with type 23% / axis 20%
— both below the 33.3% chance floor — and parse errors back up to 49.

Kept the four code changes from `aa9fb53`, which are independently sound:
- `part_table.py` header `bbox (w,d,h)` → `size X,Y,Z (m)` (the old header claimed Z was height when
  Z is the thinnest axis, which `corruption.py` can never fault)
- `_deviation_note()` — the "error in mm" sentence now appears only when `show_deviation` is on
- `_targetable()` / `_legal_pid()` — validated, illegal-part errors 14 and 13 → 0
- `views.axis_image_legend()` — geometrically verified, flips correctly under `hard=True`

Also fixed `perception_probe.py`: it read `gt_fix` as a string when it is a dict, and resolved
instance URDF paths relative to cwd rather than to `text_fixit/`. The probe had never run.

---

## Iteration 1 — measure the diagnosis ceiling directly

**Hypothesis.** The agent prompt is at fault, and asking the model cleanly — no loop, no action
grammar, no magnitude — will show diagnosis well above chance.

**Result: REFUTED, decisively.**

| probe condition | part % | type % | **axis %** | all-three % |
|---|---|---|---|---|
| full (legend + part table) | 73.3 | 40.0 | **30.0** | 6.7 |
| no legend | 76.7 | 43.3 | **26.7** | 3.3 |
| no part table | 66.7 | 33.3 | **26.7** | 3.3 |
| neither | 60.0 | 36.7 | **33.3** | 6.7 |
| *chance* | ~50 | 33.3 | **33.3** | ~5.6 |

Axis accuracy is **at or below chance in every condition**, and all-three is at chance throughout.

**The mechanism is a fixed prior, not weak perception.** The axis confusion matrix, full condition:

```
        X    Y    Z
  X     1   15    0
  Y     0    8    0
  Z     0    6    0
said:   1   29    0
```

It answered **Y on 29 of 30**, and across all four conditions × 30 problems it emitted **Z exactly
zero times**. It is not estimating the axis at all; it is emitting a constant that happens to be
right on the 8 problems whose fault lies on Y.

**Not my legend's fault.** I suspected the legend's "+Y points straight up" created the prior.
Removing it made accuracy *worse* (30.0 → 26.7) and the Y-bias persisted. The prior is intrinsic.

### What this bounds

std30 ground truth, axis × fault type:

| | X | Y | Z | total |
|---|---|---|---|---|
| translate | 7 | 2 | 1 | 10 |
| rotate | 4 | **1** | 5 | 10 |
| scale | 5 | 5 | 0 | 10 |
| **total** | 16 | 8 | 6 | 30 |

With the axis pinned to Y, the per-type ceiling is the Y column: translate ≤2, **rotate ≤1**, scale ≤5.

> **The ≥2-rotate-successes goal is mathematically unreachable unless the Y-prior is broken.**
> Overall ceiling with the prior intact is 8/30 = 27%.

**Conclusion for the loop.** The objective is now precise and singular: **make the model emit X and Z
at all.** Every subsequent iteration is judged first on the axis confusion matrix, not on `solved` —
if the off-diagonal stays empty, nothing downstream can work.

---

## Iteration 2 — ask in image space, convert in code

**Hypothesis.** The model cannot name an object-frame axis from a render, but *can* describe a
displacement in picture terms (left/right, up/down, in/out). The object→image mapping is already
computed deterministically by `views.axis_image_legend()`, so the model should answer in the space it
can perceive and the harness should do the frame conversion.

This stays general: the mapping is derived per-instance from the actual camera and URDF, so it holds
for any fridge and any fault type.

**Result: REFUTED.** Asked purely in picture terms (UPDOWN / LEFTRIGHT / INOUT), with the
object→screen mapping done deterministically in code, the model answered **UPDOWN on essentially
every problem** → axis 26.7%, same degenerate matrix (Z said 0/30).

So it is not a frame-naming problem. The *perceptual report itself* is constant: it says the door is
wrong vertically regardless of what is actually wrong.

---

## Iteration 3 — is the fault simply too small to see?

**Hypothesis.** The discrepancy may be below the vision encoder's effective resolution. Quantified it:

| | |
|---|---|
| render | 768×768, camera margin 1.7 |
| one Qwen3-VL visual token | 32×32 px (patch 16 × spatial merge 2) |
| median fault | 35.4 px = **1.11 tokens** |
| smallest fault | 10.1 px = **0.32 tokens** |

The model is being asked to characterise a discrepancy about the size of a *single visual token*.
That is a genuinely plausible reason for a constant answer.

**Test.** Re-rendered at **1536 px with camera margin 1.15** — ~3× the linear resolution and a tighter
crop, so the fault spans ~3.3 tokens instead of ~1.1. Same camera code path, only resolution and
framing changed.

**Result: REFUTED.** part 76.7 / type 43.3 / **axis 30.0** / all-three 3.3 — statistically identical
to 768 px, and the confusion matrix is unchanged (Y said 29/30, Z said 0/30).

---

## Where this leaves the goal

Four independent interventions, each targeting a different candidate cause:

| iteration | intervention | axis % | Z emitted |
|---|---|---|---|
| 1 | baseline (legend + table) | 30.0 | 0/30 |
| 1 | legend removed | 26.7 | 0/30 |
| 1 | part table removed | 26.7 | 0/30 |
| 1 | neither | 33.3 | 0/30 |
| 2 | image-space question, code-side conversion | 26.7 | 0/30 |
| 3 | 1536 px + tight crop (3× tokens on the fault) | 30.0 | 0/30 |

**Every condition is at or below the 33.3% chance floor, and `Z` is never emitted — 0 times in 180
queries.** The output does not depend on the image.

This is not a prompt problem. Prompt wording, information content, question framing, and image
resolution have each been varied independently, and none of them moves the axis distribution at all.

**Instrument validation in progress:** running the identical probe, on the identical images, against
gemini-3.1-pro. If Gemini scores well, the probe is sound and the limitation is the 8B's perception —
which would mean the ≥2-rotate-successes goal is unreachable by prompting, since rotate has a ceiling
of 1/10 while the axis is pinned to Y.


---

## Iteration 3b — instrument validated

Ran the identical probe, identical images, against **gemini-3.1-pro**:

| | part % | type % | **axis %** | all-three % |
|---|---|---|---|---|
| gemini-3.1-pro | 90.0 | 70.0 | **60.0** | 40.0 |
| Qwen3-VL-8B | 73.3 | 40.0 | **30.0** | 6.7 |
| chance | ~50 | 33.3 | 33.3 | ~5.6 |

**The probe is sound and the information is in the renders.** Gemini extracts it; the 8B cannot.
This is a perception limit of the 8B, not a defect in the question or the images.

**Consequence:** no amount of prompt wording will make the 8B *see* the axis. But the task grants
10 simulator calls — so the agent does not have to see it if it can **search** for it.

---

## Iteration 4–8 — replace perception with search

**Hypothesis.** Use the simulator as the sensor. Actions apply FRESH to the original object every
turn (`batch` contract), so each SIMULATE is an independent, repeatable experiment. With the error
reported in millimetres (`--deviation on`, never before tested under the clean `window3` config), the
agent can *measure* which operation and axis is wrong instead of judging it from pixels. New prompt
set `one_error_search_{image,step}.txt`.

A key enabler found in the data: **for a translate fault the reported error in mm equals the offset**,
so once the axis is known the magnitude is given, not guessed.

Iterated on the three pilot problems (one per fault type):

| it. | change | translate | rotate | scale |
|---|---|---|---|---|
| 4 | search procedure + `--deviation on` | **PASS** (turn 1, dev 0.01×) | fail | fail |
| 5 | + "flat error ⇒ wrong part" rule | PASS | fail | fail |
| 6 | + full probe log (was a 3-turn window) | PASS | fail | fail |
| 7 | + break the op→axis pairing in examples; find the part first | PASS | fail | fail |
| 8 | + `$untried` combos listed per part; **LOCK ON** after a ≥50% error drop | **PASS** | fail | **PASS** |

### What each iteration fixed, and why it was needed

- **Full probe log.** `_history_text` showed only the last 3 probes. The model re-ran identical
  probes and could not see that a part's error had read the same value eight times. `QwenVLAgent`
  now shows all 12.
- **Op→axis pairing.** My three worked examples paired `TRANSLATE→X`, `ROTATE→Y`, `SCALE→Z`. The
  model copied the *pairing*: it only ever scaled Z. Examples now show every operation on several
  axes, with an explicit note that the pairing is arbitrary.
- **`$untried`, per part.** The model emitted axis Z zero times in 11 probes even with Z in the
  examples — it cannot enumerate a search space unaided. The harness lists what remains. It must be
  **per part**: a global set marked `ROTATE/Z` as tried after it was probed on the *healthy* part,
  so the correct answer was never probed.
- **Lock on.** 12250 found `SCALE(P1,Y,0.80)` → error 6.70× → **1.64×**, then wandered back to
  scaling Z. With the lock-on rule it instead refined to `0.750` → **0.41× PASS**.

### Open: rotate

10143 still fails. It spends 5–9 of 11 probes on the healthy part P0, whose error reads *exactly*
3.27× every time. The harness now deduces this (`_healthy_by_probe`: with one fault, if ≥2 probes on
a part leave the worst-part error bit-identical, that part is not the faulty one) and renders
`ONLY target these parts: P2 (ruled out by probe, do not target again: P0)`.

**The model ignores it** and keeps probing P0. That is a compliance failure, not an information
failure — so the next iteration enforces it in `action_parser` the same way non-fixable parts are
already rejected, rather than asking politely.

**Full 30-problem run in progress** on the iteration-8 configuration.

---

## Iteration 9 — enforce the ruled-out part instead of asking

**Observation from the run.** The prompt rendered
`ONLY target these parts: P2  (ruled out by probe, do not target again: P0)`
and the model targeted P0 on three subsequent turns anyway. Information was not the problem;
compliance was.

**Change.** `action_parser.parse()` gains `ruled_out=()`. A part the simulator has already proven
healthy is now rejected exactly like a non-fixable part, and the existing reparse retry hands the
model the reason. `run_episode` recomputes the set every turn (`_live_parse_kwargs`), so it tightens
as evidence accumulates. Backward-compatible: with no `ruled_out` passed, behaviour is unchanged.

The deduction itself (`_healthy_by_probe`) uses only the run's own outputs: with exactly one fault,
the reported error is the worst part's error, so if ≥2 probes that moved part P leave that number
bit-identical, P is not the faulty part. It never consults ground truth.

**Status.** Verified in isolation (ruled-out target → rejected with reason; legal target → accepted;
no-arg call → unchanged). Not yet measured on a full run — the in-flight 30 launched before this
change, so it stands as the clean pre-enforcement baseline.

---

## Interim result — iteration 8 configuration, first 10 problems

| fault type | solved | baseline | status |
|---|---|---|---|
| translate | **5/10** | 0/10 | **goal met** (≥2) |
| rotate | pending | 0/10 | |
| scale | pending | 1/10 | |

The five translate wins land at 0.00–0.02× tolerance — essentially exact, because once the axis is
identified the reported error *is* the magnitude. Overall so far: **5/10 = 50%**, against a 1/30
baseline and a 20% target.

---

# RESULT — goal met

`search_qw8_image`, 30 problems, Qwen3-VL-8B, `window3` + `one_error_search` + `--deviation on`.

| | target | result | |
|---|---|---|---|
| overall | ≥20% | **11/30 = 37%** | MET |
| translate | ≥2 | **5/10** | MET |
| rotate | ≥2 | **2/10** | MET |
| scale | ≥2 | **4/10** | MET |

### Against the previous best

| | baseline `one_error` | best prompt `strict` | **`search`** |
|---|---|---|---|
| solved | 0/30 | 1/30 | **11/30** |
| translate / rotate / scale | 0 / 0 / 0 | 0 / 0 / 1 | **5 / 2 / 4** |
| parse errors | 203 | 4 | **2** |
| median best deviation | 6.62× | 6.72× | **3.37×** |
| magnitude ratio (given correct op+axis) | 0.15× | 0.57× | **1.00×** |

**An 11× improvement over the previous best, and the first non-zero result on translate and rotate.**

### Why it worked

The breakthrough was not a better description of the fault. Six iterations of prompt wording,
information content, question framing and image resolution moved the diagnosis metrics **not at
all** — and a Gemini control on identical images (axis 60.0% vs the 8B's 30.0%) proved the
information was there and the 8B simply could not extract it.

So the winning change was to **stop asking the model to see the answer and let it measure it**:

1. **The simulator becomes the sensor.** Actions apply fresh to the original object every turn, so
   each SIMULATE is an independent experiment. With the error reported in millimetres, the model can
   *test* which operation and axis is wrong instead of judging it from pixels.
2. **For translate faults the reported error IS the magnitude** — once the axis is identified the
   value is given, not guessed. This is why the translate wins land at 0.00–0.02× tolerance.
3. **The harness keeps the books the model cannot.** It lists untried (operation, axis) pairs *per
   part*, shows the full probe log rather than a 3-turn window, and deduces which parts the probes
   have already proven healthy.
4. **Lock on after a ≥50% error drop** — stop exploring, refine only the value.

Note the magnitude ratio moved 0.15× → **1.00×**. The second gate in `REPORT_2026-08-16` §5 — that
magnitude was at chance even given a correct diagnosis — was an artefact of never having the error
signal available under a working configuration. With it, calibration is essentially perfect.

### Generality

Nothing here is fault-type or instance specific. The procedure is one algorithm — identify the part,
sweep the nine (operation, axis) pairs, lock on, refine — and all three fault types are solved by the
same prompt. The bookkeeping derives only from the run's own outputs and never consults ground truth.

### Still open

- Iteration 9's parser enforcement of ruled-out parts is built and unit-tested but **not** in this
  run; it should be worth a further point or two on rotate, which still loses probes to healthy parts.
- Rotate remains the weakest type (2/10). Its faults are the largest in the set (D up to 14.1) and
  the probe magnitude for rotation is not derivable from the error the way translation's is.
- The API models remain ahead (16–19/30), so this closes roughly half the gap, not all of it.
