# strict_v3_12250_ctrl_scale_0

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
| scale | 0/1 | 6.83× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 2–2 (median 2, mean 2)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **6.83×**, median 6.83×, mean 6.83×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 6.83× | 6.83× | 0/1 |
| 2 | 6.83× | 6.83× | 0/1 |
| 3 | 6.83× | 6.83× | 0/1 |

## Cost

- wall clock: **6s** total, 5.0–5.0 (median 5, mean 5) per trial
- per-turn latency: 1.3–1.6 (median 1.4, mean 1.43)
- tokens: 10,550 prompt + 171 output (of which 0 thinking, 171 visible) = **10,721** (10,721/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12250_ctrl_scale_0` | scale | fail | 2 | 6.83× | +183 | `SCALE(P1, Y, 0.733483)` |
