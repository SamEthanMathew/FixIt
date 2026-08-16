# strict_w4_11299_ctrl_translate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **5.19× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| translate | 0/1 | 1.55× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **1.55×**, median 1.55×, mean 1.55×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 2.76× | 2.76× | 0/1 |
| 2 | 2.76× | 2.76× | 0/1 |
| 3 | 2.76× | 2.76× | 0/1 |
| 4 | 1.55× | 1.55× | 0/1 |
| 5 | 1.55× | 1.55× | 0/1 |
| 6 | 1.55× | 1.55× | 0/1 |
| 7 | 1.55× | 1.55× | 0/1 |
| 8 | 1.55× | 1.55× | 0/1 |
| 9 | 1.55× | 1.55× | 0/1 |
| 10 | 1.55× | 1.55× | 0/1 |
| 11 | 1.55× | 1.55× | 0/1 |

## Cost

- wall clock: **17s** total, 16.3–16.3 (median 16.3, mean 16.3) per trial
- per-turn latency: 1.2–1.4 (median 1.3, mean 1.33)
- tokens: 29,863 prompt + 607 output (of which 0 thinking, 607 visible) = **30,470** (30,470/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `11299_ctrl_translate_0` | translate | fail | 10 | 1.55× | +14 | `TRANSLATE(P1, X, -0.12826)` |
