# strict_v4_10143_ctrl_rotate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen_full` · image |
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
- iterations when **failed**: 4–4 (median 4, mean 4)
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

## Cost

- wall clock: **36s** total, 35.3–35.3 (median 35.3, mean 35.3) per trial
- per-turn latency: 0.8–2.6 (median 0.8, mean 1.16)
- tokens: 77,860 prompt + 848 output (of which 0 thinking, 848 visible) = **78,708** (78,708/trial)

## Integrity

- invalid actions: 11
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10143_ctrl_rotate_0` | rotate | fail | 4 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
