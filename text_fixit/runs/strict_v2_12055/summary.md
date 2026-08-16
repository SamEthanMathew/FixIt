# strict_v2_12055

**1/1 solved (100%)** — 1 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_strict` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 1 from `data/instances_std30.jsonl` |
| mean difficulty | **3.17× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| translate | 1/1 | 0.44× |

## Outcome

- iterations when **solved**: 2–2 (median 2, mean 2)
- iterations when **failed**: —
- problems that ever got under threshold: **1/1**
- closest approach (× tolerance): best **0.44×**, median 0.44×, mean 0.44×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 1.36× | 1.36× | 0/1 |
| 2 | 0.44× | 0.44× | 1/1 |
| 3 | 0.44× | 0.44× | 1/1 |

## Cost

- wall clock: **8s** total, 7.2–7.2 (median 7.2, mean 7.2) per trial
- per-turn latency: 1.1–1.3 (median 1.1, mean 1.17)
- tokens: 8,687 prompt + 165 output (of which 0 thinking, 165 visible) = **8,852** (8,852/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `12055_ctrl_translate_0` | translate | **PASS** | 2 | 0.44× | -15 | `TRANSLATE(P0, X, -0.08777)` |
