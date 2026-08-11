# Experiment (M6) — The Two-Fault Rung

**Date written:** 2026-08-10 (predictions below are pre-registered — recorded before any model was run)
**Author:** FixIt / Stage-1 closed-loop repair
**Status:** PLANNED — not yet generated, not yet run
**Code state:** `text_fixit/` at the commit recorded in each run's `manifest.json`
**Predecessors:** M4 `docs/EXPERIMENT_2026-08-09_composite_faults.md`; M5 `runs/_analysis/m5_reveal_fixable.{md,json}`

---

## 1. Why this experiment

The benchmark has a hole in the middle. Measured on the same hardened instances (τ=1.5%,
off-grid magnitudes, budget 10, deviation OFF):

| difficulty | success | source |
|---|---|---|
| **n=1** single fault | 4–28% | M5 (`m5_reveal_fixable`) |
| **n=2** | *not built* | — |
| **n=3** composite | **0/200** | M4 (`m4_final`) |

n=1 still discriminates between models and contracts. n=3 is a wall: zero for both models, both
contracts, both modalities, and still zero at 3× tolerance, with `ever_simulated_a_pass` = 0%.
Nothing measurable lives between them.

Two consequences, and they are the reason to run M6 before anything else:

**No method can show partial progress.** A trained policy that is genuinely better than
off-the-shelf has nowhere to demonstrate it — it either clears a 0% wall or it does not. A
benchmark whose only rungs are "saturating" and "impossible" cannot rank methods, which is the
purpose M4 assigned to the composite set.

**H3 was never tested.** M4's two-door vs one-door comparison was confounded by construction: at
n=3, a `composite_2door` instance always contains a door carrying only ONE sub-fault, which is far
easier to move toward tolerance than the one-door arm's door carrying all three. M4 declined to make
a claim. At n=2 the arms can be matched on action count, which makes the assignment burden
measurable for the first time.

M4's own closing section asked for this rung. M5 now says how to run it.

## 2. What M5 contributed to this design

M5 re-ran the hardened single-fault control with the part table's `role`/`fixable` columns
REVEALED (hard render and multi-fault hint still on), and added the `stack` contract that M4 had
skipped as redundant for a one-action fix. 200 episodes, 12 conditions, 0 API give-ups.

| condition | M5 (fixable shown) | M4 (fixable hidden) |
|---|---|---|
| er batch image | 20% | 20% |
| er batch text | 20% | 16% |
| er stack image | **24%** | — |
| er stack text | **24%** | — |
| g3 batch image | 20% | 12% |
| g3 batch text | 4% | 4% |
| g3 stack image | **28%** | — |
| g3 stack text | 4% | — |

Three findings carry into M6:

1. **`reveal_fixable` is inert.** Batch arms move by 0, +1, +2 and 0 episodes out of 25. It is not a
   meaningful difficulty knob, so M6 pins it revealed rather than spending matrix width on it.
2. **`stack` beats `batch`, and M4's redundancy assumption was wrong.** For a single fault the two
   contracts are not equivalent: stack lets the agent iterate on one fault instead of re-issuing a
   blind full correction. g3-image goes 20% → 28%, and `deviation_closed` flips from −3% to
   **+25%** — the first positive value anywhere in this project — with `made_worse` 52% → 28%.
   This comparison is internally controlled (both M5 arms share `reveal_fixable=True`).
3. **The text penalty is model-specific, not a property of the symbolic channel.** g3 is destroyed
   by text (4% in both contracts, `deviation_closed` −81% batch / −63% stack, `made_worse` 88%/76%)
   while er is unharmed (20%/24%, matching its own image scores exactly). M4 read H5 as "text is
   harmful under composition"; on a *single*-fault task it is one model failing to use it.

**Carry-over caveat.** All 12 M5 manifests record `git_commit e58b2516` (the M4-results commit), but
their `argv` shows `--reveal-fixable`, a flag that only exists in `da54f09`. The runs were launched
from an uncommitted working tree and the code committed afterwards, so the recorded revision is wrong
for every M5 run. The M4 control manifests separately log the three switches as `null` (they predate
the split) with `hard=true`, so their `reveal_fixable=False` is inferred from the old preset
semantics rather than read off the log. Both facts are why the M4↔M5 comparison above is stated as
directional. M6 must be launched from a committed tree.

## 3. What changes

### 3.1 The instance set

`data/instances_2fault.jsonl` — **30 instances, 30 distinct fridge bases**, each with **exactly 2
sub-faults**, under the identical hardening knobs as M4/M5 (continuous off-grid magnitudes,
`FIXIT_TAU_FRAC=0.015`, hard render, multi-fault hint):

- **15 × `2fault_1door`** — both sub-faults on a single door
- **15 × `2fault_2door`** — one sub-fault on each of two doors

Both arms need exactly two correct actions. The only thing that differs is whether the agent must
also assign the faults to the right parts. That is the H3 ablation M4 could not run.

### 3.2 Fault-type pairs are stratified, not incidental

With 2 of the 3 types there are three pairs: **T+R, T+S, R+S**. M5's per-type tables show the two
models are lopsided in *opposite* directions:

| | rotate | scale | translate |
|---|---|---|---|
| er, stack text | **0/8** | 3/8 | 3/9 |
| g3, stack image | 3/8 | 3/8 | **1/9** |

So *which* two faults compose may matter more than that there are two. Each arm is built with 5
instances per pair (5 × 3 = 15). At n=5 per cell this detects only a gross effect, and the doc
should not claim more than that.

### 3.3 Fixed, not varied

`reveal_fixable=True` throughout (M5 §2.1). `hard_render=True`, `multi_fault_hint=True`, budget 10,
deviation OFF, τ=1.5%, `loop_gemini_full`, thinking dynamic, `max_output_tokens=32768`.

### 3.4 A third model: Qwen3-VL (reduced arm)

M6 adds **`Qwen/Qwen3-VL-8B-Instruct`**, served locally by vLLM (`text_fixit/serve_qwen.sh`, port
8001, `qwenvl` conda env), at a reduced episode count. This is not a fourth ablation axis — it is the
**pre-training baseline for the model that Stage-2 will actually fine-tune**. Everything measured so
far is a frontier API model that cannot be trained; Qwen is the one that can, so its position on the
n=2 rung is the number the RL work will be judged against.

The comparison is prompt-clean by construction: `QwenVLAgent` inherits template filling, the
window3/full history modes, the image-history window and the oneshot rewrite from `GeminiAgent` and
overrides only the transport, so a `loop_qwen_full` run is prompt-identical to `loop_gemini_full`.

**Slice: `stack` contract, both modalities, the full 30 instances = 60 episodes** (half of the 120 a
full model arm receives). `stack` because it is M5's winner and the MDP framing Stage-2 needs; both
modalities because H5's model-specificity is the live question and an open-weight VLM is a genuinely
new data point on it. Instance count is kept at 30 so each Qwen cell has the same power as a Gemini
cell — the reduction comes out of the contract axis, not the sample size.

If a cheaper probe is wanted, halve to 15 instances (stratified: keep the 1door/2door split and the
type-pair balance) for 30 episodes, and record that one episode is then worth 6.7pp.

### 3.5 Two harness gaps that must be closed before the Qwen arm runs

Both are in `agents/qwen_vl.py` and both would corrupt the integrity story M4 §10 relies on.

**1. `QwenVLAgent._call` never populates `self.last_meta`.** `GeminiAgent._call` assigns
`self.last_meta = meta` (gemini.py:293) carrying latency, usage, finish reason, per-attempt errors
and the `gave_up` flag; the Qwen override (qwen_vl.py:105) returns the fallback string without
touching it, so `last_meta` stays `{}` from `__init__`. Consequences:

- `run_episode.py:90` checks `last_meta.get("gave_up")`, so **`n_api_giveup` is always 0 for Qwen**;
- `turns.jsonl` records `latency_s`, `usage` and `finish_reason` as `null`, and `logger.raw()` is
  gated on `if meta:` so **no `raw/` log is written at all**;
- most seriously, a dead or OOM'd vLLM server returns `<act>COMMIT NO_FIX()</act>` for every turn,
  which is **indistinguishable from the model genuinely giving up** — the exact confusion
  `n_api_giveup` was introduced to prevent. A whole condition could score 0% from a crashed server
  and look like a legitimate result.

Fix by mirroring Gemini's meta dict (attempts, errors, latency, `gave_up=True` on exhaustion) before
running anything at scale.

**2. `max_tokens` defaults to 1536, against Gemini's 32768.** M4 §5 raised the Gemini cap precisely
because composite instances provoked ~15.7k thought tokens and a starved `<act>` came back empty or
`MALFORMED_FUNCTION_CALL`. Qwen3-VL-Instruct has no separate thinking channel, so its `<think>` block
is ordinary output competing for the *same* 1536 tokens as the `<act>` line. On a 2-fault instance
that is a plausible truncation point, and a truncated turn scores as an invalid action — i.e. as a
model failure when it is a harness cap. Raise the cap (the server is started with
`--max-model-len 32768`, so there is headroom) and report `invalid_action_rate` and any truncated
finish reasons alongside the headline number.

**Launch note.** `evaluate.py --model` sets `GEMINI_MODEL` only; the Qwen backend reads `QWEN_MODEL`
and `QWEN_BASE_URL` from the environment. Passing `--model Qwen/...` will be silently ignored. Start
the server first (`bash text_fixit/serve_qwen.sh`) and confirm it answers before launching.

## 4. Solvability

Unchanged from M4 §3 and enforced by the same gates. `gt_fix_sequence` is the corruption list
REVERSED with each spec inverted; `canonical.part_centroid` / `canonical.scale_pivot` are recomputable
from current geometry, so the inverse is expressible in the agent's parameter-free action space.

**The scale-first ordering constraint still applies and is not optional.** `corruption._edit_scale`
multiplies `<mesh scale>` in the mesh frame, before the visual origin's `rpy`; once a rotation has
put a non-zero `rpy` on a part, the recomputed pivot diverges by up to 0.13 m and the oracle cannot
restore the part. The generator sorts scale first on each part so its inverse runs last. This matters
for the **T+S and R+S** pairs specifically — the T+R pair is the only one that never trips it.

## 5. Generator work required

`instances_hard.py` currently hardcodes three sub-faults, one of each type (`CTYPES`,
`build_composite`). Needed:

- parameterize the sub-fault **count** and the **type subset** per instance (draw a pair, not all three);
- arm sizes `N_ONE_DOOR` / `N_TWO_DOOR` → 15/15, level names `2fault_1door` / `2fault_2door`;
- keep the `sorted(..., key=lambda tc: tc[0] != "scale")` scale-first sort verbatim;
- gates 1–6 carry over unchanged. Gate 5 (necessity) now drops 1 of 2 inverses — applying a single
  inverse must still leave ≥ `BROKEN_MARGIN`×τ, which remains a meaningful test.

**Generation risk: base-shape scarcity.** The `2fault_2door` arm needs bases with ≥2 doors that pass
gate 3. Exactly 15 such bases exist today (they are M4's `composite_2door` bases). Reuse across sets
is fine, but within-set distinctness is asserted, so the `1door` arm must draw 15 *further* distinct
bases from a 43-shape pool where 17 bases are already shared between `instances_hard` and
`instances_control`. If 30 distinct bases cannot be assembled, **fall back to 12+12 and record the
reduction** — do not silently reuse a base.

## 6. Run matrix

**300 episodes** — 240 for the two API models, 60 for the reduced Qwen arm.

| set | n | contract | modality | model | agent | episodes |
|---|---|---|---|---|---|---|
| 2fault | 30 | batch + stack | text + image | `gemini-3.1-pro-preview` | `loop_gemini_full` | 120 |
| 2fault | 30 | batch + stack | text + image | `gemini-robotics-er-2-preview` | `loop_gemini_full` | 120 |
| 2fault | 30 | **stack only** | text + image | `Qwen/Qwen3-VL-8B-Instruct` | `loop_qwen_full` | **60** |
| oracle | 30 | batch + stack | text | — | `oracle` | local |
| random | 30 | batch + stack | text | — | `random` | local |

Shard the API arms with `--shard I/N` as in M4/M5. The Qwen arm is local and unsharded; it needs the
vLLM server up (§3.5) and does not consume API quota, so its cost is GPU wall-clock only.

Run naming: `m6_<model>_<contract>_<modality>` (`g3`/`er`/`qw`), so `summarize_runs.py --group m6`
picks all of them up and merges shards automatically.

## 7. Metrics — and one comparison that must NOT be made

Standard per-condition tables via `summarize_runs.py --group m6`. The group-discovery block is now
prefix-driven, so adding `GROUPS["m6"]` is the only change needed.

**H3 is reported on `PASS` and `deviation_closed` only.** Both are whole-object measures and both
arms need two correct actions, so they are comparable. **`parts_within_tol` is not comparable across
the arms** — its denominator is 1 faulty part in the `1door` arm and 2 in the `2door` arm — and it is
exactly the metric that produced M4's spurious "two-door looks easier" reading. It stays in the table
for continuity and must not be cited in the H3 verdict.

## 8. Pre-registered predictions

Written before generation and before any model run.

- **H1 — n=2 lands strictly between the rungs.** Best cell (stronger model, image, stack) falls in
  **3–15%**, against 20–28% at n=1 and 0% at n=3. Refuted if n=2 is ≥20% (the rung is too easy to
  bridge the gap) or 0% (the wall is at two faults, not three).
- **H2 — stack beats batch at n=2**, on image, for both models, by **≥5pp** — M5's single-fault
  result scaling to composition. This is the first real test of M4's H2, which floored at 0/0.
- **H3 — `2fault_1door` ≥ `2fault_2door` on PASS.** Assignment burden costs something at constant
  action count. A null result here is informative and should be reported as such.
- **H4 — the type pair matters more than the arm.** Spread in success across T+R / T+S / R+S exceeds
  the `1door` vs `2door` gap. Motivated by the opposite per-type lopsidedness of the two models in M5.
- **H5 — the model-specific text penalty persists.** g3 text stays ≤4%; er text tracks er image
  within 5pp. Refuted if er's text arm collapses too, which would restore M4's original reading that
  composition (not the model) breaks the symbolic channel.
- **H6 — Qwen3-VL-8B lands at or near the floor, but above random.** Predicted **0–7%** on
  `stack`/image (0–2 of 30), i.e. below both API models but distinguishable from the random
  baseline's low single digits. An 8B open-weight instruct model is two tiers below the frontier
  arms, and this rung already floors one of them on text. Two ways this is informative rather than
  merely low:
  - if Qwen is **0/30 in both modalities**, the n=2 rung is above the trainable model entirely and
    Stage-2 needs an easier rung (or dense reward) before RL has any gradient to work with — a
    decision this experiment should make, not defer;
  - if Qwen registers **non-zero `deviation_closed`** even at 0% PASS, there is exploitable partial
    signal and the graded metrics are a usable reward proxy.

  `made_worse_rate` is the number to watch here: Stage-2 cannot bootstrap from a policy whose average
  action degrades the object.

## 9. Validation before running any model

Same gate battery as M4 §8, logged to `runs/_analysis/verify_2fault.{log,json}` via a
`verify_hard.py` run pointed at the new set:

| gate | requirement |
|---|---|
| invertibility | `gt_fix_sequence` restores every faulty part, max deviation ≈ 0.000000 mm |
| necessity | dropping either inverse leaves ≥3τ residual |
| off-grid magnitudes | 30/30 |
| distinct bases | 30/30 (or the recorded 12+12 fallback) |
| `tau_frac == 0.015` | 30/30 |
| type-pair balance | 5 per pair per arm |
| oracle round-trip (gate 6) | 100% through the agent's own action language |
| oracle / random baselines | 100% / low single digits, both contracts |

Do not run a model until oracle is 100% on both contracts.

Additionally, before the Qwen arm (§3.5):

| check | requirement |
|---|---|
| `last_meta` populated by `QwenVLAgent._call` | latency / usage / `gave_up` present in `turns.jsonl` |
| induced-failure test | stop the vLLM server mid-episode; the run must record an API give-up, not a clean `NO_FIX` |
| `max_tokens` raised from 1536 | no truncated turns on a 2-fault instance |
| smoke episode | `run_episode.py --agent loop_qwen_full --modality image --verbose` parses a valid action |
| prompt parity | a `loop_qwen_full` prompt dump is byte-identical to `loop_gemini_full`'s but for the model name |

## 10. Deliberately out of scope

**The text-observation redesign is NOT part of M6.** M4 called for it and M5 sharpened the case, but
changing the observation format and the difficulty rung in the same experiment makes neither
attributable. It is M7 — and M5 arguably narrows its brief from "redesign the symbolic channel" to
"determine why one model is destroyed by a channel the other uses fine."

## 11. Results

300/300 episodes: 240 API (2 models × 2 contracts × 2 modalities × 30) + 60 Qwen (stack × 2
modalities × 30). Raw tables: `runs/_analysis/m6_two_fault.{md,json}`.

**Integrity.** 3 API give-ups (1.25% of API episodes, all g3 — below M4's 1.7%), **0 rate-limit
errors** at 14 concurrent conditions, 0–5 invalid actions per API condition. The Qwen arms are the
exception and are discussed under H6.

### Headline

| | image | text |
|---|---|---|
| **g3 batch** | **3/30 (10%)** | 0/30 |
| g3 stack | 0/30 | 0/30 |
| er batch | 1/30 (3%) | 0/30 |
| er stack | 1/30 (3%) | 0/30 |
| qwen stack | 0/30 | 0/30 |

Aggregates over the 240 API episodes: image **4.2%** vs text **0.0%**; batch **3.3%** vs stack
**0.8%**; 1door **2.5%** vs 2door **1.7%**.

Reference points on the same instances: **oracle 100%** (both contracts), **random 0%**.
Neighbouring rungs: n=1 hardened control 4–28% (M5); n=3 composite 0/200 (M4).

### Verdicts

**H1 — n=2 lands strictly between the rungs. CONFIRMED, but only just, and by a single cell.**
Predicted 3–15% for the best cell; observed **10%** (g3/batch/image), between n=1's 20–28% and n=3's
0%. Neither refutation condition fired. But the rung is far closer to the wall than to the floor:
**5 of the 8 API cells are exactly 0%**, and 7 of 8 are ≤3%. The tolerance sweep does not move it —
10% at 1× is still 10% at 3× — so these are genuine misses, not near-misses, exactly as at n=3.
**The intended "measurable middle" exists but is carried by one condition**, which is a weaker
result than the experiment was designed to produce (see §12).

**H2 — stack beats batch by ≥5pp on image. REFUTED, and REVERSED.** g3: batch 10% vs stack **0%**
(batch +10pp). er: 3% vs 3%, a tie. Aggregate batch 3.3% vs stack 0.8%. M5's single-fault stack
advantage does **not** survive composition — it inverts. The mechanism is visible in
`ever_simulated_a_pass`: g3/batch/image reaches a passing state in 10% of episodes, g3/stack/image in
**0%**. Stack never finds the answer at all, rather than finding it and failing to commit. `RESET()`
was genuinely exercised (26–61 calls per stack condition), so the affordance was used, not ignored.
Reading: with two faults, a wrong first step contaminates the working state, and per-step feedback
buys less than the freedom to re-plan the whole repair from the original object.

**H3 — 1door ≥ 2door. NOT SUPPORTED; underpowered.** 2.5% vs 1.7% — 3 episodes vs 2, out of 120
each. The direction matches the prediction but the difference is one episode, and the best cell runs
the *other* way (g3/batch/image: 2door 13% vs 1door 7%). The level-matched design finally makes this
comparison legitimate — both arms need exactly two correct actions, and PASS is directly comparable —
but any real effect is smaller than 120 episodes per arm can resolve at a ~2% base rate. **No claim.**

**H4 — the type pair matters more than the arm. WEAKLY SUPPORTED.** Pair spread is 0%–3.8% (3.8pp)
against an arm gap of 0.8pp, so the ordering predicted holds. The qualitative pattern is cleaner than
the aggregate: **all 3 of g3's solves are `rotate+scale`** (3/10 = 30% in that one cell), **both of
er's are `scale+translate`**, and **`rotate+translate` is 0/80 across every model, contract and
modality**. With 5 solves total this is suggestive, not established — but it is the most promising
axis in the data, and it says the two models fail on *different* pairs, echoing the opposite per-type
lopsidedness M5 found at n=1.

**H5 — the text penalty is model-specific. BOTH CLAUSES HOLD, THE UNDERLYING CLAIM IS REFUTED.**
Literally: g3 text ≤4% ✓ (0%), and er text within 5pp of er image ✓ (0% vs 3%). But the M5-derived
claim those clauses were meant to test — that text harms g3 specifically while er uses it fine — is
false at n=2. **Text is 0/120 across all models, both contracts.** And er's text arms are now
destructive on the graded metrics, not merely unhelpful:

| er | deviation closed | made worse |
|---|---|---|
| batch image | −15% | 57% |
| batch **text** | **−64%** | **90%** |
| stack image | −21% | 67% |
| stack **text** | **−51%** | **80%** |

M5 showed er unharmed by text on a *single* fault. Composition breaks that immediately. This
**restores M4's original H5 reading** and refutes the refinement M5 suggested: the symbolic channel's
harm is a property of composition, not of one model. My M5-based framing was wrong.

**H6 — Qwen at or near the floor but above random. CONFIRMED at the floor; both decision branches
fire.** 0/60, the bottom of the predicted 0–7%. Pre-registered rule 1 (*0/30 in both modalities → the
rung is above the trainable model entirely*) fires. Rule 2 (*non-zero `deviation_closed` → exploitable
partial signal*) does **not** — both values are negative (−7% image, −14% text). **Stage-2 has no
gradient to climb on this set.**

Two behavioural findings underneath the zero. **Compliance, not repair, is Qwen's binding
constraint**: 36 invalid actions (image) and 109 (text) against 0–5 for every API condition; 17/30
text episodes hit at least one, one burned 15 invalid turns, and **3 text episodes never executed a
single valid SIMULATE**. The dominant failure is a bare action with no mode verb
(`<act>ROTATE(P0, Z, -5)</act>`, 167 of 196 first-parse failures). And **`RESET()` was used zero times
in 60 episodes**, against 26–61 per stack condition for the API models — Qwen does not engage the loop
affordances at all. The parser was deliberately NOT relaxed for this, since that would score Qwen
under a different contract than g3/er and destroy the comparison.

Counterintuitively, Qwen is the **least destructive** model on the set (−7%/−14% deviation closed,
50–53% made worse, against −15% to −70% and 57–90% for the API models). That is almost certainly
because it does less — small edits, prompt-example copying — not because it understands more.

### What this means

**The n=2 rung is not the usable middle the benchmark needs.** It was built to sit between a
saturating rung and a wall; it landed at 2% aggregate, much nearer the wall. Only g3/batch/image
produces a usable signal, and inside it only one fault pair does. As a discriminator it is
thin.

**Two results are solid enough to act on.** Text observation is harmful under composition for *every*
model tested — that is now three independent confirmations (M4 n=3, M6 n=2 both models) against one
non-replication (M5 n=1, er). And the batch/stack ordering **inverts** between n=1 and n=2, which
means the contract question cannot be settled once and reused; it is difficulty-dependent.

**For Stage-2**, the trainable model is not merely below the rung, it is below the protocol. Format
compliance has to be fixed (trace-SFT) before repair skill is even measurable, and the reward signal
on this set is negative everywhere.

## 12. Follow-ups this data argues for

1. **An easier intermediate rung is still missing.** n=2 at τ=1.5% with off-grid magnitudes is nearly
   as hard as n=3. The knobs to relax are *not* the fault count — try n=2 at τ=2.5% (the M4-era
   tolerance), or n=2 drawn from a narrower magnitude range. The tolerance sweep says τ alone will not
   do it for the *existing* instances (0%→0% at 3×), so the magnitudes are the likelier lever.
2. **`rotate+translate` is 0/80 and `rotate+scale` carries every g3 solve.** A pair-focused study at
   higher n per cell would be cheap and is the most promising signal here.
3. **The text-channel redesign (M7) is now better motivated than when M4 proposed it**, and its brief
   is broader than M5 suggested: it is not one model failing, it is the representation failing under
   composition.
4. **Qwen needs trace-SFT before any RL**, and any such stage should be evaluated on protocol
   compliance (invalid-action rate, RESET usage) as a first-class metric, not just PASS.
