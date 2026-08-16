# strict_w3_10143_ctrl_rotate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **3.27× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/1 | 3.27× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **3.27×**, median 3.27×, mean 3.27×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 3.27× | 3.27× | 0/1 |
| 2 | 3.27× | 3.27× | 0/1 |
| 3 | 3.27× | 3.27× | 0/1 |
| 4 | 3.27× | 3.27× | 0/1 |
| 5 | 3.27× | 3.27× | 0/1 |
| 6 | 3.27× | 3.27× | 0/1 |
| 7 | 3.27× | 3.27× | 0/1 |
| 8 | 3.27× | 3.27× | 0/1 |
| 9 | 3.27× | 3.27× | 0/1 |
| 10 | 3.27× | 3.27× | 0/1 |
| 11 | 3.27× | 3.27× | 0/1 |

## Cost

- wall clock: **17s** total, 15.7–15.7 (median 15.7, mean 15.7) per trial
- per-turn latency: 1.0–1.5 (median 1.2, mean 1.22)
- tokens: 32,606 prompt + 582 output (of which 0 thinking, 582 visible) = **33,188** (33,188/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
