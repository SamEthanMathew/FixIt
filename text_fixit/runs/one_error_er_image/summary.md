# one_error_er_image

**19/30 solved (63%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `gemini-robotics-er-2-preview` |
| prompt set | `one_error` |
| agent / modality | `loop_gemini_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 10/10 | 0.39× |
| scale | 6/10 | 3.0× |
| translate | 3/10 | 4.3× |

## Outcome

- iterations when **solved**: 1–10 (median 3, mean 3.89)
- iterations when **failed**: 9–10 (median 10, mean 9.91)
- problems that ever got under threshold: **19/30**
- closest approach (× tolerance): best **0.04×**, median 0.6×, mean 2.56×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 5.79× | 0.05× | 4/30 |
| 2 | 4.65× | 0.05× | 9/30 |
| 3 | 4.35× | 0.05× | 7/26 |
| 4 | 4.72× | 0.12× | 4/22 |
| 5 | 4.28× | 0.14× | 5/20 |
| 6 | 4.12× | 0.1× | 7/19 |
| 7 | 4.84× | 0.1× | 4/16 |
| 8 | 5.78× | 0.1× | 1/13 |
| 9 | 5.74× | 0.04× | 1/13 |
| 10 | 5.46× | 0.04× | 2/13 |
| 11 | 5.68× | 0.35× | 1/11 |

## Cost

- wall clock: **2058s** total, 7.7–271.4 (median 50.65, mean 68.55) per trial
- per-turn latency: 1.6–126.9 (median 5.8, mean 8.77)
- tokens: 1,400,475 prompt + 250,613 output (of which 219,093 thinking, 31,520 visible) = **1,651,088** (55,036/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 1
- images sent per turn: [2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 7.96× | +188 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 5 | 0.18× | -20 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 10 | 3.55× | +65 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | **PASS** | 10 | 0.35× | -15 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 10 | 3.16× | +104 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 16.52× | +347 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 10 | 1.02× | +9 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 3.2× | +133 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | **PASS** | 6 | 0.69× | -8 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 6.33× | +168 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | **PASS** | 4 | 0.66× | -9 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | **PASS** | 2 | 0.53× | -12 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | **PASS** | 3 | 0.12× | -23 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | **PASS** | 9 | 0.04× | -14 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | **PASS** | 6 | 0.83× | -2 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | **PASS** | 1 | 0.12× | -19 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | **PASS** | 1 | 0.31× | -10 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | **PASS** | 2 | 0.05× | -20 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | **PASS** | 2 | 0.96× | -1 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | **PASS** | 2 | 0.33× | -19 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | **PASS** | 6 | 0.27× | -15 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | **PASS** | 1 | 0.05× | -24 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | **PASS** | 5 | 0.51× | -12 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 2.15× | +52 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | **PASS** | 3 | 0.19× | -18 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | **PASS** | 1 | 0.09× | -27 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 9 | 8.39× | +167 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | **PASS** | 5 | 0.14× | -25 | `SCALE(P0, X, 0.715502)` |
