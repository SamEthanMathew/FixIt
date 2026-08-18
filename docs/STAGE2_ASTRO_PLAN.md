# Stage-2: ASTRO-style SFT (LoRA)

**Status:** pipeline built and validated end-to-end. **No training has been run.**
**Date:** 2026-08-18
**Supersedes:** `docs/STAGE2_SFT_PLAN.md` — see §8.
**Implements:** `Fixit_RL.pdf` §5.2 (SFT on traces with failed attempts, feedback, backtracking) and
§7 ablations 1–4, following `ASTRO.pdf` (arXiv:2507.00417, Kim et al., AI at Meta).

---

## 1. Why ASTRO

ASTRO's thesis: Llama-3 fails to become a reasoner under RL because it has **no search prior** — it
never reflects or backtracks, so RL has nothing to amplify. The fix is a four-stage pipeline: MCTS
with a verifier → linearize the tree into a CoT that keeps the failed branches → SFT → RL.

Its controlled ablation (Table 4) is the result that matters. Same problems, same search trees, same
example count; the only difference is whether traces contain reflection and backtracking:

| | MATH-500 | AMC 2023 | AIME 2024 |
|---|---|---|---|
| Direct-SFT | 65.8 | 45.2 | 16.7 |
| **ASTRO-SFT** | **69.6** | **51.9** | 13.3 |
| Direct-RL | 79.8 | 60.5 | 27.1 |
| **ASTRO-RL** | **81.8** | **64.4** | **30.0** |

Backtrack count at test time correlates with score at r = 0.816 / 0.851 / 0.854.

This is exactly `Fixit_RL.pdf` §7 ablation 4 → 5, with a concrete recipe attached.

---

## 2. The mapping

| ASTRO | FixIt-ASTRO |
|---|---|
| math problem `x` | one broken fridge instance |
| reasoning step `s_t` | one probe, `TRANSLATE(P1, X, -0.198)` |
| state `S_t` | instance + probe log so far |
| verifier `V` | `env._evaluate_specs` → PyBullet `evaluate_repair_multi` |
| `Q` from `M=16` rollouts | `1 − min(dev/dev0, 1)` — **exact and dense, one call** |
| correct terminal | a SIMULATE returning `ALL PASS` |
| incorrect terminal | a probe whose branch dies without passing |
| ancestor jump = backtrack | abandon a hypothesis |
| *"But wait… Let's go back to where we…"* | same phrases + **`<backtrack/>`**, already in the grammar |
| no repeated wrong answer | no repeated `(part, op, axis)` cell |
| GRPO, verifiable reward | `R = R_final − λ_sim·N_sim − λ_repeat·N_repeat − λ_invalid·N_invalid` |

`<backtrack/>` was already parsed by `action_parser`, preserved by `qwen_vl._normalize()` (whose
docstring says it exists *for this SFT stage*), and logged by `run_episode`. Stage 1 built it.

---

## 3. Three adaptations forced by a continuous action space

ASTRO searches discrete reasoning steps. A repair is `(part, operation, axis, MAGNITUDE)` and the
magnitude is continuous. Three consequences, each of which silently degrades the data if ignored.

**3.1 Uniqueness is per hypothesis cell, not per action string.** ASTRO forbids two nodes with the
same incorrect *answer*. Translated literally that forbids duplicate action strings — useless, since
`TRANSLATE(P1,Y,-0.145)` and `TRANSLATE(P1,Y,-0.150)` are the same hypothesis. The unit is the
discrete cell `(part, op, axis)`; the magnitude is a refinement *within* it. That is also exactly
what `repeated-failure rate` measures in `Fixit_RL.pdf` §7.

**3.2 A magnitude refinement is not a backtrack.** Descending a refine chain is continuation. Only a
cell change is a backtrack, and the **depth of the lowest common ancestor** says which kind — which
is why the tree is three levels deep rather than flat:

- LCA is the **root** → `backtrack to part_selection`
- LCA is a **part** node → `backtrack to transformation_selection`
- LCA is a **cell** node → not a backtrack

Those are precisely the two backtrack actions in `Fixit_RL.pdf` §3.3.

**3.3 The sign is part of the magnitude.** A wrongly-signed probe makes the error worse, so the flip
(`−v`, or `1/f` for SCALE) attaches as a refinement inside the cell. Omitting it was measured to cost
**6 of 10 rotate instances** — see §5.

Also dropped: ASTRO's `Ψ'` LLM self-evaluation filter (Appendix A.1, `N=8` self-consistency votes to
reject lucky guesses). PyBullet is the verifier; a pass *is* the repair. There is no lucky guess to
filter, so `Ψ' = Ψ`.

---

## 4. Modules

| file | role |
|---|---|
| `text_fixit/astro/make_sets.py` | split-aware instance generation (train shapes vs held-out shapes) |
| `text_fixit/astro/tree.py` | ASTRO §2.2 — the search tree with Q-values |
| `text_fixit/astro/linearize.py` | ASTRO §2.3 Algorithm 1 — tree → node sequence with backtracks |
| `text_fixit/astro/verbalize.py` | ASTRO §2.4 — procedure cloning into `<think>/<backtrack/>/<act>` |
| `text_fixit/astro/build_dataset.py` | replay through a real env, emit prompt/completion JSONL |
| `text_fixit/astro/train_lora.py` | ASTRO §3.1 — LoRA SFT |
| `text_fixit/astro/serve_lora.sh` | serve the adapter for the existing eval harness |

**Every turn is an independent training example.** `loop_qwen` runs `history="window3"`, which
`GeminiAgent.act()` implements as a *stateless* single-message call. So an n-turn trace yields n
independent `(system, user) → assistant` pairs: no multi-turn masking, no conversation collator.

**Prompt parity is structural, not asserted.** `$history`, `$untried`, `$targetable` and
`$found_note` are computed from `env.history` at call time, so `build_dataset.py` steps a real
`FridgeRepairEnv` and calls the agent's own `_system_prompt` / `_step_prompt`.

**Observability invariant.** Ground truth is used for one thing only: the verifier. Every branching
decision — which part is faulty, which axis survives, what the next magnitude is — comes from
simulator output, via the arithmetic `prompts/one_error_search_text.txt` already gives the model.
Nothing in a trace is derivable only from `instance["gt_fix"]`.

---

## 5. What is measured (std30, n=30, τ=1.5%)

| | result |
|---|---|
| trees with a passing terminal | **26/30 (87%)** — ASTRO's own yield was 14.0K/20.7K = 68% |
| by fault type | translate **10/10**, rotate **9/10**, scale **7/10** |
| simulator calls per tree | mean 17.5, max 20, ~2.7 s/instance |
| traces | 101 = **26 direct (k=0) + 75 search (k≥1)** — ASTRO's 1:3 mix — **+ 4 budget-exhaustion aux** |
| examples | 571 turns (44 aux, reaching turn 11), **0 dropped** by the verification gates |
| token length | prompt p99 3,113 / max 3,173; **total max ~3,2xx**, 0 over 4,096 |
| supervision checks | COMMIT↔found_note byte-parity 101/101 · off-procedure traces 0/96 · no-op probes 0 · rounding mismatches 0 |

**Two findings from building it.**

*The sign flip is load-bearing.* Probing `ROTATE(part, A, +20)` once per axis and never trying the
other sign left rotate at **3/10** — in every failure the best probe was no better than the broken
object, so the ≥50% lock-on never fired. Adding the flip took rotate to **9/10**.

*The prompt's greedy lock-on has a local minimum on scale faults.* `deviation_mm` is mean per-vertex
displacement, so sliding an over-sized door **along the mis-scaled axis** realigns its centroid and
cuts the error by **79–91%** — a bigger drop than the correct `SCALE` probe produces. STEP 4 ("the
moment any probe cuts the error by half, the search is OVER") therefore locks onto `TRANSLATE` and
refines into a dead end. On `10867_ctrl_scale_0` that path reaches **0.618 τ** — inside the deviation
tolerance — and still fails, because the over-sized door interpenetrates. Refining the top-3 cells
instead of committing to the first costs ~4 extra calls and took scale from 6/10 to 7/10. **This is
a live hypothesis for why scale is the weakest type for the models too** (2/10 text, 4/10 image) and
is worth testing as a prompt change independently of SFT.

---

## 6. Deviations from ASTRO's hyperparameters

| ASTRO §3.1 / B.2 | here | why |
|---|---|---|
| 1 epoch, AdamW, cosine | **kept** | ASTRO trains one epoch deliberately, "to provide a better initialization for the RL stage" — same intent |
| LR **3e-6** | **1e-4** | 3e-6 is a full-finetune rate. LoRA's `B` starts at zero and would barely move in one epoch. Largest deviation, forced by the method |
| **no masking** (all tokens) | **completion-only** | ASTRO's prompt is a short math question. Ours is a ~2,800-token system prompt *identical in every example*; training on it lets boilerplate dominate the loss. `--astro-no-masking` restores the paper's behaviour |
| max seq len **8192** | **4096** | measured max is 3,211 tokens; 8192 is padding |
| full FT of 70B on 64×H100 | LoRA r=16 α=32 on one RTX 6000 Ada | hardware |

LoRA targets are **derived from the loaded model**, not hardcoded: 252 LLM Linear layers
(36 layers × 7 projections), **116 vision Linear layers excluded**. `target_modules="all-linear"`
would adapt the vision tower, re-enable its activation graph, and destabilise it.
`--print-targets` shows the list on the meta device, with no weights allocated.

---

## 7. Run book — none of this has been executed

```bash
# 0. instance sets (regenerated at the std30 regime; instances_train/test.jsonl are Aug-3,
#    tau_frac=None, pre-tracking, and not comparable).
#    HELD-OUT USES --seed 100: generation is deterministic on (base, ctype, seed), so a seed-0
#    test build would reproduce std30's 11 test rows verbatim -- the instances every prompt
#    iteration was tuned on. make_sets refuses seeds < 100 for --split test.
FIXIT_TAU_FRAC=0.015 conda run -n fixing python text_fixit/astro/make_sets.py \
    --split train --per-type 100 --out data/instances_astro_train.jsonl
FIXIT_TAU_FRAC=0.015 conda run -n fixing python text_fixit/astro/make_sets.py \
    --split test  --per-type 35 --seed 100 --out data/instances_astro_heldout.jsonl

# 1. datasets (~2.7 s/instance => ~40 min for 900; expect ~17k examples with the aux traces).
#    build_dataset refuses non-train rows unless --expect-split any; the direct arm is built
#    from the SAME trees.
FIXIT_TAU_FRAC=0.015 conda run -n fixing python text_fixit/astro/build_dataset.py \
    --instances data/instances_astro_train.jsonl \
    --out data/sft/astro_train.jsonl --report
FIXIT_TAU_FRAC=0.015 conda run -n fixing python text_fixit/astro/build_dataset.py \
    --instances data/instances_astro_train.jsonl --arm direct \
    --out data/sft/direct_train.jsonl --report

# 2. STOP THE vLLM SERVER NOW -- the overfit gate in the next step is a full GPU load, and with
#    the stage-1 server resident GPU0 has ~18 GB free against a ~21 GB need. GPU1 carries
#    another user's job; do not use it.
# 3. gates before any real run
conda run -n qwenvl2 python text_fixit/astro/train_lora.py --print-targets
conda run -n qwenvl2 python text_fixit/astro/train_lora.py \
    --data data/sft/astro_train.jsonl --overfit 32 --yes      # loss must reach ~0

# 4. train both arms. MATCH TRAINING STEPS, not example counts: the direct arm has ~4x fewer
#    examples from the same trees, so scale --epochs so steps (= examples x epochs / 8) match
#    the astro arm's. ASTRO count-matched its Direct arm; steps-matching is our equivalent.
conda run -n qwenvl2 python text_fixit/astro/train_lora.py \
    --data data/sft/astro_train.jsonl --out runs_sft/astro_qwen8_text --yes
conda run -n qwenvl2 python text_fixit/astro/train_lora.py \
    --data data/sft/direct_train.jsonl --out runs_sft/direct_qwen8_text \
    --epochs <astro_examples/direct_examples> --yes

# 5. evaluate. THREE seeded runs per arm (temperature 0.7 single runs swing +-2/30 on this
#    benchmark -- PROMPT_ITERATION_LOG documents 11->9/30 on identical configs).
#    serve_lora.sh refuses a busy port; after startup confirm the adapter is live:
#      curl -s http://127.0.0.1:8001/v1/models | grep '"astro"'
bash text_fixit/astro/serve_lora.sh text_fixit/runs_sft/astro_qwen8_text
for i in 1 2 3; do
  FIXIT_TAU_FRAC=0.015 FIXIT_PROMPT_SET=one_error_search \
  conda run -n fixing python text_fixit/run_trials.py --agent loop_qwen --model astro \
      --modality text --deviation on --instances data/instances_astro_heldout.jsonl --sweep \
      --budget 10 --max-actions 1 --run astro_sft_heldout_text_r$i
done
# the paired BASE arm, same instances, same three seeds (serve the base with serve_qwen.sh):
bash text_fixit/serve_qwen.sh   # after stopping the adapter server
for i in 1 2 3; do
  FIXIT_TAU_FRAC=0.015 FIXIT_PROMPT_SET=one_error_search \
  conda run -n fixing python text_fixit/run_trials.py --agent loop_qwen \
      --model Qwen/Qwen3-VL-8B-Instruct \
      --modality text --deviation on --instances data/instances_astro_heldout.jsonl --sweep \
      --budget 10 --max-actions 1 --run astro_base_heldout_text_r$i
done
conda run -n fixing python text_fixit/funnel.py astro_sft_heldout_text_r1 astro_base_heldout_text_r1
```

**Analysis protocol (power is the binding constraint).** At n=105 over 13 correlated bases, the
minimal detectable success delta is ~+18 points unpaired — and **+29–33 after deflating for
per-base correlation** — while ASTRO's own SFT-stage effect was +4 to +7. So: (1) every
comparison is **paired on shared instances** (McNemar over the 105, pooling the 3 seeds), which
buys back most of the power; (2) report per-base clustered intervals, never raw Wilson alone;
(3) treat the funnel (part/type/axis vs chance) as the primary endpoint, as before — it has
per-action rather than per-episode n; (4) a delta smaller than the paired CI is reported as
"not resolved at this n", not as a null.

**Ablation arms**, mapping onto `Fixit_RL.pdf` §7 and ASTRO Table 4:

| arm | how |
|---|---|
| 1. final-answer-only | target `gt_fix` directly (the old plan's design) |
| 2. traces, no failed branches | `--arm direct` — the constructed clean arm: winning cell, correct sign, refine chain only. **Not** `--k-mix 0`: the review measured 21/26 shortest-path traces containing failed probes and 10/26 containing sign-flip recoveries, so the naive k=0 draw is not ASTRO's Direct-SFT. Steps-matched to arm 4 via `--epochs` |
| 3. failed branches, no backtrack labels | strip `<backtrack/>` and the reflection phrases |
| 4. **full ASTRO** | default `--k-mix 0,1,1,2` + budget-exhaustion aux traces |
| 5. RL after SFT | Stage 3 |
| 6. RL without SFT | Stage 3 |

Arms 2 vs 4 is ASTRO's Table 4 reproduced on this task, and it is the experiment that decides
whether the search prior does anything here.

---

## 8. What this supersedes in `STAGE2_SFT_PLAN.md`

That plan was written 2026-08-16 16:56. Three commits landed after it (`ece5a80`, `72795dd`,
`c852058`) and invalidate its premise.

| it says | actually |
|---|---|
| Qwen3-VL-8B 0–1/30, prompting exhausted | **11/30 image, 7/30 text** with `one_error_search` |
| magnitude 0.15–0.57×, "second gate at chance" | **1.00×** — that gate is closed |
| the bottleneck is perception | the fix was *using the simulator as a measuring instrument*, not better perception |
| gold target = `SIMULATE <gt_fix>` every turn | that is ASTRO's **Direct-SFT control**, and the arm that loses. Demoted to ablation 1 |
| `max_length` 10240 | measured max **3,211** |
| disk is the binding constraint | `_hard_*.urdf` are **9 KB**; 900 instances ≈ 8 MB. 87 GB free |
| `perception_probe.py:133` bug | already fixed |

Still valid and carried over: held-out split **by shape**, eval power **n ≥ 90**, LoRA with the ViT
frozen, the named-target-modules warning, the overfit-32 gate, saving the processor with the adapter,
and the honest framing that a null result is a real result.

---

## 8b. Adversarial review, 2026-08-18 — findings and what changed

A six-area review (expert math, trace quality, replay parity, training stack, serving, methodology)
with empirical verification. Confirmed and fixed in code:

- **Split guards** (was: nothing kept test shapes out of training; `build_dataset` even defaulted
  to std30, which is 19 train / 11 test). `build_dataset` and `train_lora` now refuse non-train
  rows; `make_sets` refuses `--split test` below seed 100 (seed-0 test rows are byte-identical to
  std30's — the prompt-tuning benchmark).
- **SCALE call format** (24/104 COMMIT targets byte-mismatched the `$history`/found_note text in
  their own prompt: local `.5f` vs `format_call`'s `.6f`). `node.call` now rendered by
  `format_call` from the parsed spec. All 101 pass-COMMIT completions verified byte-contained in
  their prompt's found_note block; targets are two-line as the prompt demands.
- **No-op probes + rounding** (SCALE ratio-1.0 probes asserted a false "not the fault" inference;
  the rounded dev0 broke "exactly as before" on 10 turns). Ratios near 1 fall back to 0.85; exact
  `root.dev` used throughout. Both counters now 0.
- **Procedure order** (18/78 search traces probed rotate/scale then returned to translate,
  contradicting STEP 1 in the same prompt). Failed-branch sampling is strictly limited to
  operations not after the target's, emitted in sweep order: now 0/96.
- **Coverage** (19.3% of real eval turns sit at index ≥9 with zero training mass; no
  commit-best-attempt or late-budget examples existed). Unsolved trees now emit budget-exhaustion
  aux traces ending in the prompt's commit-lowest-error rule (std30: +4 traces, +44 examples,
  max turn 11).
- **Incoherent think on high-Q dead branches** (a 90%-drop branch was abandoned with no stated
  reason). `_evidence` now cites the disqualifying criteria (interpenetration / door no longer
  closes) the observation already shows.
- **Ops**: `run_trials` manifests recorded `prompt_set: one_error` (a set that no longer exists)
  when the env var was unset — now records the agents' real default; `evaluate.py` refuses
  `--model` with a mixed qwen+gemini agent list instead of silently routing one side;
  `serve_lora.sh` refuses a busy port and documents the adapter-liveness check;
  `meta.trace_id` added so per-trace audits don't collide.

Verified as **non-issues**: vLLM 0.16.0 serves LoRA on Qwen3-VL (`SupportsLoRA` declared — no
merge fallback needed); the vision tower's Linear names (`qkv/proj/linear_fc1/linear_fc2`) cannot
collide with the 7 LLM LoRA suffixes; trace lengths (max 8 sims) sit safely under budget 10.

Open, by design: the **mechanism-transfer question** (ASTRO's gain is in-context; window3 trains a
per-state policy — arm 3 vs 4, off-trace probe recovery, and budget-20 runs are the discriminators)
and **expert coverage** (26/30; the trained distribution is easier than eval — the aux traces
mitigate, not remove).

## 9. Bugs fixed while building this

- **`run_trials.py` / `evaluate.py` `--model` ignored the qwen agents.** Both set `GEMINI_MODEL`,
  but `QwenVLAgent` reads `QWEN_MODEL`. `--agent loop_qwen --model <adapter>` would have silently
  evaluated the **base** model — i.e. reported that SFT did nothing. Now routed by agent name.

---

## 10. Risks

- **SFT may teach output priors rather than search.** Detection is unchanged from the old plan:
  `funnel.py` measures part/type/axis against chance and the by-shape split catches memorisation.
  A null result is reportable.
- **Off-policy.** ASTRO's traces come from the policy's own MCTS; ours come from a scripted expert,
  so the states are not the ones the model reaches. ASTRO has the same property after SFT and fixes
  it with RL; the DAgger round in the old plan §9 remains the cheaper intermediate option.
- **Expert coverage is 87%, and it is not uniform** — scale 7/10. Training data is therefore
  *easier* than the benchmark, which biases toward optimism on the SFT loss and away from it on
  held-out success.
- **Statistical power.** n ≥ 90 held-out, as before. Do not skip it.
