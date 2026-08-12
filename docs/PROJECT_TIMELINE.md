# FixIt Stage-1 — project timeline

A chronological record of every experiment run on the closed-loop repair task: what was tested, why
it was tested, what came back, and what had to be corrected afterwards. Written 2026-08-12.

Per-experiment detail lives in the `EXPERIMENT_*.md` files; this is the connecting narrative.
Raw records are under `text_fixit/runs/`, aggregates under `text_fixit/runs/_analysis/`.

---

## Phase 0 — origin (2022, revived 2026-07)

The repository began as the CVPR'22 **FixIt** codebase (Hong et al.): point-cloud perception plus a
learned dynamics model that selects a fix for a malfunctional object from multiple choice
(`flownet3d/`, `pointnet++/`, `dynamics/`, `generate_data/`). That stack is dormant.

- **2026-07-10** — modernized for Python 3.10 / Torch 2.5.
- **2026-07-15** — dataset visualizations, model galleries, rollout GIFs.

The new direction, from `text_fixit/MILESTONE_1.md`: stand up a **closed perception → action →
simulation → perception loop** where an off-the-shelf VLM repairs a broken refrigerator, and measure
on held-out shapes whether the loop and visual feedback actually help versus one-shot and random.

## Phase 1 — building the harness (2026-08-03 → 08-08)

| date | change | reasoning |
|---|---|---|
| 08-03 | Stage-1 text LLM closed-loop harness (Gemini) | the loop itself: `env` / `action_parser` / `run_episode` / agents |
| 08-03 | `--per-type` stratified sampling; tries-to-submit metric | success rate alone hides whether the loop is used |
| 08-03 | full-context history mode (`loop_gemini_full`) | test whether an accumulating transcript beats a 3-turn window |
| 08-04 | VLM image observation path (modality × deviation 2×2) | is the symbolic channel or the visual one carrying the task? |
| 08-04 | process-unique temp candidate URDF | concurrent runs were clobbering each other's scratch files |
| 08-07 | continuous actions; begin/end part states; "keep going" | the action space was quantised while corruptions were on-grid |

**Design decision that shaped everything after:** actions are **parameter-free**
(`TRANSLATE(P1, X, 0.06)`) with the rotation centre and scale pivot recomputed from current geometry
(`canonical.py`). This is what makes every break exactly invertible in the agent's own language —
and it is what allows an oracle to hit 100%.

## Phase 2 — the image observation, refined by trial (2026-08-08)

Six commits in one day, all on how the object is shown. Each was a response to a specific failure:

| change | why |
|---|---|
| drop filmstrip → open+closed views; flat materials | PartNet textures render near-black; the model could not see the geometry |
| remove top-down view; render OPEN from the same 3/4 angle | inconsistent viewpoints made before/after uncomparable |
| **stop revealing which door is broken** | the render was highlighting the faulty part — the task was leaking |
| colour by part INDEX, not by fault | same leak, subtler: colour was a fault indicator |
| show before AND after, both closed and open | the model had no reference to compare its repair against |
| **feed the CLOSED view only** | open views were uninformative; a displaced door swings into free space |

That last one is the empirical core of `evaluation.py`: **closing is the discriminating motion.**
An opening sweep was built, tested and falsified — broken doors scored identically to healthy ones.

## Phase 3 — M1–M3 baselines (through 2026-08-08)

Single fault, τ=2.5%, on-grid magnitudes, budget 10, deviation OFF:

| model | text | image |
|---|---|---|
| gemini-3.1-pro | 41% | 49% |
| robotics-er-2 | 33% | **57%** |

**Two problems, both visible in the logs.** Solves arrived in a *median of one* SIMULATE — so the
loop was not load-bearing. And corruption magnitudes were drawn **on a discrete grid** while the
action space had been made continuous, so a model could land inside tolerance by recalling a
plausible grid bin without estimating anything.

## Phase 4 — M4: composite faults (2026-08-09)

**Reasoning:** make the task hard along both axes at once — composition *and* the freebies — and
design it so the two causes can be told apart afterwards.

**Built:** 25 composite instances (exactly 3 sub-faults each: one translate, one rotate, one scale),
a matched 25-instance single-fault control under the same hardened knobs, and **two action
contracts** — `batch` (an ordered list applied fresh each turn) and `stack` (one action onto a
persisted working state, plus `RESET()`).

**Hardening knobs:** continuous off-grid magnitudes, τ 2.5% → 1.5%, part table's `fixable`/`role`
columns hidden, all doors rendered one neutral colour from an adverse yaw.

**Result — 300 episodes:**

- Composite: **0/200** for both models, both contracts, both modalities. Still 0% at 3× tolerance.
- Hardened control: 4–20%, against a predicted 25–40%.
- Text was not merely worse but *destructive*: −42% deviation closed, objects ending worse than they
  started 52–88% of the time.

**Pre-registered predictions:** H1 (composition dominates) confirmed far more strongly than
predicted. H4 (control drops modestly) **refuted** — more of the earlier 40–57% was on-grid luck
than had been credited. H5 (image advantage narrows) **refuted in reverse** — it widened.

**A scoring bug this exposed:** PyBullet caches parsed URDF and collision geometry **by filename**
within a client, so reusing one temp path froze `closes`/`collides` at their first-candidate values.
Invisible under a single-action contract; obvious under `stack`, where the oracle scored 92% batch
but 64% stack on identical final geometry. Fixed with a unique filename per evaluation.

## Phase 5 — M5: which hardening knob actually mattered (2026-08-09/10)

**Reasoning:** `--hard` bundled three switches. If they are not separable, no one can say which made
the task hard.

**Built:** split into `reveal_fixable` / `hard_render` / `multi_fault_hint`, then re-ran the control
set with the fixable column **revealed**, plus the `stack` contract M4 had skipped as "redundant for
a one-action fix".

**Result — 200 episodes:**

- `reveal_fixable` is **inert** — batch arms moved 0, +1, +2, 0 episodes out of 25.
- **`stack` beat `batch`** at one fault (g3-image 20% → 28%), with `deviation_closed` flipping from
  −3% to **+25%** — the first positive value in the project. M4's redundancy assumption was wrong.
- The text penalty looked **model-specific**: g3 was destroyed by text, er was not.

## Phase 6 — M6: the n=2 rung (2026-08-10)

**Reasoning:** the benchmark had no measurable middle. n=1 discriminated (4–28%); n=3 was a wall
(0/200). Nothing in between, so no method could show partial progress, and M4's H3 (does assignment
burden cost?) was untestable because its 2-door arm always contained a door carrying only one fault.

**Built:** 30 instances, exactly 2 sub-faults, **level-matched** — 15 with both faults on one door,
15 with one fault on each of two doors. Both arms need exactly two correct actions, so PASS is
directly comparable. Stratified 5 per type-pair per arm.

**Result — 300 episodes:**

- Best cell 10% (g3/batch/image); **5 of 8 API cells exactly 0%**; aggregate 2%. The rung exists but
  sits far nearer the wall than the floor.
- **H2 refuted and reversed** — M5's stack advantage *inverts* under composition (g3: batch 10% vs
  stack 0%). The contract question is difficulty-dependent and cannot be settled once.
- **H5's underlying claim refuted** — text is 0/120 across all models; er's text arms are destructive
  too (−64% deviation closed). M5's "text harm is g3-specific" did not survive composition.
- All 3 of g3's solves were `rotate+scale`; `rotate+translate` was 0/80 everywhere.

## Phase 7 — M7: where is Qwen's rung? (2026-08-10)

**Reasoning:** M6 put Qwen3-VL-8B at 0/60 with 145 invalid actions and read it as *compliance-bound*.
That left a confound — 0% could equally mean the rung was too hard — and the two have opposite
consequences for Stage-2. Breaking it costs nothing: walk the same model down rungs already
calibrated for the API models.

**Result — 125 episodes: 0/125, including 0/75 on the easiest rung in the project** (where er scores
57%).

- **Not compliance** — invalid rate 2–3% on batch, *lower* than several API cells, and it does not
  fall as difficulty falls. **M6's reading was wrong**; the 25% invalid rate there was an artifact of
  the text modality.
- **Exemplar anchoring** — 90% of episodes opened with the *verbatim prompt example*
  `TRANSLATE(P1, Y, -0.04)`; 67% of all actions used the exemplar's axis.

**A structural limit this exposed:** the existing sets **cannot be made easier by loosening
tolerance**. Corruptions are generated at ≥3τ, so at 4× tolerance a third of instances already pass
unrepaired and `NO_FIX()` scores.

## Phase 8 — M8: prompt ablation on an easier rung (2026-08-11)

**Reasoning:** test both candidate fixes at once — remove the exemplar, and reduce difficulty.

**Prompt changes made here** (all in `text_fixit/prompts/`):

| change | reasoning |
|---|---|
| `contract_batch_ablate.txt` — concrete examples → metasyntax `TRANSLATE(<part>, <axis>, <metres>)` | test whether the model was copying the exemplar |
| `system_ablate.txt` / `system_image_ablate.txt` — added a **FAULT SCALE** block | state the real magnitude range explicitly |
| `system.txt` — `"generated at 3x this tolerance"` → `${margin_x}` | a set generated at margin 1.2 would otherwise be misdescribed |
| fault ranges templated from the **instance** (`magnitude_ranges`) | hardcoding them made the ablation quote 0.08–0.20 m at a set whose real range was 0.028–0.070 m — worse than silence |
| `FIXIT_PROMPT_VARIANT` env switch in `_load()` | an ablation must not half-apply; missing variants fall back |

**Result — 120 episodes, 2×2:**

- **The ablation was not the lever.** Ablate 20%/10% vs base 17%/17% — noise.
- **It did work mechanically**: verbatim-copy rate 62% → 13%, Y-axis share 60% → 40%. The anchoring
  was real and is now fixed; it simply was not what was binding.
- **The easier instances were the lever** — Qwen went 0/185 to 10–20%.

**A trap found while building the set:** `--broken-margin` alone does **not** make a set easier. It
is only a growth floor, and the initial draw ranges already clear it — at margin 1.5 the set still
came out at median D=4.6 with 0/30 instances below the target. The real lever is the **draw range**,
so `--difficulty-scale` was added. At 0.35 the set lands at median D=1.6.

## Phase 9 — M9/M10: does scale help? (2026-08-11)

**Reasoning:** if a larger open model clears the harder rungs, the answer is "buy parameters". If
not, the task needs something these models lack. Downloaded `Qwen3-VL-32B-Instruct-FP8` (35.5 GB —
the bf16 66.7 GB would not fit 103 GB of free disk); chose dense over the same-size 30B-A3B MoE
because the MoE activates ~3B params per token and is far harder to fine-tune.

**Two harness bugs found, each of which manufactured a false model failure:**

1. **`history="full"` makes the 32B stop emitting `<act>` tags.** It wrote complete plans in prose —
   *"I will adjust both doors: translate P1 inward along X…"* — and never converted them to syntax.
   58% invalid, reparse recovering 9%. Not truncation (`finish_reason=stop`, max completion 1,660 of
   4,096). `window3` gave **0% invalid**. Without probing this, the finding would have been "the 32B
   cannot follow the protocol" — false. The 8B is insensitive to the same flag, so M6–M8 stand.
2. **`QwenVLAgent` hardcoded a 180s client timeout.** On text the 32B writes ~790 completion tokens
   (vs ~275 on images), p90 latency 402s, so **20% of turns timed out** → retries → `gave_up` →
   `COMMIT NO_FIX()`. Four of twelve episodes scored as the model declining to repair. `QWEN_TIMEOUT`
   added; the rerun scored ~3× the contaminated arm.

**Result — the complete ladder, both models, all five rungs:**

| rung | Qwen-8B | Qwen-32B |
|---|---|---|
| easy (D≈1.6) | 17% | 23% |
| standard single (D≈4.6) | 1% | 8% |
| hardened control | 4% | 0% |
| n=2 composite | 0/30 | 0/30 |
| n=3 composite | 0/25 | 0/25 |

**The cliff is a property of the task, not the model.** Both score exactly zero on all three τ=1.5%
rungs — 0/160 combined. Scale lifts the easy rungs a few points and moves nothing below them; on the
hardened control the ordering even inverts.

## Phase 10 — M11: what capability is actually missing? (2026-08-12)

**Reasoning:** the ladder says *how well* models do, not *what they cannot do*. Success rate cannot
distinguish four different failures — finding the part, choosing the action type, choosing the axis,
estimating the magnitude — and they imply four different remedies.

**Tier 1 (free, recomputed from existing logs — `text_fixit/decompose.py`):** a capability funnel.

| model | PASS | localise | type | axis | type+axis | mag median | mag ±25% |
|---|---|---|---|---|---|---|---|
| gemini-3.1-pro | 20% | 100% | 96% | 92% | **84%** | 1.01× | 71% |
| robotics-er-2 | 20% | 92% | 84% | 80% | **76%** | 1.00× | 63% |
| Qwen-8B | 4% | 72% | 60% | 44% | **32%** | 0.99× | 75% |
| Qwen-32B | 0% | 68% | 48% | 48% | **24%** | 0.41× | 0% |

**Tier 2 (new runs, 200 episodes):** show the numeric error, and remove the loop.

| model | loop, dev OFF | loop, dev **ON** | one-shot | loop adds |
|---|---|---|---|---|
| robotics-er-2 | 20% | **76%** | 16% | +4 pts |
| gemini-3.1-pro | 20% | **65%** (n=20) | 12% | +8 pts |
| Qwen-8B | 4% | **4%** | 4% | +0 pts |
| Qwen-32B | 0% | **4%** | 0% | +0 pts |

**The dissociation:** API models are **perception-limited** — the number drives their axis accuracy
80–92% → **100%** while magnitude accuracy barely moves, so the gain is diagnostic. Open models are
**diagnosis-limited** — the same number changes nothing (axis 44% → 44%), because a precise error on
a mis-identified axis is worthless.

**The loop is nearly decorative** — 4–8 points for API models, zero for open ones.

---

## Claims made and later withdrawn

Recorded because each went into the record before it was stable.

| claim | status | why it changed |
|---|---|---|
| "Qwen is compliance-bound" (M6) | **wrong** | invalid rate was a text-modality artifact; M7 measured 2–3% on batch |
| "Qwen undershoots magnitude by 0.40×" (M7) | **does not generalise** | that statistic was the largest value ever tried on a hard rung; like-for-like it is 0.99× |
| "the prompt ablation works" (M8, n=19) | **withdrawn** | base arms caught up completely by n=30 |
| "text harm is g3-specific" (M5) | **refuted** | at n=2 composition, text is 0/120 for every model |
| "the 32B closes the text gap" (M9, n=21) | **withdrawn** | settled at 17% vs 23% image by n=30 |
| "4× parameters buys nothing" (M9, n=20) | **premature** | 32B reached 8% vs 1% at full n=75 |
| "deviation gives 100%" (M11, n=4) | **withdrawn** | settled at 65–76% by n=20–25 |

The common thread: **every one was an interim reading at n<25.** A 95% Wilson interval at n=25 spans
roughly ±15 points.

## Infrastructure lessons

Three bugs in this project silently converted infrastructure failure into apparent model incapacity:
the PyBullet filename cache (M4), `history="full"` prose drift (M9), and the 180s client timeout
(M9). The last two were caught **only because** `n_api_giveup` and the invalid-action counters
existed first — they were added in M4 for exactly this reason, before anyone needed them.

## Where it stands

- **A trainable rung exists**: `instances_easy` (D≈1.6), 17–23% for both open models against 3%
  random — the only place an open model produces reward events.
- **SFT the 8B, not the 32B**: the 32B clears nothing extra, costs 4× the compute, will not
  fine-tune on 2×48 GB, and its bf16 weights do not fit the disk.
- **Blocking before any training**: `instances_easy` mixes 19 train-split and 11 test-split shapes
  with one instance per base. Training on its oracle traces and evaluating on the same set would leak
  invisibly. It needs a shape-level split plus multiple instances per shape.
- **If the goal is sequential decision-making**, the task needs redesign: the loop is worth 4–8
  points today, and composition — where a loop should matter most — is 0% for every model tested.
