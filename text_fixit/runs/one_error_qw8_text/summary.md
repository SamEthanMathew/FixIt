# one_error_qw8_text

**0/30 solved (0%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error` |
| agent / modality | `loop_qwen_full` · text |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 6.93× |
| scale | 0/10 | 8.43× |
| translate | 0/10 | 5.17× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 3–10 (median 10, mean 8.97)
- problems that ever got under threshold: **0/30**
- closest approach (× tolerance): best **1.11×**, median 6.67×, mean 6.84×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.83× | 3.03× | 0/30 |
| 2 | 7.58× | 1.88× | 0/30 |
| 3 | 7.19× | 1.88× | 0/30 |
| 4 | 7.13× | 1.88× | 0/30 |
| 5 | 7.19× | 1.88× | 0/29 |
| 6 | 7.13× | 1.11× | 0/29 |
| 7 | 7.08× | 1.11× | 0/29 |
| 8 | 7.05× | 1.11× | 0/28 |
| 9 | 6.48× | 1.11× | 0/25 |
| 10 | 6.59× | 1.11× | 0/22 |
| 11 | 6.37× | 1.11× | 0/17 |

## Cost

- wall clock: **1134s** total, 24.0–73.4 (median 37.05, mean 37.76) per trial
- per-turn latency: 0.3–3.4 (median 1.9, mean 1.92)
- tokens: 1,597,968 prompt + 30,737 output (of which 0 thinking, 30,737 visible) = **1,628,705** (54,290/trial)

## Integrity

- invalid actions: 72
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 7.67× | +173 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 10 | 3.84× | +71 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 9 | 2.2× | +30 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 6.94× | +166 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 10 | 3.16× | +104 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 7 | 10.3× | +164 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 3 | 5.05× | +100 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 9 | 3.2× | +61 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 6 | 6.13× | +119 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 9 | 11.54× | +339 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 10 | 5.2× | +121 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 7 | 9.97× | +235 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.13× | +39 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 8 | 3.65× | +32 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 8 | 5.99× | +106 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.76× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 8 | 7.38× | +133 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 9 | 7.07× | +194 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 3.61× | +89 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 10 | 6.76× | +143 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 7 | 11.83× | +288 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 1.11× | +52 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 9 | 12.64× | +311 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 10 | 6.62× | +170 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 7.58× | +177 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 5.51× | +182 | `SCALE(P0, X, 0.715502)` |
