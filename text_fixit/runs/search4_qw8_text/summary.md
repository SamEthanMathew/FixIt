# search4_qw8_text

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
| rotate | 2/10 | 5.81× |
| scale | 1/10 | 6.22× |
| translate | 3/10 | 3.69× |

## Outcome

- iterations when **solved**: 1–8 (median 3.5, mean 4)
- iterations when **failed**: 10–10 (median 10, mean 10)
- problems that ever got under threshold: **6/30**
- closest approach (× tolerance): best **0.01×**, median 4.38×, mean 5.24×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 9.37× | 0.01× | 2/30 |
| 2 | 7.86× | 0.01× | 2/30 |
| 3 | 7.56× | 0.69× | 1/28 |
| 4 | 7.18× | 0.69× | 2/28 |
| 5 | 7.13× | 0.7× | 1/27 |
| 6 | 7.07× | 1.31× | 0/26 |
| 7 | 6.66× | 0.96× | 1/26 |
| 8 | 6.54× | 0.81× | 2/26 |
| 9 | 6.43× | 0.81× | 1/25 |
| 10 | 6.42× | 1.31× | 0/24 |
| 11 | 6.42× | 1.31× | 0/24 |

## Cost

- wall clock: **517s** total, 3.1–24.2 (median 18.75, mean 17.2) per trial
- per-turn latency: 0.9–4.0 (median 1.5, mean 1.64)
- tokens: 778,177 prompt + 18,081 output (of which 0 thinking, 18,081 visible) = **796,258** (26,542/trial)

## Integrity

- invalid actions: 0
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | **PASS** | 1 | 0.02× | -25 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 10 | 2.94× | +48 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | **PASS** | 8 | 0.81× | -5 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 7.72× | +153 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | **PASS** | 1 | 0.01× | -24 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 10.28× | +172 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 10 | 7.07× | +150 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 10 | 1.31× | +9 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 3.54× | +59 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 10 | 14.11× | +489 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | **PASS** | 4 | 0.7× | -8 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 10 | 10.02× | +235 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 3.27× | +33 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 10 | 3.72× | +32 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 1.94× | +20 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.35× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 7.97× | +171 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | **PASS** | 7 | 0.96× | -1 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 4.12× | +91 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 10 | 4.8× | +77 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 10 | 9.88× | +123 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 10 | 3.8× | +70 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 9.37× | +200 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | **PASS** | 3 | 0.69× | -8 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 10 | 5.51× | +109 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 9.08× | +181 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 10 | 6.07× | +162 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 10 | 8.39× | +167 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 10 | 4.63× | +106 | `SCALE(P0, X, 0.715502)` |
