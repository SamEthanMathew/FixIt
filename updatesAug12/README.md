# Updates — 2026-08-12/13

Everything needed for the Notion page: run configuration, the exact rendered prompts, what the model
actually received, one PASS and one FAIL episode with every image, and the aggregate numbers.

**Assets:** `report_assets/` (see the tree at the bottom).
**Commit with the image-transport fix:** see `git log` for `Fix image transport on the stateless
(window3/oneshot) agent path`.

---

## 0. READ FIRST — the image-transport bug, and what it invalidates

**The bug (now fixed).** `GeminiAgent.act()` has two paths. The `history="full"` path built a message
carrying `obs["images"]` and serialised them into the request. The **stateless path — used by
`window3` and by every `oneshot` agent — passed only the step text.** `obs["images"]` was never
referenced. So in image modality the model was told

> "(attached: the ORIGINAL BROKEN object CLOSED, then YOUR FIX applied to it CLOSED — compare before
> vs after…)"

and received **no pixels at all**. The logger still wrote the PNGs to disk, because it logs what the
*environment rendered*, not what the *model received*. Those two had silently diverged.

**Confirmed two ways.** In code: the stateless branch never touches `obs["images"]`. In data: median
prompt tokens for window3+image were **1350**, *below* window3+text at **1479**; two attached images
are worth ~1100 tokens. After the fix the same configuration measures **2465**.

**Full inventory: [`INVALIDATED_DATA.md`](INVALIDATED_DATA.md)** — 17 runs / 523 episodes,
auto-generated from manifests and turn logs, with per-group guidance on what each affected
run was used to claim.

**Runs affected — every image-modality run on `window3` or `oneshot`:**

| run group | agent | status |
|---|---|---|
| M9 Qwen arms (`m9_qw8_*`, `m9_qw32_*`) | `loop_qwen` (window3) | **image-blind — do not cite as image results** |
| M10 Qwen ladder (`m10_*`) | `loop_qwen` | **image-blind** |
| M11 `dev_qw8`, `dev_qw32` | `loop_qwen` | **image-blind** |
| M11 `oneshot_g3`, `oneshot_er`, `oneshot_qw8`, `oneshot_qw32` | `oneshot_*` | **image-blind (API models too)** |
| Baselines, M4, M5, M6, M7, M8 | `*_full` | unaffected — images were attached |
| M11 `dev_er`, `dev_g3` | `loop_gemini_full` | unaffected |

**What it did NOT change.** The corrected re-run of the easy rung scores **4/30 = 13%** against the
image-blind **5/30 = 17%** and the `full`-history (images attached) **5/30 = 17%**. Within noise at
n=30 — so on this rung Qwen-8B was performing the same with and without pixels, and the ladder's
*shape* stands. The affected numbers should nevertheless be labelled, because they were collected
under a configuration that did not do what its name says.

**Provenance going forward.** Every turn now logs `n_images_rendered` (environment) and
`images_sent_to_model` (request). In the exported episodes below they are `2/2` on every turn.

---

## 1. Latest run configuration

Run `m12_qw8_easy_image_imgfix` — the first image run with pixels genuinely attached.

| field | value |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` (vLLM, FP16, `--max-model-len 32768`) |
| agent | `loop_qwen` (**history = window3**, stateless single-message call) |
| git commit | `942bb9c` + the image-transport fix |
| dataset | `text_fixit/data/instances_easy.jsonl`, sha256 `12383cc5…`, n=30 |
| modality | **image** |
| contract | **batch** (a turn carries an ordered list; applied fresh to the original broken object) |
| budget | 10 SIMULATE calls |
| tolerance | τ_frac 0.025 → 43–49 mm on these doors |
| deviation shown | **off** (the model is never told the numeric error) |
| prompt variant | base (no ablation) |
| hard switches | `reveal_fixable=True`, `hard_render=False`, `multi_fault_hint=False` |
| temperature / max tokens | 0.7 / 4096 |
| result | **4/30 = 13%** |

## 2. Exact prompts

Not templates — the **rendered text actually sent**, per turn, in
`report_assets/qwen8_image_*/prompts/<episode>_tNN.txt`. Each file has a `===== SYSTEM =====`
section and a `===== USER =====` section.

- **Turn 1** — `..._t01.txt` (initial observation)
- **Turn 2** — `..._t02.txt` (first feedback)
- **Final turn** — `..._t07.txt` (success) / `..._t11.txt` (failure)

**Dynamically filled values:** `$category`, `$instance_id`, `$part_table` (per-shape part IDs, bbox
sizes, hinge axes), `$fault_hint`, `$tol_pct` (from `FIXIT_TAU_FRAC`), `${margin_x}` (the set's real
generation margin), `$contract_block` (batch vs stack), `$value_grid`/`$angle_grid`/`$scale_grid`
(action bounds), `$K` (budget), `$observation`, `$budget_left`, `$history` (last 3 SIMULATEs),
`$commit_note`.

**Required output format** — enforced by `action_parser.py`:

```
<think>reasoning</think>
<act>SIMULATE TRANSLATE(P1, Y, -0.04)</act>          # or COMMIT
```

`<backtrack/>` may precede `<act>`. A turn carries one action, or an ordered list of up to 6 in
square brackets separated by semicolons. `NO_FIX()` asserts the object is already functional.

## 3. What the image model sees

**Initial turn (2 images):**
1. `t01_0.png` — annotated part-ID view (P0/P1/P2 labels drawn at each part's projected centroid)
2. `t01_1.png` — the original broken refrigerator, all doors closed

**Every simulation turn (2 images):**
1. `tNN_0.png` — the **same original broken** object, closed (fixed reference, identical every turn)
2. `tNN_1.png` — the **candidate** after this turn's action, closed

Plus text stating the action tested, budget remaining, the last three attempts with their outcomes,
and which criteria failed. Under `deviation=off` the failure line names the physical symptom but
never the millimetre error.

## 4. Successful episode — `12042_ctrl_rotate_0`

`report_assets/qwen8_image_success/` · **PASS** · τ = 48.5 mm · broken deviation 59.8 mm (D=1.23)
· ground truth `ROTATE(P1, Z, -18.69)`

| turn | action | deviation | images r/s |
|---|---|---|---|
| 1 | `TRANSLATE(P1, Y, -0.040)` | 83.4 mm | 2/2 |
| 2 | `TRANSLATE(P1, Y, -0.080)` | 114.8 mm | 2/2 |
| 3 | `TRANSLATE(P1, Y, -0.120)` | 148.6 mm | 2/2 |
| 4 | `TRANSLATE(P1, Y, -0.160)` | 183.7 mm | 2/2 |
| 5 | `TRANSLATE(P1, Y, -0.200)` | 220.0 mm | 2/2 |
| 6 | `ROTATE(P1, Z, -10.0)` | **27.9 mm** | 2/2 |
| 7 | **COMMIT** `ROTATE(P1, Z, -10.0)` | 27.9 mm → **PASS** | 2/2 |

**The story:** five turns escalating the *wrong action type* monotonically — each one making the
object worse (83 → 220 mm) while the feedback said so — then it switched to `ROTATE` and solved it
in a single step. Half the budget was spent before it questioned the *type* of fix. Note it started
from the prompt's own exemplar, `TRANSLATE(P1, Y, -0.04)`.

## 5. Failed episode — `10797_ctrl_scale_0`

`report_assets/qwen8_image_failure/` · **FAIL** · τ = 43.5 mm · broken deviation 54.5 mm (D=1.25)
· ground truth `SCALE(P1, X, 0.838)`

| turn | action | deviation | note |
|---|---|---|---|
| 1 | `TRANSLATE(P1, Y, -0.040)` | 71.1 mm | prompt exemplar again |
| 2 | `TRANSLATE(P1, Y, -0.060)` | 85.6 mm | worse |
| 3 | `ROTATE(P1, Z, -15.0)` | 114.2 mm | worse |
| 4 | `[TRANSLATE(P1,Y,-0.08); ROTATE(P1,Z,…)]` | 230.6 mm | much worse |
| 5 | `[TRANSLATE(P1,Y,-0.04); SCALE(P1,**Y**,…)]` | 78.0 mm | right part, right **type**, **wrong axis** |
| 6–7 | more `SCALE(P1, **Y**, …)` combinations | 89.9 / 83.3 mm | still the wrong axis |
| 8 | `TRANSLATE(P1, Y, -0.020)` | 59.6 mm | closest it gets — still > τ |
| 9–10 | repeats of earlier attempts | 78.0 / 85.6 mm | no new hypothesis |
| 11 | **COMMIT** `TRANSLATE(P1, Y, -0.060)` | 85.6 mm → **FAIL** | |

**The story:** the correct fix is a scale on **X**. The model found the right part and eventually the
right transformation type, but **never once tried axis X** — it scaled on Y in every attempt. It
committed a state 85.6 mm off, *worse than the 54.5 mm object it started from*. This is the
diagnosis failure the aggregate funnel identifies, in a single episode.

## 6. Aggregate results

`report_assets/aggregate/` holds `manifest.json`, `records.jsonl`, `turns.jsonl` for the run above,
plus derived `m8_easy_ablation`, `m9_scale_ladder`, `m10_qwen_ladder` in `.md` and `.json`.

**Qwen-8B, easy rung, image modality:**

| run | images actually sent? | score |
|---|---|---|
| `m12_qw8_easy_image_imgfix` | **yes** | **4/30 = 13%** |
| `m9_qw8_easy_image` | no (bug) | 5/30 = 17% ⚠ |
| `m8_qw_base_image` (full history) | yes | 5/30 = 17% |

Random on this set is 3%; oracle is 100%.

⚠ **Any `m9_*`, `m10_*`, `m11_dev_qw*` or `m11_oneshot_*` figure labelled "image" was produced before
the fix and should carry a warning on the page.**

## 7. Asset tree

```
report_assets/
  qwen8_image_success/          12042_ctrl_rotate_0  (PASS, 7 turns)
    manifest.json  record.json  turns.jsonl  trajectory.md  raw.jsonl
    prompts/  12042_ctrl_rotate_0_t01.txt … _t07.txt
    images/12042_ctrl_rotate_0/  t01_0.png t01_1.png … t07_0.png t07_1.png   (14 images)
  qwen8_image_failure/          10797_ctrl_scale_0   (FAIL, 11 turns)
    …same structure…                                                        (22 images)
  aggregate/
    manifest.json  records.jsonl  turns.jsonl
    m8_easy_ablation.{md,json}  m9_scale_ladder.{md,json}  m10_qwen_ladder.{md,json}
```

Every turn's images are present, not just the final frame: `tNN_0` is the fixed original-broken
reference and `tNN_1` is that turn's candidate.
