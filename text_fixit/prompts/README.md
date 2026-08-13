# Prompts

The previous generation lives in [`old_prompts/`](old_prompts/) for reference. This directory is
where the standardized replacements go. **Until the five required files exist here, every LLM agent
raises on construction** — `agents/gemini.py` loads them by exact filename.

## Required files

| file | loaded when | must contain |
|---|---|---|
| `system.txt` | modality = **text** | `$contract_block` |
| `system_image.txt` | modality = **image** | `$contract_block` |
| `contract_batch.txt` | `--contract batch` | the action space + procedure |
| `contract_stack.txt` | `--contract stack` | same, plus `RESET()` |
| `step.txt` | every turn (window3 / oneshot only) | `$observation` |

A system file is rendered first, and `$contract_block` is replaced by the *already-rendered* contract
file — so the contract's own variables are substituted before it is injected.

## Substitution

`string.Template.safe_substitute`, so **an unknown `$name` is left in the output verbatim rather than
raising**. A typo'd variable ships silently into the model's context. Grep a rendered prompt for `$`
before trusting a new template.

### System files (`system.txt`, `system_image.txt`)

| variable | value |
|---|---|
| `$category` | `Refrigerator` |
| `$instance_id` | e.g. `10036_ctrl_translate_0` |
| `$function_text` / `$success_text` | per-category task and success description |
| `$part_table` | the rendered part table (ids, labels, bboxes, hinges; `role`/`fixable` columns only when `reveal_fixable`) |
| `$fault_hint` | `Exactly one part may be faulty.` or the multi-fault wording |
| `$tol_pct` | tolerance as a percentage, from `FIXIT_TAU_FRAC` |
| `$margin_x` | the set's **real** generation margin (`3` on the hard sets, `1.2` on the easy ones) |
| `$thinking_note` | reasoning-budget note; empty unless `--thinking-budget` is set |
| `$contract_block` | the rendered contract file |
| `$translate_range` `$rotate_range` `$scale_range` | fault magnitude ranges, read **from the instance** |

### Contract files

| variable | value |
|---|---|
| `$value_grid` `$angle_grid` `$scale_grid` | continuous action bounds |
| `$K` | SIMULATE budget (0 for oneshot) |
| `$fixable_note` | the "only fixable parts" line; empty when the fixable column is hidden |
| `$sim_returns` | what SIMULATE returns, differing by modality |

### Step file

`$observation`, `$budget_left`, `$commit_note`, `$history` (last three SIMULATEs).

## Output contract the parser enforces

`action_parser.py` will reject anything else, and a rejected turn costs a turn:

```
<think>reasoning</think>
<act>SIMULATE TRANSLATE(P1, Y, -0.04)</act>
```

- mode is `SIMULATE` or `COMMIT`; `<backtrack/>` may precede `<act>`
- calls: `TRANSLATE|ROTATE|SCALE(P#, X|Y|Z, value)`, `NO_FIX()`, `RESET()` (stack only)
- batch accepts an ordered list of up to 6 in `[...]` separated by `;`; stack accepts exactly one
- magnitudes are clamped to the action bounds, not snapped to a grid

## Two things the old prompts got wrong

Worth not repeating.

**Never hardcode a number the instance owns.** `margin_x` and the magnitude ranges were literals
(`3x this tolerance`, `0.08-0.20 m`). On a set generated at margin 1.2 with 0.35× magnitudes, the
prompt stated values several times off — worse than saying nothing.

**Concrete exemplars get copied verbatim.** With `<act>SIMULATE TRANSLATE(P1, Y, -0.04)</act>` in the
procedure block, Qwen3-VL-8B opened **90% of episodes** with exactly that action, and 67% of all its
actions used the exemplar's axis. Replacing the values with metasyntax cut verbatim copying from 62%
to 13%. It did not improve the score — but it removes a confound from any result about *what the
model chose*.

## Variant switch

`FIXIT_PROMPT_VARIANT=foo` makes `system.txt` resolve to `system_foo.txt` when that file exists, and
fall back to the base file when it does not — so an ablation can never half-apply. The variant is
recorded in the run manifest.
