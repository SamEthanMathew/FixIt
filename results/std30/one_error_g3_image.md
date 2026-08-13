# one_error_g3_image

**16/30 solved (53%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `gemini-3.1-pro-preview` |
| prompt set | `one_error` |
| agent / modality | `loop_gemini_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 7/10 | 1.91× |
| scale | 9/10 | 1.45× |
| translate | 0/10 | 4.46× |

## Outcome

- iterations when **solved**: 1–6 (median 2.5, mean 2.88)
- iterations when **failed**: 1–10 (median 10, mean 7.93)
- problems that ever got under threshold: **16/30**
- closest approach (× tolerance): best **0.0×**, median 0.91×, mean 2.61×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 5.53× | 0.0× | 6/30 |
| 2 | 3.84× | 0.0× | 8/30 |
| 3 | 3.4× | 0.23× | 4/22 |
| 4 | 3.21× | 0.1× | 6/20 |
| 5 | 3.5× | 0.1× | 4/18 |
| 6 | 4.06× | 0.01× | 3/14 |
| 7 | 4.06× | 0.01× | 3/14 |
| 8 | 5.32× | 1.42× | 0/10 |
| 9 | 5.32× | 1.42× | 0/10 |
| 10 | 5.18× | 1.42× | 0/10 |
| 11 | 5.29× | 1.42× | 0/9 |

## Cost

- wall clock: **13516s** total, 19.4–2558.8 (median 239.05, mean 450.53) per trial
- per-turn latency: 2.7–1096.5 (median 19.8, mean 69.54)
- tokens: 1,892,770 prompt + 1,159,152 output (of which 926,682 thinking, 232,470 visible) = **3,051,922** (101,731/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 7.67× | +173 | `TRANSLATE(P1, X, -0.19847)` |
| `10685_ctrl_scale_0` | scale | **PASS** | 2 | 0.62× | -10 | `SCALE(P2, X, 0.690325)` |
| `11211_ctrl_rotate_0` | rotate | fail | 1 | 14.13× | +331 | `ROTATE(P0, Z, 22.5051)` |
| `12249_ctrl_translate_0` | translate | fail | 10 | 7.19× | +155 | `TRANSLATE(P0, X, 0.17520)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 1.42× | +306 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | **PASS** | 6 | 0.01× | -15 | `ROTATE(P2, Z, -23.7176)` |
| `10867_ctrl_scale_0` | scale | **PASS** | 6 | 0.81× | -5 | `SCALE(P0, X, 0.724298)` |
| `11178_ctrl_translate_0` | translate | fail | 6 | 2.63× | +156 | `TRANSLATE(P1, Y, -0.14547)` |
| `12042_ctrl_rotate_0` | rotate | **PASS** | 1 | 0.0× | -29 | `ROTATE(P1, Z, -38.0044)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 1.73× | +60 | `TRANSLATE(P0, X, -0.08777)` |
| `10489_ctrl_scale_0` | scale | **PASS** | 4 | 0.1× | -18 | `SCALE(P2, Y, 0.771644)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10638_ctrl_scale_0` | scale | **PASS** | 1 | 0.18× | -18 | `SCALE(P1, X, 0.739679)` |
| `10849_ctrl_translate_0` | translate | fail | 10 | 3.49× | +69 | `TRANSLATE(P0, X, -0.08517)` |
| `12050_ctrl_rotate_0` | rotate | **PASS** | 3 | 0.33× | -8 | `ROTATE(P0, X, -23.0027)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 6.13× | +139 | `TRANSLATE(P2, Y, -0.14191)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 5.32× | +171 | `TRANSLATE(P1, X, 0.18806)` |
| `11304_ctrl_rotate_0` | rotate | **PASS** | 4 | 0.12× | -19 | `ROTATE(P0, X, 29.4375)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `12250_ctrl_scale_0` | scale | **PASS** | 1 | 0.06× | -27 | `SCALE(P1, Y, 0.733483)` |
| `10612_ctrl_scale_0` | scale | **PASS** | 1 | 0.04× | -24 | `SCALE(P2, Y, 0.771633)` |
| `10627_ctrl_rotate_0` | rotate | **PASS** | 1 | 0.31× | -10 | `ROTATE(P2, Z, -43.8612)` |
| `10655_ctrl_rotate_0` | rotate | **PASS** | 2 | 0.94× | -2 | `ROTATE(P1, X, -26.7650)` |
| `11299_ctrl_translate_0` | translate | fail | 4 | 3.16× | +54 | `TRANSLATE(P1, X, -0.12826)` |
| `11712_ctrl_scale_0` | scale | **PASS** | 3 | 0.23× | -17 | `SCALE(P1, X, 0.704582)` |
| `10373_ctrl_rotate_0` | rotate | **PASS** | 6 | 0.05× | -20 | `ROTATE(P0, Y, -35.2125)` |
| `10797_ctrl_rotate_0` | rotate | fail | 1 | 1.76× | +20 | `ROTATE(P1, X, 22.8324)` |
| `10905_ctrl_translate_0` | translate | fail | 9 | 4.13× | +401 | `TRANSLATE(P0, Z, 0.17837)` |
| `10944_ctrl_scale_0` | scale | **PASS** | 4 | 0.87× | -3 | `SCALE(P0, Y, 0.709604)` |
| `12054_ctrl_scale_0` | scale | **PASS** | 1 | 0.04× | -28 | `SCALE(P0, X, 0.715502)` |
