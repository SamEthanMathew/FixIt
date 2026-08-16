# strict_v2_10143_ctrl_rotate_0

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
- iterations when **failed**: 0–0 (median 0, mean 0)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **3.27×**, median 3.27×, mean 3.27×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 3.27× | 3.27× | 0/1 |

## Cost

- wall clock: **32s** total, 31.3–31.3 (median 31.3, mean 31.3) per trial
- per-turn latency: 0.8–1.3 (median 0.9, mean 0.93)
- tokens: 61,112 prompt + 708 output (of which 0 thinking, 708 visible) = **61,820** (61,820/trial)

## Integrity

- invalid actions: 15
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10143_ctrl_rotate_0` | rotate | fail | 0 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
