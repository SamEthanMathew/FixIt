# search_qw8_image

**11/30 solved (37%)** — 30 distinct problems, one attempt each.

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
| scale | 4/10 | 5.89× |
| translate | 5/10 | 3.11× |

## Outcome

- iterations when **solved**: 1–10 (median 10, mean 8.36)
- iterations when **failed**: 1–10 (median 10, mean 9.47)
- problems that ever got under threshold: **11/30**
- closest approach (× tolerance): best **0.0×**, median 3.37×, mean 4.96×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 9.33× | 0.01× | 4/30 |
| 2 | 8.13× | 0.01× | 5/30 |
| 3 | 8.43× | 0.01× | 3/27 |
| 4 | 7.4× | 0.0× | 5/27 |
| 5 | 7.1× | 0.0× | 5/27 |
| 6 | 6.76× | 0.0× | 6/27 |
| 7 | 6.24× | 0.0× | 6/27 |
| 8 | 5.45× | 0.0× | 6/27 |
| 9 | 5.45× | 0.0× | 6/27 |
| 10 | 5.21× | 0.0× | 9/27 |
| 11 | 5.01× | 0.0× | 9/26 |

## Cost

- wall clock: **644s** total, 3.6–32.9 (median 22.55, mean 21.44) per trial
- per-turn latency: 1.1–5.6 (median 1.8, mean 1.82)
- tokens: 1,028,987 prompt + 22,238 output (of which 0 thinking, 22,238 visible) = **1,051,225** (35,041/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | **PASS** | 10 | 0.02× | -25 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 10 | 5.86× | +121 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -25 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 8.26× | +165 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 10 | 0.01× | -24 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 9 | 10.28× | +161 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 10 | 3.47× | +61 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -27 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | **PASS** | 10 | 0.0× | -23 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.08× | +489 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | **PASS** | 10 | 0.7× | -8 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 10.01× | +234 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.79× | +33 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 1.94× | +20 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.76× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 1 | 8.05× | +147 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | **PASS** | 10 | 0.96× | -1 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 4.12× | +91 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +244 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 10 | 6.76× | +143 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | **PASS** | 10 | 0.47× | -13 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | **PASS** | 10 | 0.69× | -8 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 14.74× | +640 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | **PASS** | 10 | 0.41× | -17 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 2.71× | +39 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | **PASS** | 10 | 0.87× | -4 | `SCALE(P0, X, 0.715502)` |
