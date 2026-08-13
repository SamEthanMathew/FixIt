# one_error_scale_qw8_text

**0/30 solved (0%)** — 30 distinct problems, one attempt each.

| | |
|---|---|
| model | `Qwen/Qwen3-VL-8B-Instruct` |
| prompt set | `one_error_scale` |
| agent / modality | `loop_qwen_full` · text |
| contract | batch, max 1 action(s)/turn, budget 10 |
| problems | 30 from `data/instances_std30.jsonl` |
| mean difficulty | **7.62× tolerance** at start |
| tolerance | τ = 1.5% of each part's size |

## By fault type

| type | solved | mean closest (× tolerance) |
|---|---|---|
| rotate | 0/10 | 7.42× |
| scale | 0/10 | 7.52× |
| translate | 0/10 | 5.46× |

## Outcome

- iterations when **solved**: —
- iterations when **failed**: 0–10 (median 9.5, mean 6.83)
- problems that ever got under threshold: **0/30**
- closest approach (× tolerance): best **1.68×**, median 6.65×, mean 6.8×

## Convergence — best distance from threshold by turn N (1.0× = passing)

| turn | mean best (× tol) | best single (× tol) | problems under threshold |
|---|---|---|---|
| 1 | 8.22× | 3.03× | 0/30 |
| 2 | 7.5× | 3.03× | 0/22 |
| 3 | 7.34× | 3.03× | 0/22 |
| 4 | 7.2× | 3.03× | 0/22 |
| 5 | 6.96× | 3.03× | 0/21 |
| 6 | 6.84× | 3.03× | 0/21 |
| 7 | 6.25× | 1.68× | 0/21 |
| 8 | 6.24× | 1.68× | 0/21 |
| 9 | 6.23× | 1.68× | 0/21 |
| 10 | 6.31× | 1.68× | 0/19 |
| 11 | 6.1× | 1.68× | 0/15 |

## Cost

- wall clock: **1325s** total, 24.9–67.6 (median 43.35, mean 44.13) per trial
- per-turn latency: 0.3–3.3 (median 1.8, mean 1.85)
- tokens: 1,783,175 prompt + 33,402 output (of which 0 thinking, 33,402 visible) = **1,816,577** (60,553/trial)

## Integrity

- invalid actions: 172
- trials hit by an API give-up: 0
- images sent per turn: [0]

## Per problem

| problem | type | outcome | iters | closest (× tol) | final over tol (mm) | ground truth |
|---|---|---|---|---|---|---|
| `10036_ctrl_translate_0` | translate | fail | 10 | 7.67× | +223 | `TRANSLATE(P1, X, -0.19847)` |
| `11178_ctrl_translate_0` | translate | fail | 8 | 4.25× | +81 | `TRANSLATE(P1, Y, -0.14547)` |
| `10849_ctrl_translate_0` | translate | fail | 9 | 3.63× | +156 | `TRANSLATE(P0, X, -0.08517)` |
| `11231_ctrl_translate_0` | translate | fail | 10 | 5.14× | +94 | `TRANSLATE(P1, X, 0.18806)` |
| `11299_ctrl_translate_0` | translate | fail | 8 | 5.23× | +105 | `TRANSLATE(P1, X, -0.12826)` |
| `10905_ctrl_translate_0` | translate | fail | 10 | 9.13× | +171 | `TRANSLATE(P0, Z, 0.17837)` |
| `12249_ctrl_translate_0` | translate | fail | 0 | 7.07× | +150 | `TRANSLATE(P0, X, 0.17520)` |
| `12055_ctrl_translate_0` | translate | fail | 0 | 3.17× | +60 | `TRANSLATE(P0, X, -0.08777)` |
| `10620_ctrl_translate_0` | translate | fail | 10 | 3.18× | +56 | `TRANSLATE(P2, X, 0.08216)` |
| `10586_ctrl_translate_0` | translate | fail | 10 | 6.13× | +119 | `TRANSLATE(P2, Y, -0.14191)` |
| `10655_ctrl_rotate_0` | rotate | fail | 0 | 14.14× | +338 | `ROTATE(P1, X, -26.7650)` |
| `10797_ctrl_rotate_0` | rotate | fail | 10 | 5.79× | +159 | `ROTATE(P1, X, 22.8324)` |
| `12252_ctrl_rotate_0` | rotate | fail | 0 | 10.02× | +235 | `ROTATE(P0, Z, -23.2817)` |
| `10143_ctrl_rotate_0` | rotate | fail | 10 | 2.45× | +87 | `ROTATE(P2, Z, -23.7176)` |
| `12050_ctrl_rotate_0` | rotate | fail | 9 | 3.95× | +35 | `ROTATE(P0, X, -23.0027)` |
| `11304_ctrl_rotate_0` | rotate | fail | 10 | 5.99× | +106 | `ROTATE(P0, X, 29.4375)` |
| `10627_ctrl_rotate_0` | rotate | fail | 10 | 11.76× | +156 | `ROTATE(P2, Z, -43.8612)` |
| `10373_ctrl_rotate_0` | rotate | fail | 10 | 8.34× | +185 | `ROTATE(P0, Y, -35.2125)` |
| `11211_ctrl_rotate_0` | rotate | fail | 10 | 8.21× | +225 | `ROTATE(P0, Z, 22.5051)` |
| `12042_ctrl_rotate_0` | rotate | fail | 10 | 3.6× | +157 | `ROTATE(P1, Z, -38.0044)` |
| `10489_ctrl_scale_0` | scale | fail | 9 | 14.0× | +262 | `SCALE(P2, Y, 0.771644)` |
| `12248_ctrl_scale_0` | scale | fail | 3 | 11.52× | +146 | `SCALE(P0, Y, 0.648390)` |
| `10612_ctrl_scale_0` | scale | fail | 9 | 6.76× | +143 | `SCALE(P2, Y, 0.771633)` |
| `10944_ctrl_scale_0` | scale | fail | 10 | 9.42× | +201 | `SCALE(P0, Y, 0.709604)` |
| `10685_ctrl_scale_0` | scale | fail | 10 | 3.03× | +52 | `SCALE(P2, X, 0.690325)` |
| `10867_ctrl_scale_0` | scale | fail | 0 | 6.73× | +138 | `SCALE(P0, X, 0.724298)` |
| `10638_ctrl_scale_0` | scale | fail | 10 | 1.68× | +311 | `SCALE(P1, X, 0.739679)` |
| `12250_ctrl_scale_0` | scale | fail | 0 | 6.57× | +162 | `SCALE(P1, Y, 0.733483)` |
| `11712_ctrl_scale_0` | scale | fail | 0 | 8.39× | +167 | `SCALE(P1, X, 0.704582)` |
| `12054_ctrl_scale_0` | scale | fail | 0 | 7.14× | +179 | `SCALE(P0, X, 0.715502)` |
