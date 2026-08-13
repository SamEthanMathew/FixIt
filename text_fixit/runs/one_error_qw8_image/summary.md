# one_error_qw8_image

**0/30 solved (0%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 6.96× |
| scale | 0/10 | 9.0× |
| translate | 0/10 | 5.23× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 3–10 (median 10, mean 8.77)
- problems that ever got under threshold: **0/30**
- closest approach (× tolerance): best **2.09×**, median 6.62×, mean 7.06×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.98× | 3.03× | 0/30 |
| 2 | 7.62× | 2.59× | 0/30 |
| 3 | 7.41× | 2.59× | 0/30 |
| 4 | 7.24× | 2.09× | 0/30 |
| 5 | 7.17× | 2.09× | 0/28 |
| 6 | 7.11× | 2.09× | 0/28 |
| 7 | 7.1× | 2.09× | 0/28 |
| 8 | 7.32× | 2.09× | 0/26 |
| 9 | 7.3× | 2.09× | 0/24 |
| 10 | 7.47× | 2.09× | 0/23 |
| 11 | 7.83× | 2.09× | 0/16 |

## Cost

- wall clock: **1001s** total, 9.8–44.4 (median 33.4, mean 33.32) per trial
- per-turn latency: 0.5–3.8 (median 1.65, mean 1.66)
- tokens: 1,361,687 prompt + 24,232 output (of which 0 thinking, 24,232 visible) = **1,385,919** (46,197/trial)

## Integrity

- invalid actions: 67
- trials hit by an API give-up: 0
- images sent per turn: [0, 2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 6.51× | +143 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 8 | 2.63× | +41 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 9 | 2.6× | +65 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 9 | 7.72× | +165 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 9 | 3.97× | +148 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 9 | 10.32× | +162 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 7 | 7.12× | +152 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 2.09× | +50 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 6 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 3 | 6.13× | +119 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.14× | +338 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 10 | 5.6× | +123 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 7 | 7.89× | +179 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 9 | 2.59× | +39 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.67× | +35 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 5.87× | +104 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 10.48× | +168 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 9 | 7.76× | +141 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 10 | 8.54× | +194 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 3.07× | +60 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 9 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 6 | 5.28× | +106 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 11.83× | +319 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 3.03× | +52 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 14.76× | +318 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 3 | 7.94× | +202 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 8.43× | +169 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 6.47× | +199 | `SCALE(P0, X, 0.715502)` |
