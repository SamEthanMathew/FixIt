# strict_pilot_12055

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
| translate | 0/1 | 3.33× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **3.33×**, median 3.33×, mean 3.33×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 3.33× | 3.33× | 0/1 |
| 2 | 3.33× | 3.33× | 0/1 |
| 3 | 3.33× | 3.33× | 0/1 |
| 4 | 3.33× | 3.33× | 0/1 |
| 5 | 3.33× | 3.33× | 0/1 |
| 6 | 3.33× | 3.33× | 0/1 |
| 7 | 3.33× | 3.33× | 0/1 |
| 8 | 3.33× | 3.33× | 0/1 |
| 9 | 3.33× | 3.33× | 0/1 |
| 10 | 3.33× | 3.33× | 0/1 |
| 11 | 3.33× | 3.33× | 0/1 |

## Cost

- wall clock: **19s** total, 17.7–17.7 (median 17.7, mean 17.7) per trial
- per-turn latency: 0.8–1.3 (median 1.2, mean 1.19)
- tokens: 49,082 prompt + 454 output (of which 0 thinking, 454 visible) = **49,536** (49,536/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12055_ctrl_translate_0` | translate | fail | 10 | 3.33× | +96 | `TRANSLATE(P0, X, -0.08777)` |
