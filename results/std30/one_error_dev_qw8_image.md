# one_error_dev_qw8_image

**1/30 solved (3%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_dev` |
| agent / modality | `loop_qwen_full` · image |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 6.97× |
| scale | 0/10 | 7.9× |
| translate | 1/10 | 4.78× |

## Outcome

- iterations when **solved**: 10–10 (median 10, mean 10)
- iterations when **failed**: 3–10 (median 9, mean 8.93)
- problems that ever got under threshold: **1/30**
- closest approach (× tolerance): best **0.18×**, median 6.41×, mean 6.55×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 8.08× | 3.03× | 0/30 |
| 2 | 7.51× | 1.36× | 0/30 |
| 3 | 7.17× | 1.36× | 0/30 |
| 4 | 6.99× | 1.36× | 0/30 |
| 5 | 7.03× | 1.36× | 0/29 |
| 6 | 6.97× | 1.36× | 0/29 |
| 7 | 6.86× | 1.36× | 0/29 |
| 8 | 6.83× | 1.36× | 0/29 |
| 9 | 6.62× | 1.36× | 0/26 |
| 10 | 6.55× | 0.18× | 1/26 |
| 11 | 4.99× | 0.18× | 1/11 |

## Cost

- wall clock: **1069s** total, 10.9–52.0 (median 35.2, mean 35.59) per trial
- per-turn latency: 0.1–3.3 (median 2.1, mean 2.02)
- tokens: 1,413,017 prompt + 28,420 output (of which 0 thinking, 28,420 visible) = **1,441,437** (48,048/trial)

## Integrity

- invalid actions: 47
- trials hit by an API give-up: 0
- images sent per turn: [0, 2, 4]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 6.89× | +173 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | **PASS** | 10 | 0.18× | -20 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 9 | 2.2× | +92 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 7.72× | +168 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 10 | 3.97× | +84 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 9 | 10.33× | +163 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 9 | 5.86× | +155 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 9 | 1.36× | +91 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 9 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 6.13× | +119 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 7 | 13.9× | +340 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 9 | 5.2× | +120 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 9 | 9.94× | +237 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 2.45× | +33 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 2.15× | +35 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 5.99× | +106 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 9 | 11.76× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 9 | 7.98× | +148 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 9 | 6.69× | +182 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 9 | 3.6× | +93 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 9 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 9 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 7 | 3.8× | +70 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 9.37× | +328 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 3.03× | +52 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 7 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 9 | 14.74× | +310 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 3 | 1.64× | +19 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 6.97× | +177 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 9 | 7.15× | +180 | `SCALE(P0, X, 0.715502)` |
