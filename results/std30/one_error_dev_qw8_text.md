# one_error_dev_qw8_text

**0/30 solved (0%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_dev` |
| agent / modality | `loop_qwen_full` · text |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 7.17× |
| scale | 0/10 | 8.5× |
| translate | 0/10 | 5.49× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 2–10 (median 10, mean 8.97)
- problems that ever got under threshold: **0/30**
- closest approach (× tolerance): best **2.59×**, median 6.75×, mean 7.05×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 7.86× | 3.03× | 0/30 |
| 2 | 7.59× | 3.03× | 0/30 |
| 3 | 7.47× | 3.03× | 0/30 |
| 4 | 7.32× | 3.03× | 0/29 |
| 5 | 7.4× | 2.63× | 0/28 |
| 6 | 7.39× | 2.63× | 0/28 |
| 7 | 7.36× | 2.63× | 0/28 |
| 8 | 7.1× | 2.63× | 0/27 |
| 9 | 6.92× | 2.59× | 0/27 |
| 10 | 6.91× | 2.59× | 0/26 |
| 11 | 6.31× | 2.59× | 0/16 |

## Cost

- wall clock: **1170s** total, 18.3–64.0 (median 37.65, mean 38.96) per trial
- per-turn latency: 0.5–5.9 (median 2.2, mean 2.29)
- tokens: 1,543,220 prompt + 34,453 output (of which 0 thinking, 34,453 visible) = **1,577,673** (52,589/trial)

## Integrity

- invalid actions: 51
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 9 | 7.67× | +173 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 10 | 2.63× | +51 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 9 | 3.47× | +62 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 9 | 6.94× | +170 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 10 | 5.2× | +105 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 2 | 10.43× | +229 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 10 | 6.1× | +126 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 9 | 3.18× | +67 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 9 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 6.13× | +119 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 9 | 14.12× | +340 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 10 | 5.35× | +120 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 9.94× | +237 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 2.59× | +23 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.31× | +28 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 5.99× | +106 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.76× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 8 | 6.93× | +123 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 10 | 8.21× | +190 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 3.51× | +83 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 9 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 6 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 9 | 6.76× | +143 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 9.37× | +200 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 3 | 3.03× | +52 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 9 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 9 | 12.64× | +261 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 10 | 5.33× | +126 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 8.43× | +167 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 7.16× | +180 | `SCALE(P0, X, 0.715502)` |
