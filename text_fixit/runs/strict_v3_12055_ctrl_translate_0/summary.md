# strict_v3_12055_ctrl_translate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **3.17× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| translate | 0/1 | 1.0× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 2–2 (median 2, mean 2)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **1.0×**, median 1.0×, mean 1.0×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 1.0× | 1.0× | 0/1 |
| 2 | 1.0× | 1.0× | 0/1 |
| 3 | 1.0× | 1.0× | 0/1 |

## Cost

- wall clock: **28s** total, 27.4–27.4 (median 27.4, mean 27.4) per trial
- per-turn latency: 0.7–1.5 (median 0.8, mean 0.87)
- tokens: 65,513 prompt + 599 output (of which 0 thinking, 599 visible) = **66,112** (66,112/trial)

## Integrity

- invalid actions: 13
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12055_ctrl_translate_0` | translate | fail | 2 | 1.0× | +0 | `TRANSLATE(P0, X, -0.08777)` |
