# Milestone 1 — Closed-Loop VLM Fridge Repair

**Goal (one sentence):** stand up a closed perception→action→simulation→perception loop where an
*off-the-shelf* VLM repairs a broken refrigerator from rendered images, and measure — on held-out
shapes — whether the loop (and visual feedback) actually helps versus one-shot and random baselines.

This is the **Stage-1 baseline** of the FixIt-RL project (no training yet). It establishes the
environment, the renderer, the scorer, and the evaluation harness that Stage-2 (SFT) and Stage-3 (RL)
will reuse.

Everything below is grounded in what is already verified on disk:
- 43 PartNet-Mobility refrigerators in `text_fixit/assets/partnet_mobility/<id>/` (URDF + textured meshes),
  split **30 train / 13 test** by shape, 0 overlap (`text_fixit/data/fridge_ids.json`).
- PyBullet load + articulated-joint sweep + contact/penetration queries work headless (`smoke_pybullet.py`).
- Healthy-fleet score calibration done (`calibrate_score.py`): clean doors penetrate 0–2 mm through a 90°
  swing; broken/noisy geometry penetrates tens–hundreds of mm. **11/13 test shapes have ≥1 clean door
  (17 clean test doors total).**

---

## 1. The loop (what M1 delivers)

```
                ┌─────────────────────────────────────────────────────────┐
                │  reset(): pick broken fridge instance                    │
                │  render: annotated view + 2 hero views + activation strip│
                └───────────────┬─────────────────────────────────────────┘
                                │  images + goal + part list  (+ history)
                                ▼
        ┌──────────────►  VLM agent (off-the-shelf)  ◄────────────┐
        │                       │ emits JSON action               │
        │                       ▼                                 │
        │        {action: simulate_fix|commit_fix,                │
        │         part, transformation}                           │
        │                       │                                 │
        │     simulate_fix       │        commit_fix               │
        │                       ▼                                 │
        │   apply fix to BROKEN object → run activation           │
        │   (sweep door 0→90°) → functional score → render result │
        │                       │                                 │
        └───── images of result ┘   (loop, budget B=6)            │
                                │                                 │
                     commit / budget-exhausted ────────────────────┘
                                │
                                ▼
                  terminal functional score → episode metrics
```

- **Single-fix, non-compounding.** Each `simulate_fix` is applied to the *original broken object*, not
  stacked on the previous attempt. This is exactly the "backtrack to a different part/transformation"
  semantics: try fix A, look, discard, try fix B. (Multi-fix is a stretch goal.)
- **Confidence = the VLM's own visual judgment.** The agent decides when the door looks fixed and emits
  `commit_fix`. The ground-truth functional score is computed internally for grading but (in the headline
  condition) **not shown to the agent** — the agent must read success off the rendered activation.

---

## 2. Scope decisions for M1

| Axis | M1 choice | Rationale |
|---|---|---|
| Category | **Refrigerator only** | Meshes in hand, part semantics clean (`link_*=door`), score validated. |
| Object pool | **Curated clean-door shapes** (11/13 test, ~24/30 train) | Guarantees an unambiguous functional signal (see §5). |
| Instances | **Freshly generated corruptions** (we control break → exact inverse GT) | Full control of difficulty; avoids reconstructing FixIt's exact instances. FixIt `choices/` kept as optional cross-reference. |
| Corruption types | **translate, rotate, scale** on one door | Matches FixIt's DSL; all three produce measurable openability loss. |
| Fix count | **Single fix per episode** | Matches "which one transformation restores function". |
| Feedback to agent | **Images only** (headline); `images+scalar` as ablation | Keeps it a genuine vision task; scalar version bridges to the text proposal. |
| Model training | **None** (off-the-shelf only) | This is Stage 1. |

---

## 3. System components & file layout

```
text_fixit/
  assets/partnet_mobility/<id>/     # meshes                              [DONE]
  data/fridge_ids.json              # 30/13 split                         [DONE]
  download_partnet_mobility.py      # SAPIEN fetch                        [DONE]
  smoke_pybullet.py                 # plumbing check                      [DONE]
  calibrate_score.py                # healthy-fleet calibration           [DONE]
  corruption.py    # sample_corruption(base)->(corruption, gt_fix); apply_transform(urdf,...)   [TODO]
  score.py         # functional_score(urdf, door) -> {open_angle, penetration, score}           [TODO]
  render.py        # EGL renderer: hero views, activation filmstrip, annotated part view         [TODO]
  env.py           # FridgeRepairEnv: reset()/step(action) Gym-style                              [TODO]
  instances.py     # build+validate episode instances -> instances/{train,test}.jsonl            [TODO]
  agents/
    base.py        # Agent.act(observation)->action                                               [TODO]
    vlm_api.py     # hosted frontier VLM                                                          [TODO]
    vlm_qwen.py    # local Qwen2.5-VL-7B via vLLM                                                 [TODO]
    random_agent.py, oneshot_agent.py, oracle_agent.py                                            [TODO]
  prompts/system.txt, prompts/step.txt                                                            [TODO]
  run_episode.py   # drive one agent×instance, log trajectory + images                            [TODO]
  evaluate.py      # batch over test instances, compute metrics, write report                     [TODO]
  runs/<run_id>/<episode_id>/...    # rendered PNGs + trajectory.json
  reports/<run_id>.md               # metrics tables
```

---

## 4. Instance generation (`corruption.py`, `instances.py`)

**Corruption sampling** (per curated (base_shape, door_joint)):
- `type ∈ {translate, rotate, scale}` (uniform).
- `translate`: displacement `d ∈ [0.10, 0.30] m` along a door-plane axis (±x or ±z). Fix = `-d`.
- `rotate`: hinge/door offset `θ ∈ [30°, 90°]` about the door's local axis. Fix = `-θ`.
- `scale`: factor `f ∈ [1.3, 1.8]` (enlarge → collides) along the door's width or height axis about the
  hinge-side pivot. Fix = `1/f`.
- Transforms are applied to the door link's mesh + URDF origin via a refactor of `generate_data/fridge/`
  (`modify_obj`, `modify_urdf`, `modify_obj2`). Each instance is written to a temp URDF dir.

**Validation gate (every instance must pass):**
1. `healthy_score(base_door) == 1.0` (door opens full 90° clean — this is the curation filter).
2. `broken_score ≤ 0.30` (corruption genuinely breaks openability).
3. Applying the exact inverse (`gt_fix`) restores `score ≥ 0.90` (sanity: the break is reversible).

Instances failing any gate are resampled. Result cached as JSONL:
```json
{"id":"10489_j1_scale_0007","base":"10489","split":"test","door_joint":1,
 "part_name":"left_door","corruption":{"type":"scale","axis":[1,0,0],"factor":1.62,"pivot":0.83},
 "gt_fix":{"type":"scale","axis":[1,0,0],"factor":0.617},"broken_score":0.11,"healthy_score":1.0}
```

**Target counts:** generate until **≥120 validated test instances** (11 shapes × 17 doors × 3 types ×
~3 magnitudes, curated) and a matching train pool for prompt development. Report the actual N.

---

## 5. Functional score (`score.py`) — fully specified

The **only** reward signal. Physics, not heuristics: it scores *any* proposed fix, not just the GT.

```
functional_score(urdf, target_door):
    load urdf headless, fixed base,
         flags = URDF_USE_SELF_COLLISION | URDF_USE_SELF_COLLISION_EXCLUDE_PARENT
    sweep target_door from 0 → 90° in 45 steps (all other doors held closed)
    at each step: performCollisionDetection(); pen = min contact[8] over self-contacts
    open_angle = largest angle reached with pen ≥ -ε_tol          # ε_tol = 5 mm (calibrated)
    return open_angle / 90°     ∈ [0,1]
```
Calibration basis (measured today): clean healthy doors → 0–2 mm penetration, `score = 1.0`; broken doors
→ deep penetration, jam early, `score → 0`. `ε_tol = 5 mm` sits well inside the gap.

- **Relative reporting:** because instances are curated so `healthy_score = 1.0`, the raw score already
  equals the fraction-of-healthy-openability recovered. (No per-shape normalization needed once curated.)
- **Episode outcomes:** `success ⇔ terminal score ≥ 0.80` (door opens ≥ 72°). Also report the continuous
  score.
- **Collision-mesh caveat + mitigation:** we only have *visual* (concave) meshes, so raw self-collision is
  noisy on ~15% of shapes → **curation (§4 gate 1) removes them for M1.** Optional robustness upgrade
  (post-M1): generate convex `mobility_vhacd.urdf` via `p.vhacd()` to reclaim the full 43-shape pool.

---

## 6. Rendering / screenshots (`render.py`) — fully specified

- **Renderer:** PyBullet `getCameraImage`, GPU-accelerated headless via the **EGL plugin**
  (`p.loadPlugin('eglRendererPlugin')`); automatic fallback to `ER_TINY_RENDERER` (CPU) so it runs on any
  box. Deterministic camera (no physics randomness in rendering).
- **Resolution:** 640 × 640 RGB. Neutral gray background, single directional light + ambient.
- **Camera framing:** target = object AABB center; distance = `2.4 × bbox_diag`.
- **Views per observation:**
  1. **Hero A** — yaw 45°, pitch −30° (front-right, elevated).
  2. **Hero B** — yaw 135°, pitch −20° (other side; resolves depth ambiguity).
  3. **Activation filmstrip** — target door rendered at **[0°, 30°, 60°, 90°]** from Hero A, tiled
     horizontally into one image. *This is the key frame:* a broken door visibly stops / interpenetrates;
     a fixed door swings clear. Static images cannot show a dynamic jam — the strip can.
- **Annotated part view (rendered once at reset):** each fixable door recolored from a fixed palette with a
  text label (`left_door`, `right_door`, …) placed at its projected centroid (via the segmentation buffer
  from `getCameraImage`). This *grounds the agent's part vocabulary* so `"part": "left_door"` is unambiguous.
- **What the agent receives each step:** `[Hero A, Hero B, activation strip]` (+ annotated view at reset).
  In the `images+scalar` ablation, also a one-line JSON `{"door_opened_deg": .., "functional_score": ..}`.
- **Files:** `runs/<run_id>/<ep_id>/reset/{annotated,heroA,heroB,activation}.png`,
  `.../step<k>/{heroA,heroB,activation}.png`, plus `trajectory.json` (actions, scores, timings).

---

## 7. Action space & agent I/O (`agents/`, `prompts/`)

**Action schema (strict JSON):**
```json
{"reasoning": "free text, short",
 "action": "simulate_fix" | "commit_fix",
 "part": "left_door",
 "transformation": {
    "type": "rotate" | "translate" | "scale",
    "axis": [1,0,0],
    "angle_deg": -35,          // rotate
    "delta_m": [0,0,-0.12],    // translate
    "factor": 0.62             // scale
 }}
```
- `part` must be in the episode's part vocabulary (from the annotated view) → else **invalid action**.
- Exactly one of `angle_deg` / `delta_m` / `factor` per `type`; magnitudes clamped to valid ranges.
- **Parsing:** extract first JSON object; on malformed → **1 reparse retry** with the error echoed; if it
  still fails → counts as an invalid action (logged, step consumed).

**Prompt (`prompts/system.txt`):** task description; the fridge goal ("the door must open freely to at
least 90° without the door colliding with the body or the other door"); the transformation grammar; the
part vocabulary; the stopping rule ("emit `commit_fix` when the rendered result shows the door opening
cleanly; otherwise `simulate_fix` again"); output-format contract. **Step prompt** appends the current
images + a compact textual history of the last **3** attempts (`part`, `transformation`, and — only in the
scalar ablation — their score) so context stays bounded.

**Models:**
- **Frontier ceiling:** one strong hosted VLM (see Open Decision D) — answers "is this already solved
  zero-shot?"
- **Trainable baseline:** **Qwen2.5-VL-7B-Instruct** local via vLLM on the RTX 6000 Ada — the model the
  Stage-2/3 training will actually use.

---

## 8. Episode protocol (`env.py`, `run_episode.py`)

```
reset(instance):
    load broken URDF; render reset observation; broken_score computed (hidden)
    return observation
step(action), budget B = 6 simulate_fix calls:
    simulate_fix → apply fix to a COPY of the broken object → activation sweep → score (hidden)
                 → render result → append to history → return observation
    commit_fix   → apply fix → score → TERMINAL (return terminal score)
    invalid      → log; after 1 retry, consume the step
    if budget exhausted with no commit → auto-commit the BEST-scoring simulated fix → TERMINAL
```
Timing budget target: ≤ ~5 s wall per `simulate_fix` (activation sweep + 6 renders), headless DIRECT+EGL.

---

## 9. Baselines & ablations

| Name | Description | Isolates |
|---|---|---|
| `random` | sample legal (part, transform) each step, commit at budget | task floor |
| `oneshot_vlm` | VLM proposes once from broken images, commits immediately (no feedback) | value of the **loop** |
| `loop_vlm` (headline) | full closed loop, images-only feedback | the milestone |
| `loop_vlm+scalar` | loop with the numeric score shown | value of **visual** vs numeric feedback |
| `loop_vlm_blind` | numbers only, no images (text-FixIt) | value of **vision** |
| `oracle` | apply the exact inverse `gt_fix` | ceiling (validates the scorer) |

Run every baseline on the **same** held-out test instances.

---

## 10. Metrics (`evaluate.py`) — exact definitions

Per model/baseline, over N held-out test episodes (mean ± bootstrap 95% CI):

1. **Success rate** = `#(terminal_score ≥ 0.80) / N`.
2. **Mean terminal functional score** ∈ [0,1].
3. **Efficiency** = mean `#simulate_fix` calls among **solved** episodes (lower = better search).
4. **Recovery rate** = among episodes whose *first* `simulate_fix` scored < 0.80, fraction that still
   reached terminal ≥ 0.80. *(This is the central hypothesis metric — does feedback + backtracking help.)*
5. **Repeated-action rate** = fraction of `simulate_fix` calls duplicating a prior (part, quantized-transform).
6. **Invalid-action rate** = invalid outputs / total actions.
7. **Commit precision** = among `commit_fix` decisions, fraction with score ≥ 0.80 *(is "confidence"
   calibrated?)*; report over-budget (never-committed) rate alongside.
8. **Generalization:** all metrics reported on the **13-shape test split only**; any prompt/threshold
   tuning happens on **train shapes**.

---

## 11. Evaluation process (end to end)

1. `python instances.py --split test` → validated `instances/test.jsonl` (report N ≥ 120).
2. For each baseline in §9: `python evaluate.py --agent <name> --split test --run <run_id>`
   → runs every episode, saves images + `trajectory.json`, streams results.
3. `evaluate.py` aggregates → `reports/<run_id>.md`: one metrics table (rows = baselines, cols = §10
   metrics) + example trajectories (image strips) for one solved and one failed episode per model.
4. **Headline read:** does `loop_vlm` beat `oneshot_vlm` on success rate and (especially) **recovery
   rate**, and does either clear `random` by a wide margin while staying below `oracle`? That answers
   "is the task non-trivial and does the loop help" — the Stage-1 question.

---

## 12. Acceptance checklist (Definition of Done)

- [ ] `corruption.py`: sample + apply + exact-inverse GT, reusing `generate_data/fridge` math.
- [ ] `score.py`: penetration-based functional score; `oracle` reaches ≥ 0.90 mean, `random` low — proving
      the scorer separates good from bad fixes.
- [ ] `render.py`: EGL headless renderer producing hero views + activation filmstrip + annotated part view;
      visually confirm a broken door *looks* jammed and a fixed door *looks* open.
- [ ] `env.py` + `run_episode.py`: full reset/step loop with a `random` agent end-to-end.
- [ ] `instances.py`: ≥ 120 validated held-out test instances cached.
- [ ] `agents/vlm_api.py` + `vlm_qwen.py`: both drive the loop and emit parseable actions.
- [ ] `evaluate.py`: produces `reports/<run_id>.md` with the §10 metrics for all §9 baselines.
- [ ] **Milestone result:** a metrics table on the 13 test shapes showing where off-the-shelf VLMs land,
      whether the closed loop beats one-shot, and clear headroom below oracle → motivates Stage-2 SFT.

---

## 13. Open decisions (need your confirmation)

- **A. Instance source** — freshly-generated corruptions (recommended, full control) vs reconstruct FixIt's
  exact `choices` instances. *Default: fresh.*
- **B. Feedback condition as headline** — images-only (recommended; true vision task) vs images+scalar.
  *Default: images-only headline, scalar as ablation.*
- **C. Continuous vs discretized action magnitudes** — continuous (recommended, matches proposal) vs a
  discrete {small/med/large × direction} set to help weak zero-shot models. *Default: continuous, with a
  discrete fallback mode available.*
- **D. Frontier VLM for the ceiling** — which hosted model (Claude / GPT-4o / Gemini) alongside local
  Qwen2.5-VL-7B. *Needs your API access preference.*
- **E. VHACD collision meshes** — curate-only for M1 (recommended, simplest) vs also generate convex
  meshes now to use all 43 shapes. *Default: curate for M1, VHACD post-M1.*

## 14. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Concave visual meshes → noisy collisions | Curation gate (§4/§5); VHACD as post-M1 upgrade. |
| Zero-shot VLM can't estimate continuous 3D magnitudes from images | Discrete action fallback (Decision C); the *loop* exists precisely to correct bad magnitudes. |
| Activation jam not visible in a static frame | Activation **filmstrip** (§6) shows the dynamic stop. |
| Per-`simulate_fix` render cost too slow for many episodes | EGL GPU rendering; DIRECT mode; cache renders by (instance, quantized-fix). |
| VLM part-reference ambiguity | Annotated, color-coded, labeled part view at reset. |
```
