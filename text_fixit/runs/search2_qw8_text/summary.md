# search2_qw8_text

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
| rotate | 1/10 | 5.6× |
| scale | 1/10 | 5.65× |
| translate | 4/10 | 2.97× |

## Outcome

- iterations when **solved**: 3–10 (median 9.5, mean 8.5)
- iterations when **failed**: 9–10 (median 10, mean 9.92)
- problems that ever got under threshold: **7/30**
- closest approach (× tolerance): best **0.01×**, median 4.12×, mean 4.74×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 9.28× | 0.01× | 2/30 |
| 2 | 7.98× | 0.01× | 3/30 |
| 3 | 7.12× | 0.01× | 4/30 |
| 4 | 6.84× | 0.01× | 5/30 |
| 5 | 6.47× | 0.01× | 5/29 |
| 6 | 6.26× | 0.01× | 5/29 |
| 7 | 6.1× | 0.01× | 5/29 |
| 8 | 5.99× | 0.01× | 5/29 |
| 9 | 5.24× | 0.01× | 6/29 |
| 10 | 4.9× | 0.01× | 6/29 |
| 11 | 5.39× | 0.01× | 3/25 |

## Cost

- wall clock: **548s** total, 6.7–93.7 (median 15.5, mean 18.21) per trial
- per-turn latency: 0.8–2.8 (median 1.2, mean 1.37)
- tokens: 846,625 prompt + 19,975 output (of which 0 thinking, 19,975 visible) = **866,600** (28,887/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | **PASS** | 10 | 0.02× | -25 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 3 | 0.02× | -24 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 10 | 1.39× | +10 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 7.72× | +153 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 10 | 0.01× | -24 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 8.08× | +168 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 9 | 5.13× | +102 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | **PASS** | 9 | 0.66× | -9 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 3.54× | +59 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.11× | +489 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 9 | 0.7× | +132 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 9.89× | +232 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.72× | +32 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 1.94× | +20 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.35× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 8.05× | +147 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | **PASS** | 9 | 0.96× | -1 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 1.98× | +29 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 4.8× | +77 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +244 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 10 | 5.28× | +106 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 6.91× | +141 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | **PASS** | 10 | 0.79× | -2 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 5.51× | +109 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 6.25× | +118 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 10 | 4.1× | +163 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 4.13× | +71 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 7.16× | +180 | `SCALE(P0, X, 0.715502)` |
