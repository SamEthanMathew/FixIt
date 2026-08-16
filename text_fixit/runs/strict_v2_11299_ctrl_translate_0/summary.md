# strict_v2_11299_ctrl_translate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **5.19× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| translate | 0/1 | 5.18× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 0–0 (median 0, mean 0)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **5.18×**, median 5.18×, mean 5.18×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 5.18× | 5.18× | 0/1 |

## Cost

- wall clock: **36s** total, 35.6–35.6 (median 35.6, mean 35.6) per trial
- per-turn latency: 1.0–1.4 (median 1, mean 1.05)
- tokens: 62,575 prompt + 815 output (of which 0 thinking, 815 visible) = **63,390** (63,390/trial)

## Integrity

- invalid actions: 15
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `11299_ctrl_translate_0` | translate | fail | 0 | 5.18× | +104 | `TRANSLATE(P1, X, -0.12826)` |
