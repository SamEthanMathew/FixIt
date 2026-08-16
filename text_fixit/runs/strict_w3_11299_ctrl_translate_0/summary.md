# strict_w3_11299_ctrl_translate_0

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
| translate | 0/1 | 2.76× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 8–8 (median 8, mean 8)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **2.76×**, median 2.76×, mean 2.76×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 2.76× | 2.76× | 0/1 |
| 2 | 2.76× | 2.76× | 0/1 |
| 3 | 2.76× | 2.76× | 0/1 |
| 4 | 2.76× | 2.76× | 0/1 |
| 5 | 2.76× | 2.76× | 0/1 |
| 6 | 2.76× | 2.76× | 0/1 |
| 7 | 2.76× | 2.76× | 0/1 |
| 8 | 2.76× | 2.76× | 0/1 |
| 9 | 2.76× | 2.76× | 0/1 |

## Cost

- wall clock: **40s** total, 39.5–39.5 (median 39.5, mean 39.5) per trial
- per-turn latency: 1.1–1.5 (median 1.3, mean 1.31)
- tokens: 45,292 prompt + 892 output (of which 0 thinking, 892 visible) = **46,184** (46,184/trial)

## Integrity

- invalid actions: 7
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `11299_ctrl_translate_0` | translate | fail | 8 | 2.76× | +44 | `TRANSLATE(P1, X, -0.12826)` |
