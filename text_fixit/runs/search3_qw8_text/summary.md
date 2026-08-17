# search3_qw8_text

**6/30 solved (20%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_search` |
| agent / modality | `loop_qwen` · text |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 2/10 | 5.74× |
| scale | 2/10 | 5.59× |
| translate | 2/10 | 3.71× |

## Outcome

- iterations when **solved**: 1–10 (median 4.5, mean 4.67)
- iterations when **failed**: 9–10 (median 10, mean 9.96)
- problems that ever got under threshold: **6/30**
- closest approach (× tolerance): best **0.01×**, median 4.26×, mean 5.01×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 9.44× | 0.01× | 2/30 |
| 2 | 7.67× | 0.01× | 2/30 |
| 3 | 7.98× | 1.31× | 0/28 |
| 4 | 7.35× | 0.7× | 1/28 |
| 5 | 7.13× | 0.7× | 2/28 |
| 6 | 7.1× | 0.93× | 1/27 |
| 7 | 6.85× | 0.96× | 1/26 |
| 8 | 6.65× | 0.96× | 1/26 |
| 9 | 6.14× | 1.31× | 0/25 |
| 10 | 5.91× | 0.84× | 1/25 |
| 11 | 5.86× | 0.84× | 1/24 |

## Cost

- wall clock: **644s** total, 3.6–104.2 (median 19.45, mean 21.43) per trial
- per-turn latency: 0.8–6.8 (median 1.6, mean 1.71)
- tokens: 793,056 prompt + 18,568 output (of which 0 thinking, 18,568 visible) = **811,624** (27,054/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | **PASS** | 1 | 0.02× | -25 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 10 | 4.65× | +91 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 10 | 1.39× | +65 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 7.72× | +153 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -24 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 10.35× | +218 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 9 | 7.07× | +157 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 1.31× | +9 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 1.38× | +9 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.11× | +489 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | **PASS** | 4 | 0.7× | -8 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 9.95× | +235 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.79× | +33 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 1.94× | +20 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.35× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 7.97× | +145 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | **PASS** | 7 | 0.96× | -1 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 3.35× | +91 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 7.87× | +139 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 10.77× | +177 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | **PASS** | 10 | 0.84× | -4 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 9.37× | +200 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | **PASS** | 5 | 0.93× | -2 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 5.51× | +109 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 6.25× | +118 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 10 | 4.1× | +90 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 4.42× | +77 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 5.88× | +143 | `SCALE(P0, X, 0.715502)` |
