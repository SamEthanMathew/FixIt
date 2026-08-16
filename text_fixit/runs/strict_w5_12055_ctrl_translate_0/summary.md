# strict_w5_12055_ctrl_translate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen` · image |
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
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **1.0×**, median 1.0×, mean 1.0×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 1.0× | 1.0× | 0/1 |
| 2 | 1.0× | 1.0× | 0/1 |
| 3 | 1.0× | 1.0× | 0/1 |
| 4 | 1.0× | 1.0× | 0/1 |
| 5 | 1.0× | 1.0× | 0/1 |
| 6 | 1.0× | 1.0× | 0/1 |
| 7 | 1.0× | 1.0× | 0/1 |
| 8 | 1.0× | 1.0× | 0/1 |
| 9 | 1.0× | 1.0× | 0/1 |
| 10 | 1.0× | 1.0× | 0/1 |
| 11 | 1.0× | 1.0× | 0/1 |

## Cost

- wall clock: **18s** total, 17.1–17.1 (median 17.1, mean 17.1) per trial
- per-turn latency: 1.1–1.5 (median 1.2, mean 1.25)
- tokens: 32,266 prompt + 587 output (of which 0 thinking, 587 visible) = **32,853** (32,853/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12055_ctrl_translate_0` | translate | fail | 10 | 1.0× | +76 | `TRANSLATE(P0, X, -0.08777)` |
