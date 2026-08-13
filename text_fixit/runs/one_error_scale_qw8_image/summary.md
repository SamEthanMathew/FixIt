# one_error_scale_qw8_image

**1/30 solved (3%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_scale` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 6.64× |
| scale | 0/10 | 9.4× |
| translate | 1/10 | 5.43× |

## Outcome

- iterations when **solved**: 3–3 (median 3, mean 3)
- iterations when **failed**: 0–10 (median 9, mean 7)
- problems that ever got under threshold: **1/30**
- closest approach (× tolerance): best **0.18×**, median 6.99×, mean 7.16×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 8.02× | 3.03× | 0/30 |
| 2 | 7.27× | 1.83× | 0/28 |
| 3 | 7.19× | 0.18× | 1/28 |
| 4 | 7.23× | 0.18× | 1/26 |
| 5 | 7.57× | 2.15× | 0/23 |
| 6 | 7.41× | 2.15× | 0/20 |
| 7 | 7.26× | 2.15× | 0/17 |
| 8 | 7.13× | 2.15× | 0/17 |
| 9 | 6.89× | 2.15× | 0/17 |
| 10 | 6.84× | 2.15× | 0/16 |
| 11 | 5.81× | 2.15× | 0/14 |

## Cost

- wall clock: **979s** total, 6.7–57.5 (median 34.4, mean 32.59) per trial
- per-turn latency: 0.4–3.1 (median 1.7, mean 1.66)
- tokens: 1,328,158 prompt + 23,515 output (of which 0 thinking, 23,515 visible) = **1,351,673** (45,056/trial)

## Integrity

- invalid actions: 109
- trials hit by an API give-up: 0
- images sent per turn: [0, 2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 8 | 7.67× | +173 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 3 | 0.18× | -20 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 3 | 3.75× | +147 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 4 | 8.29× | +170 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 10 | 4.0× | +113 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 5 | 10.54× | +165 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 2 | 7.25× | +188 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 3.27× | +71 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 6.13× | +119 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 9 | 14.13× | +340 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 2 | 6.03× | +179 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 5.74× | +231 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 4 | 2.45× | +21 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 2.15× | +34 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 4.99× | +102 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 5 | 9.17× | +118 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 8.28× | +413 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 0 | 8.58× | +191 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 5 | 4.9× | +113 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 9 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 10 | 5.63× | +145 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 0 | 14.3× | +318 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 3.03× | +53 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 4 | 14.89× | +348 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 10 | 7.94× | +562 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 8.7× | +427 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 3 | 7.31× | +215 | `SCALE(P0, X, 0.715502)` |
