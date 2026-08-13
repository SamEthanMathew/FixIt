# one_error_er_text

**10/30 solved (33%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `gemini-robotics-er-2-preview` |
| prompt set | `one_error` |
| agent / modality | `loop_gemini_full` · text |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 6.96× |
| scale | 6/10 | 2.23× |
| translate | 4/10 | 3.47× |

## Outcome

- iterations when **solved**: 1–8 (median 1, mean 2.5)
- iterations when **failed**: 8–10 (median 10, mean 9.8)
- problems that ever got under threshold: **10/30**
- closest approach (× tolerance): best **0.0×**, median 3.49×, mean 4.22×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.58× | 0.0× | 7/30 |
| 2 | 6.19× | 0.0× | 7/30 |
| 3 | 7.36× | 0.46× | 1/23 |
| 4 | 6.91× | 0.46× | 1/23 |
| 5 | 6.65× | 1.0× | 0/22 |
| 6 | 6.28× | 1.0× | 0/22 |
| 7 | 6.22× | 0.09× | 1/22 |
| 8 | 5.97× | 0.09× | 2/22 |
| 9 | 5.99× | 0.1× | 1/21 |
| 10 | 6.32× | 1.21× | 0/19 |
| 11 | 5.86× | 1.21× | 0/17 |

## Cost

- wall clock: **4235s** total, 4.1–377.7 (median 128.15, mean 141.11) per trial
- per-turn latency: 0.7–139.5 (median 9.2, mean 15.84)
- tokens: 900,438 prompt + 763,682 output (of which 753,884 thinking, 9,798 visible) = **1,664,120** (55,471/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 2
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 7.67× | +173 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 1 | 0.38× | -15 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 10 | 5.24× | +202 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 8.26× | +165 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 3 | 0.46× | -13 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 8 | 4.52× | +161 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | **PASS** | 7 | 0.09× | -23 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 3.92× | +382 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | **PASS** | 1 | 0.95× | -1 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.14× | +338 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 10 | 1.76× | +415 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 10.08× | +314 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 7.39× | +120 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.79× | +33 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 5.99× | +106 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 9 | 11.76× | +373 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 1.21× | +4 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 9 | 8.58× | +191 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 4.91× | +411 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | **PASS** | 8 | 0.1× | -18 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | **PASS** | 1 | 0.0× | -25 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 1.99× | +101 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 1.88× | +37 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | **PASS** | 1 | 0.02× | -22 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | **PASS** | 1 | 0.0× | -29 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | **PASS** | 1 | 0.01× | -22 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | **PASS** | 1 | 0.01× | -29 | `SCALE(P0, X, 0.715502)` |
