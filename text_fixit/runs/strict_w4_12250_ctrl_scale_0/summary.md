# strict_w4_12250_ctrl_scale_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **6.57× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| scale | 0/1 | 6.83× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **6.83×**, median 6.83×, mean 6.83×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.28× | 7.28× | 0/1 |
| 2 | 7.28× | 7.28× | 0/1 |
| 3 | 7.28× | 7.28× | 0/1 |
| 4 | 7.28× | 7.28× | 0/1 |
| 5 | 6.83× | 6.83× | 0/1 |
| 6 | 6.83× | 6.83× | 0/1 |
| 7 | 6.83× | 6.83× | 0/1 |
| 8 | 6.83× | 6.83× | 0/1 |
| 9 | 6.83× | 6.83× | 0/1 |
| 10 | 6.83× | 6.83× | 0/1 |
| 11 | 6.83× | 6.83× | 0/1 |

## Cost

- wall clock: **15s** total, 14.1–14.1 (median 14.1, mean 14.1) per trial
- per-turn latency: 1.1–1.3 (median 1.1, mean 1.15)
- tokens: 32,063 prompt + 568 output (of which 0 thinking, 568 visible) = **32,631** (32,631/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12250_ctrl_scale_0` | scale | fail | 10 | 6.83× | +198 | `SCALE(P1, Y, 0.733483)` |
