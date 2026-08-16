# strict_v4_11299_ctrl_translate_0

**0/1 solved (0%)** — 1 distinct problems, one attempt each.

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
| translate | 0/1 | 1.14× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 2–2 (median 2, mean 2)
- problems that ever got under threshold: **0/1**
- closest approach (× tolerance): best **1.14×**, median 1.14×, mean 1.14×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 3.16× | 3.16× | 0/1 |
| 2 | 1.14× | 1.14× | 0/1 |
| 3 | 1.14× | 1.14× | 0/1 |

## Cost

- wall clock: **40s** total, 38.7–38.7 (median 38.7, mean 38.7) per trial
- per-turn latency: 1.1–1.8 (median 1.2, mean 1.21)
- tokens: 76,265 prompt + 902 output (of which 0 thinking, 902 visible) = **77,167** (77,167/trial)

## Integrity

- invalid actions: 13
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `11299_ctrl_translate_0` | translate | fail | 2 | 1.14× | +4 | `TRANSLATE(P1, X, -0.12826)` |
