# strict_v3_11299_ctrl_translate_0

**1/1 solved (100%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **5.19× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| translate | 1/1 | 0.88× |

## Outcome

- iterations when **solved**: 3–3 (median 3, mean 3)
- iterations when **failed**: —
- problems that ever got under threshold: **1/1**
- closest approach (× tolerance): best **0.88×**, median 0.88×, mean 0.88×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 3.16× | 3.16× | 0/1 |
| 2 | 1.14× | 1.14× | 0/1 |
| 3 | 0.88× | 0.88× | 1/1 |
| 4 | 0.88× | 0.88× | 1/1 |

## Cost

- wall clock: **19s** total, 18.6–18.6 (median 18.6, mean 18.6) per trial
- per-turn latency: 0.3–2.0 (median 0.3, mean 0.6)
- tokens: 66,931 prompt + 391 output (of which 0 thinking, 391 visible) = **67,322** (67,322/trial)

## Integrity

- invalid actions: 12
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `11299_ctrl_translate_0` | translate | **PASS** | 3 | 0.88× | -3 | `TRANSLATE(P1, X, -0.12826)` |
