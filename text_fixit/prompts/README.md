> **2026-08-16 — prompt sets reorganised.** The active set is **`one_error_search`** (11/30 on
> std30, up from 1/30). It is self-contained: all four roles are present, so it also serves as
> `BASE_PROMPT_SET`. The superseded sets — `one_error`, `one_error_dev`, `one_error_scale`,
> `one_error_strict` — moved to `old_prompts/old_one_error_prompts/`. See
> `docs/PROMPT_ITERATION_LOG.md` for how the search set was derived and why the earlier ones failed.

# Prompts

The standardized set is **`one_error`** — one fault, one action per turn, two closed views.
Everything from the previous generation is in [`old_prompts/`](old_prompts/) for reference.

## Files

| file | role |
|---|---|
| `one_error_image.txt` | system prompt, image modality |
| `one_error_text.txt` | system prompt, text modality |
| `one_error_step.txt` | the per-turn user message (window3 / oneshot; `full` history builds its own) |

A **prompt set** is a family of files sharing a prefix. `FIXIT_PROMPT_SET=<name>` selects one;
`one_error` is the default. Any file a set does not define falls back to `one_error`, so an ablation
ships only the file it actually changes. The set name is recorded in every run manifest as
`prompt_set`, so a run's prompt is identified by one name rather than reconstructed from flags.

These sets are **self-contained** — no `$contract_block`, because there is only one contract now
(a single action, applied fresh to the original broken object).

---

## What the model is told

Worth being explicit, because several of these are choices that could reasonably go the other way.

**It knows which parts exist and which are fixable.** `$part_table` lists every part with an id
(`P0`, `P1`, …), a human label (`door_1_right`), its role, a `fixable` yes/no column, its **bounding
box** `(w,d,h)` in metres, and for fixable parts the hinge axis and location. Hiding the
`role`/`fixable` columns is a runtime switch (`--hard` without `--reveal-fixable`); when hidden,
`$fixable_note` renders empty so the prompt does not leak the candidate set through the back door.

**It knows part sizes, not part positions.** The bounding box is in the table. The part's *current*
centre is not — that arrives in the observation.

**It knows the tolerance** (`$tol_pct`, 1.5% at `FIXIT_TAU_FRAC=0.015`) and the three success gates:
within tolerance, door still closes, no interpenetration.

**It knows the action bounds** — the continuous ranges for translate/rotate/scale.

**It is NOT told:**
- the numeric deviation, unless `--deviation on`
- which part is faulty, or the fault type
- how large faults typically are (the old prompt's "3x this tolerance" line is gone)
- the healthy target geometry — it must search for it

**Image modality** additionally gets, per turn, two rendered views with all doors closed: the
original broken object (identical every turn) and the result of the action chosen on the **previous**
turn. Turn 1 also carries an annotated view with each fixable door recoloured and labelled `P#`.

**Text modality** gets the same comparison as numbers: the original broken per-part centre and size,
then the result of the previous action as world centres with the doors driven open and shut.

---

## Available variables

`string.Template.safe_substitute` — **an unknown `$name` is left in the output verbatim rather than
raising.** A typo ships silently into the model's context. Grep a rendered prompt for `$` before
trusting a new template; that check caught `$fixable_note` reaching a model during this rewrite.

### System files (`*_image.txt`, `*_text.txt`)

| variable | value |
|---|---|
| `$category` | `Refrigerator` |
| `$instance_id` | e.g. `10036_ctrl_translate_0` |
| `$function_text` | what the object is supposed to do |
| `$success_text` | what counts as repaired |
| `$part_table` | the rendered part table (see above) |
| `$tol_pct` | tolerance as a percentage, from `FIXIT_TAU_FRAC` |
| `$fixable_note` | "Only parts marked fixable=yes may be targeted." — **empty** when the column is hidden |
| `$value_grid` `$angle_grid` `$scale_grid` | continuous action bounds |
| `$K` | SIMULATE budget (0 for oneshot) |

Also available, unused by `one_error` and listed so an ablation can reach for them:
`$fault_hint` (single vs multi-fault wording), `$margin_x` (the set's real generation margin),
`$thinking_note` (reasoning budget), `$translate_range` `$rotate_range` `$scale_range` (fault
magnitude ranges, read from the instance), `$contract_block` (batch/stack contract text),
`$success_text`.

### Step file (`*_step.txt`)

`$observation`, `$budget_left`, `$commit_note`, `$history` (last three SIMULATEs).

---

## Output contract

`action_parser.py` rejects anything else, and a rejected turn costs a turn:

```
<think>reasoning</think>
<act>SIMULATE TRANSLATE(P1, Y, -0.04)</act>
```

- mode is `SIMULATE` or `COMMIT`; `<backtrack/>` may precede `<act>`
- calls: `TRANSLATE|ROTATE|SCALE(P#, X|Y|Z, value)`, `NO_FIX()`
- **exactly one action per turn** under `one_error`
- magnitudes are clamped to the action bounds, not snapped to a grid

---

## Ablations

**Every ablation is a new prompt set — never an edit to `one_error`.** Add
`<name>_image.txt` / `<name>_text.txt` for whichever you change, run with
`FIXIT_PROMPT_SET=<name>`, and add a row below stating the difference from `one_error`.

| set | differs from `one_error` by | measured effect |
|---|---|---|
| `one_error` | — (baseline) | Qwen3-VL-8B **0/60** on `instances_std30` |
| `one_error_scale` | a FAULT SCALE block stating the typical magnitude of each fault type, read from the instance's `magnitude_ranges`, plus that the repair is the same size in the opposite direction (reciprocal for scale). Deviation stays OFF. Nothing else differs. | running |
| `one_error_dev` | three lines in WHAT YOU SEE telling the model the observation reports the remaining error in mm and the tolerance. Run with `--deviation on`, which adds `worst part off by N mm (tolerance M mm)` to the observation. Nothing else differs — verified by diff. | running |

### Known candidates, with prior evidence

**Remove the concrete exemplar.** `one_error` keeps `<act>SIMULATE TRANSLATE(P1, Y, -0.04)</act>` in
the PROCEDURE block. Under the previous generation Qwen3-VL-8B opened **90% of episodes with exactly
that action**, and 67% of all its actions used the exemplar's axis. Replacing the values with
metasyntax cut verbatim copying from 62% to 13% — but did **not** change the success rate. Worth
re-running as `one_error_metasyntax` because it removes a confound from any claim about what the
model *chose*, not because it is expected to help.

**State the fault scale.** `one_error` deliberately omits it. Adding `$translate_range` etc. tests
whether magnitude estimation is the constraint. Prior evidence says it is not: once a model reaches
the right part+type+axis, its best magnitude is already ~1.0× ground truth.

**Show the deviation.** Not a prompt change — the `--deviation on` flag. On the hardened rung this
took the API models from 20% to 65–76% while leaving Qwen unmoved, which is the sharpest
capability split measured so far.

---

## Two hazards from the previous generation

**Never hardcode a value the instance owns.** `margin_x` and the magnitude ranges used to be
literals (`3x this tolerance`, `0.08-0.20 m`). On a set generated at margin 1.2 with 0.35×
magnitudes the prompt stated numbers several times off — worse than saying nothing. `one_error`
avoids this by not mentioning fault scale at all.

**Concrete exemplars get copied verbatim.** See the ablation table above.
