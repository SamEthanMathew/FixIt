# strict_w3_12250_ctrl_scale_0

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
| scale | 0/1 | 7.28× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 8–8 (median 8, mean 8)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **7.28×**, median 7.28×, mean 7.28×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.28× | 7.28× | 0/1 |
| 2 | 7.28× | 7.28× | 0/1 |
| 3 | 7.28× | 7.28× | 0/1 |
| 4 | 7.28× | 7.28× | 0/1 |
| 5 | 7.28× | 7.28× | 0/1 |
| 6 | 7.28× | 7.28× | 0/1 |
| 7 | 7.28× | 7.28× | 0/1 |
| 8 | 7.28× | 7.28× | 0/1 |
| 9 | 7.28× | 7.28× | 0/1 |

## Cost

- wall clock: **36s** total, 35.0–35.0 (median 35, mean 35) per trial
- per-turn latency: 0.8–1.2 (median 1.1, mean 1.04)
- tokens: 44,401 prompt + 699 output (of which 0 thinking, 699 visible) = **45,100** (45,100/trial)

## Integrity

- invalid actions: 7
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12250_ctrl_scale_0` | scale | fail | 8 | 7.28× | +183 | `SCALE(P1, Y, 0.733483)` |
