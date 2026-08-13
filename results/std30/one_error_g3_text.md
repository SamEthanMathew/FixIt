# one_error_g3_text

**14/30 solved (47%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `gemini-3.1-pro-preview` |
| prompt set | `one_error` |
| agent / modality | `loop_gemini_full` · text |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 2/10 | 5.03× |
| scale | 6/10 | 2.96× |
| translate | 6/10 | 2.75× |

## Outcome

- iterations when **solved**: 1–10 (median 1.5, mean 3.14)
- iterations when **failed**: 3–10 (median 9.5, mean 8.94)
- problems that ever got under threshold: **14/30**
- closest approach (× tolerance): best **0.0×**, median 3.21×, mean 3.58×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 8.8× | 0.0× | 7/30 |
| 2 | 6.58× | 0.0× | 9/30 |
| 3 | 7.3× | 0.28× | 2/23 |
| 4 | 6.97× | 0.73× | 1/21 |
| 5 | 6.84× | 0.73× | 1/20 |
| 6 | 6.65× | 0.63× | 2/19 |
| 7 | 5.95× | 0.63× | 3/19 |
| 8 | 6.7× | 0.74× | 1/16 |
| 9 | 7.1× | 3.18× | 0/15 |
| 10 | 6.61× | 3.18× | 0/15 |
| 11 | 6.88× | 0.32× | 1/9 |

## Cost

- wall clock: **52718s** total, 11.9–4771.8 (median 1883.35, mean 1757.28) per trial
- per-turn latency: 2.5–1166.2 (median 220.9, mean 227.76)
- tokens: 1,498,862 prompt + 5,231,899 output (of which 5,022,071 thinking, 209,828 visible) = **6,730,761** (224,359/trial)

## Integrity

- invalid actions: 2
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 9 | 3.88× | +174 | `TRANSLATE(P1, X, -0.19847)` |
| `10685_ctrl_scale_0` | scale | fail | 3 | 3.03× | +52 | `SCALE(P2, X, 0.690325)` |
| `11211_ctrl_rotate_0` | rotate | fail | 9 | 8.8× | +233 | `ROTATE(P0, Z, 22.5051)` |
| `12249_ctrl_translate_0` | translate | **PASS** | 1 | 0.09× | -23 | `TRANSLATE(P0, X, 0.17520)` |
| `12252_ctrl_rotate_0` | rotate | **PASS** | 7 | 0.74× | -7 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.38× | +207 | `ROTATE(P2, Z, -23.7176)` |
| `10867_ctrl_scale_0` | scale | fail | 9 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 2 | 0.42× | -14 | `TRANSLATE(P1, Y, -0.14547)` |
| `12042_ctrl_rotate_0` | rotate | fail | 6 | 3.8× | +155 | `ROTATE(P1, Z, -38.0044)` |
| `12055_ctrl_translate_0` | translate | **PASS** | 2 | 0.28× | -20 | `TRANSLATE(P0, X, -0.08777)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 14.0× | +301 | `SCALE(P2, Y, 0.771644)` |
| `10620_ctrl_translate_0` | translate | **PASS** | 10 | 0.32× | -17 | `TRANSLATE(P2, X, 0.08216)` |
| `10638_ctrl_scale_0` | scale | **PASS** | 1 | 0.02× | -22 | `SCALE(P1, X, 0.739679)` |
| `10849_ctrl_translate_0` | translate | fail | 10 | 4.09× | +264 | `TRANSLATE(P0, X, -0.08517)` |
| `12050_ctrl_rotate_0` | rotate | fail | 9 | 3.79× | +78 | `ROTATE(P0, X, -23.0027)` |
| `10586_ctrl_translate_0` | translate | **PASS** | 6 | 0.9× | -2 | `TRANSLATE(P2, Y, -0.14191)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 5.32× | +348 | `TRANSLATE(P1, X, 0.18806)` |
| `11304_ctrl_rotate_0` | rotate | fail | 9 | 5.99× | +346 | `ROTATE(P0, X, 29.4375)` |
| `12248_ctrl_scale_0` | scale | **PASS** | 6 | 0.63× | -5 | `SCALE(P0, Y, 0.648390)` |
| `12250_ctrl_scale_0` | scale | **PASS** | 1 | 0.0× | -29 | `SCALE(P1, Y, 0.733483)` |
| `10612_ctrl_scale_0` | scale | **PASS** | 1 | 0.0× | -25 | `SCALE(P2, Y, 0.771633)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.76× | +300 | `ROTATE(P2, Z, -43.8612)` |
| `10655_ctrl_rotate_0` | rotate | **PASS** | 4 | 0.73× | -7 | `ROTATE(P1, X, -26.7650)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 1 | 0.37× | -15 | `TRANSLATE(P1, X, -0.12826)` |
| `11712_ctrl_scale_0` | scale | **PASS** | 1 | 0.0× | -22 | `SCALE(P1, X, 0.704582)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 5.71× | +362 | `ROTATE(P0, Y, -35.2125)` |
| `10797_ctrl_rotate_0` | rotate | fail | 10 | 5.58× | +177 | `ROTATE(P1, X, 22.8324)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 11.79× | +192 | `TRANSLATE(P0, Z, 0.17837)` |
| `10944_ctrl_scale_0` | scale | fail | 9 | 5.22× | +417 | `SCALE(P0, Y, 0.709604)` |
| `12054_ctrl_scale_0` | scale | **PASS** | 1 | 0.01× | -29 | `SCALE(P0, X, 0.715502)` |
