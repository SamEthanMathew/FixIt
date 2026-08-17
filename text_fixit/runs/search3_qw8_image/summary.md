# search3_qw8_image

**9/30 solved (30%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_search` |
| agent / modality | `loop_qwen` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 2/10 | 5.87× |
| scale | 2/10 | 2.61× |
| translate | 5/10 | 2.59× |

## Outcome

- iterations when **solved**: 1–10 (median 2, mean 3.33)
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **9/30**
- closest approach (× tolerance): best **0.01×**, median 2.75×, mean 3.69×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 8.33× | 0.01× | 4/30 |
| 2 | 7.49× | 0.01× | 5/30 |
| 3 | 8.63× | 0.69× | 1/26 |
| 4 | 7.73× | 0.02× | 2/25 |
| 5 | 7.58× | 0.02× | 2/25 |
| 6 | 7.7× | 0.96× | 1/23 |
| 7 | 7.22× | 0.96× | 1/23 |
| 8 | 6.79× | 1.64× | 0/22 |
| 9 | 5.47× | 1.64× | 0/22 |
| 10 | 4.92× | 0.41× | 1/22 |
| 11 | 4.92× | 0.41× | 1/22 |

## Cost

- wall clock: **626s** total, 4.3–32.0 (median 23.85, mean 20.84) per trial
- per-turn latency: 0.5–5.5 (median 1.9, mean 1.93)
- tokens: 947,188 prompt + 18,246 output (of which 0 thinking, 18,246 visible) = **965,434** (32,181/trial)

## Integrity

- invalid actions: 4
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | **PASS** | 1 | 0.02× | -25 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 4 | 0.02× | -24 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -25 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 6.64× | +129 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -24 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 10.33× | +162 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 10 | 3.47× | +151 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -27 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 2.23× | +28 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.14× | +338 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | **PASS** | 4 | 0.7× | -8 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 10.04× | +310 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.79× | +33 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 1.94× | +20 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.76× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 7.98× | +147 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | **PASS** | 6 | 0.96× | -1 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 4.12× | +91 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 1.74× | +15 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 4.97× | +55 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 10 | 2.32× | +33 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 4.45× | +82 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | **PASS** | 2 | 0.69× | -8 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 1.85× | +20 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 3.42× | +54 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | **PASS** | 10 | 0.41× | -17 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 4.13× | +71 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 2.12× | +33 | `SCALE(P0, X, 0.715502)` |
