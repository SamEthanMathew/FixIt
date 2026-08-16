# strict_v2_12250_ctrl_scale_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **6.57× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| scale | 0/1 | 7.12× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 6–6 (median 6, mean 6)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **7.12×**, median 7.12×, mean 7.12×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.12× | 7.12× | 0/1 |
| 2 | 7.12× | 7.12× | 0/1 |
| 3 | 7.12× | 7.12× | 0/1 |
| 4 | 7.12× | 7.12× | 0/1 |
| 5 | 7.12× | 7.12× | 0/1 |
| 6 | 7.12× | 7.12× | 0/1 |
| 7 | 7.12× | 7.12× | 0/1 |

## Cost

- wall clock: **26s** total, 25.6–25.6 (median 25.6, mean 25.6) per trial
- per-turn latency: 0.6–1.6 (median 0.7, mean 0.94)
- tokens: 68,197 prompt + 600 output (of which 0 thinking, 600 visible) = **68,797** (68,797/trial)

## Integrity

- invalid actions: 9
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12250_ctrl_scale_0` | scale | fail | 6 | 7.12× | +178 | `SCALE(P1, Y, 0.733483)` |
