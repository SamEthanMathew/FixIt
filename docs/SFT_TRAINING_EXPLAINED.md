# How the two SFT trainings work: Direct-SFT vs ASTRO-SFT

**Companion to** `docs/REPORT_2026-08-19_astro_sft_results.md` (the results) and
`docs/STAGE2_ASTRO_PLAN.md` (the plan). This document explains the *mechanics*: what each training
actually optimizes, what a training example physically looks like, and why the two arms produce
such different models from the same source material.

Headline for orientation: **base 6.7% → Direct-SFT 36.5% → ASTRO-SFT 78.1%** repair success on
fully held-out shapes.

---

## 1. The common substrate — what both trainings share

Everything in this section is identical between the two arms. The arms differ *only* in the
content of the assistant turns they imitate.

### 1.1 The task the model is being trained for

The agent lives in a closed loop with a physics simulator. Each episode: one broken fridge, one
hidden fault (a part translated, rotated, or scaled wrongly). Per turn the model emits one action —

```
<think>…reasoning…</think>
<act>SIMULATE TRANSLATE(P1, Y, -0.145)</act>
```

— the simulator applies it *fresh to the original broken object* (attempts never stack), and
reports the residual error in millimetres plus pass/fail criteria. The episode is solved only if a
committed repair puts the faulty part within tolerance (τ = 1.5% of the door diagonal), the door
still closes, and nothing interpenetrates. Budget: 10 SIMULATEs.

### 1.2 Every turn is an independent training example

The eval agent (`loop_qwen`) runs in `window3` mode: a **stateless** call per turn. The harness
re-renders everything the model needs into each prompt — the system prompt (procedure, part
table), and a step prompt containing the full probe log:

```
Every probe you have run so far, with its result - never repeat one:
  TRANSLATE(P0, X, -0.21385) -> off 302mm
  TRANSLATE(P0, X, 0.21385) -> off 302mm

You may ONLY target these parts: P0, P1
Operation/axis combinations you have NOT yet probed: P0: TRANSLATE/Y, …
```

Because the state is externalized like this, a k-turn episode decomposes into k independent
`(system, user) → assistant` pairs. There is no multi-turn masking and no conversation collator —
plain single-turn SFT, which is also exactly the input distribution the model sees at evaluation.

**Prompt parity is structural, not asserted.** The dataset builder does not format prompts from a
template; it *replays* each trace through a real `FridgeRepairEnv` and calls the same
`_system_prompt` / `_step_prompt` methods the live agent calls. Whatever the harness would show
the model at eval — the `$history` block, the untried-combinations list, the ruled-out-parts
deduction, the found-note commit banner — is byte-identically what training conditions on.

### 1.3 The teacher: a scripted expert, no LLM anywhere

Training data comes from a deterministic search expert that executes the procedure the system
prompt itself prescribes:

1. **Identify the part** — probe each candidate once; the faulty part is the one whose probe
   *changes* the reported error (a healthy part cannot move the worst-faulty-part metric).
2. **Sweep hypotheses** — the nine (operation, axis) cells on that part, translate → rotate →
   scale.
3. **Flip on rise** — a probe that made the error worse gets its sign flipped (reciprocal for
   scale): the sign lives in the magnitude, not the hypothesis.
4. **Refine** — any cell that closed ≥50% of the error gets its magnitude iterated by the secant
   rule `V·A/(A−B)` (log-space for scale, since factors compose), top-3 cells, until PASS or
   plateau.

The expert reads **only simulator observations** — never `gt_fix`. Ground truth is used for
exactly one thing: the verifier that says whether a candidate PASSes. Every number in every trace
is therefore *derivable from what the model can see*, which is what makes the reasoning text
verifiable rather than post-hoc. The expert solves 233/300 training instances (78%).

Each solved instance yields a **search tree**: virtual root → virtual part nodes → hypothesis
cells (one probe each) → refinement chains. Every simulated node carries its true residual error.

### 1.4 The optimization itself

Identical for both arms:

| | |
|---|---|
| base model | Qwen/Qwen3-VL-8B-Instruct |
| adapter | LoRA r=16, α=32, dropout 0.05, on all 252 language-tower `nn.Linear`s; vision tower excluded and frozen |
| trainable | 43.6M / 8.81B parameters (0.495%) |
| loss | cross-entropy on **completion tokens only** — the ~2,800-token prompt is masked out, so the gradient carries only "given this state, produce this turn" |
| schedule | AdamW, LR 1e-4, cosine, 3% warmup, bf16, bs 1 × grad-accum 8, max_length 4096 |
| steps | **matched**: 5,346 examples × 1 epoch (astro) ≈ 531 × 10 epochs (direct) ≈ 640 optimizer steps each |

The steps-matching matters: ASTRO's own ablation matched dataset sizes between its arms, and
without it the comparison confounds "search prior" with "more gradient updates."

---

## 2. Direct-SFT — cloning answers

### 2.1 What a direct trace contains

For each solved tree, take **only the winning path**: the correct hypothesis cell entered at its
first strictly-improving probe, plus its refinement chain, plus the commit. No other-part probes,
no failed cells, no sign flips. This is ASTRO's "Direct-SFT" control — *"solutions that do not
contain any self-reflection or backtracking."*

A real one, in full (instance `12250_ctrl_scale_0`, a mis-sized door — 3 turns):

```
turn 1  <think>The object is off by 191 mm and nothing has been probed yet.
        I will start with SCALE(P1, Y, 0.850000).</think>
        <act>SIMULATE SCALE(P1, Y, 0.850000)</act>

turn 2  <think>SCALE(P1, Y, 0.850000) cut the error from 191 mm to 83 mm, closing 56% of it.
        But wait, is this the right repair so far? Hmm... This looks like the right repair
        so far. Factor 0.85 closed 107 mm of the 191 mm error; a multiplier compounds, so the
        full correction is that factor raised to the power 191 mm/107 mm = 1.78:
        SCALE(P1, Y, 0.749192).</think>
        <act>SIMULATE SCALE(P1, Y, 0.749192)</act>

turn 3  <think>A SIMULATE reported ALL PASS, so this is the repair.</think>
        <act>COMMIT SCALE(P1, Y, 0.749192)</act>
```

Note it is not *answer-only*: it still shows the refinement arithmetic. What it never shows is
**being wrong** — no probe in any direct trace raises the error, targets the wrong part, or tests
the wrong operation. 233 traces → 531 examples.

### 2.2 What gradient descent extracts from that

The model sees thousands of (state → action) pairs in which the very first probe is always
correct. The learnable regularities are:

- the mapping from the *initial* observation to the right repair — for scale faults this is
  genuinely learnable, because the mis-sized door's dimensions sit in the geometry block and the
  ratio to its sibling *is* the answer;
- the refinement arithmetic once a probe lands;
- the commit protocol.

What is **not in the data at all**: any state in which a previous probe failed. At eval, the
model's first guess is often wrong — and every subsequent prompt then contains a history block
unlike anything in its training distribution.

### 2.3 What the trained model actually does

Exactly what its data taught: it *names* a repair immediately (fault-type identification ≈ 98%,
full part+type+axis diagnosis 60% — better than the astro arm's 41%!), commits fast
(2.7 sims/solve), and emits zero backtrack tags. On **scale** faults, where the answer is readable
from the state, this is a winning strategy: **74%**, better than the astro arm. On translate and
rotate, whose magnitudes are *not* readable and must be measured through probes, it diagnoses
correctly, misses on magnitude (ratio 1.2, best deviation stuck ~3.2τ), cannot recover (27%), and
scores **16% / 19%**.

Direct-SFT builds a **pattern reader**.

---

## 3. ASTRO-SFT — cloning the search

### 3.1 From tree to trace: linearization with the failures kept

Following ASTRO's Algorithm 1, each trace is built by sampling **k failed branches** (k ∈ {0,1,1,2}
per tree — one "direct" draw plus three search draws, ASTRO's own mix) and merging them *before*
the winning branch. Where the merged sequence jumps from a dead branch back to an ancestor, that
is a **backtrack** — and the depth of the lowest common ancestor picks its kind:

- jump across parts (LCA = root) → `backtrack to part_selection`
- jump within a part (LCA = part node) → `backtrack to transformation_selection`
- a magnitude step inside one hypothesis → *not* a backtrack (continuous-action adaptation:
  the sign flip and the secant step are refinements, not new branches)

Three invariants keep the traces honest: the sequence always ends at a verified PASS; no
hypothesis cell `(part, op, axis)` is ever visited twice; and failed branches are sampled in
procedure order (never probing rotate before the translate sweep the prompt mandates).

### 3.2 Verbalization: ASTRO's reflection markers, computed evidence

Each node becomes a turn. At a backtrack, ASTRO's hard-coded reflection phrases are stamped in,
with the evidence *computed from the two measured error values* — never free-written:

```
turn 3  <think>But wait, is this the right repair so far? Hmm...
        TRANSLATE(P0, X, 0.21385) raised the error from 214 mm to 302 mm.
        This does not look like the right repair so far.
        Let's go back to where we chose the operation and axis for P0.
        I will test TRANSLATE on axis Y next: TRANSLATE(P0, Y, -0.21385).</think>
        <backtrack/><act>SIMULATE TRANSLATE(P0, Y, -0.21385)</act>
```

(Real example, `12248_ctrl_rotate_0`, turn 3 of 11.) When a probe *fails for a reason other than
deviation* — the door jams, parts interpenetrate — the evidence sentence says so, which is what
keeps the chain-of-thought coherent on the branches where a wrong hypothesis closes 90% of the
error and must still be abandoned.

### 3.3 Coverage the direct arm cannot have

Two additions target the states that decide hard episodes:

- **Recovery states.** 665 of 898 traces contain ≥1 failed branch, so the model trains on prompts
  whose history block shows dead hypotheses — the exact distribution it faces at eval after its
  own first guess misses.
- **Budget-exhaustion traces (66).** From the 67 instances the expert *couldn't* solve, a trace of
  exactly 10 failing probes ending in the prompt's own rule:

  ```
  <think>The budget is spent and no SIMULATE reported ALL PASS, so I commit the attempt
  with the lowest error.</think>
  <act>COMMIT ROTATE(P0, X, -20.0000)</act>
  ```

  Without these, "late in the budget and still failing" — where 19% of real eval turns live — had
  zero training mass, and the commit-best-attempt protocol had no example anywhere.

Total: 898 traces + 66 aux → **5,346 examples**, of which 898 turns carry `<backtrack/>`.

### 3.4 What gradient descent extracts from that

The same (state → action) objective now covers a different state space. The learnable
regularities include everything Direct-SFT gets, *plus* the transition function of the search:

- error unchanged → that part is healthy, switch parts
- error rose → flip the sign within the same hypothesis
- error rose after both signs → abandon the cell, emit `<backtrack/>`, pick the next untried cell
  in procedure order
- error halved → stop exploring, iterate `V·A/(A−B)` on the same cell
- ALL PASS in the log → commit that exact action, verbatim
- budget exhausted → commit the lowest-error attempt

One honest subtlety (documented in the plan §8b): this is **not** ASTRO's in-context search.
ASTRO's model reflects and backtracks *inside one long generation*; ours is stateless per turn, so
a turn's reasoning never re-enters later context — the harness's rendered history carries the
memory. Within a single turn the reflection text still causally precedes (and conditions) the
action tokens, but across turns what is being trained is a **state-conditioned search policy**.
The `<backtrack/>` tag doubles as an auxiliary prediction target — emitting it correctly requires
internally classifying "my current hypothesis just died."

### 3.5 What the trained model actually does

It *measures*. On held-out shapes it probes, reads the error, flips, abandons, refines — emitting
621 backtrack tags across 315 episodes (base and direct: zero) — and recovers from a failed first
probe **77%** of the time (base 6%, direct 27%). Its magnitudes come out calibrated (ratio 1.00;
median best deviation 0.12τ, well inside tolerance). Result: **100%** on translate (where the
reported error *is* the magnitude), **82%** on rotate, 52% on scale — **78.1%** overall, which is
its teacher's own coverage, reached almost exactly.

ASTRO-SFT builds a **measuring instrument**.

---

## 4. The one-table summary

| | Direct-SFT | ASTRO-SFT |
|---|---|---|
| trace content | winning path only | winning path **+ failed branches + backtracks + exhaustion** |
| teaches | state → answer (+ refinement) | state → next experiment (the search transition function) |
| states covered | "first guess is right" | "first guess was wrong, budget draining, hypothesis dead" |
| behavioural signature | fast commit, 2.7 sims, 0 backtracks | probe–measure–recover, 5.1 sims, 621 backtracks |
| diagnosis (all-3, chance 5.6%) | **60%** | 41% |
| magnitude calibration | 1.2× | **1.00×** |
| recovery after failed 1st probe | 27% | **77%** |
| success: translate / rotate / scale | 16 / 19 / **74** | **100 / 82** / 52 |
| **overall** | 36.5% | **78.1%** |

**The unifying principle:** each arm is exactly as good as the epistemic situation its traces
rehearse. Scale faults are *readable* — the size ratio is in the observation, so answer-shaped
supervision suffices and Direct-SFT wins there. Translate and rotate magnitudes are *not in the
state* — they exist only in probe feedback — and supervision with the measurement process
amputated cannot teach measuring. The search prior pays precisely where the answer must be
obtained by experiment. That is ASTRO's Table-4 claim (search traces > clean traces, theirs +4
points) reproduced at **+42 points**, with a per-fault-type decomposition that says *when* it
holds and when it doesn't.

**What this sets up:** a combined arm (astro traces + direct's ratio-read scale repairs — the
profiles are complementary), and Stage-3 RL, which per ASTRO's thesis amplifies a search prior —
a prior this model now measurably has.

---

## 5. Pointers

- results & statistics: `docs/REPORT_2026-08-19_astro_sft_results.md`
- design & review: `docs/STAGE2_ASTRO_PLAN.md` (esp. §3 continuous adaptations, §8b review)
- code: `text_fixit/astro/{tree,linearize,verbalize,build_dataset,train_lora}.py`
- datasets: `text_fixit/data/sft/{astro_train,direct_train}.jsonl` (+ manifests)
- adapters: `text_fixit/runs_sft/{astro,direct}_qwen8_text/`
- curves: wandb `r-pad/fixit-astro-sft`
- presentation page: `docs/astro_sft_pipeline.html`
