# m8_easy_ablation

Easier single-fault rung (difficulty-scale 0.35, median D=1.6, tau 2.5%) x prompt ablation (metasyntax exemplars + explicit fault scale). Qwen3-VL-8B, batch, budget 10.

| condition | N | solved | success | tries all (min-max med/mean) | tries when solved | invalid | resets | API give-ups |
|---|---|---|---|---|---|---|---|---|
| qw_ablate_image | 30 | 6 | 20% | 2-10  med 10 / mean 7.8 | 2-4  med 2.5 / mean 2.67 | 20 | 0 | 0 |
| qw_ablate_text | 30 | 3 | 10% | 2-10  med 10 / mean 9.3 | 2-4  med 3 / mean 3 | 0 | 0 | 0 |
| qw_base_image | 30 | 5 | 17% | 2-10  med 10 / mean 9.03 | 2-10  med 6 / mean 6 | 13 | 0 | 0 |
| qw_base_text | 30 | 5 | 17% | 1-10  med 10 / mean 8.77 | 1-7  med 2 / mean 2.6 | 0 | 0 | 0 |

## Graded progress (informative when PASS floors at 0)

| condition | parts within tol | deviation closed | made worse | ever simulated a PASS |
|---|---|---|---|---|
| qw_ablate_image | 20% | -4% | 50% | 27% |
| qw_ablate_text | 10% | -65% | 70% | 13% |
| qw_base_image | 17% | -15% | 57% | 20% |
| qw_base_text | 17% | -36% | 60% | 17% |

## Tolerance sweep  (geometry only; closes/collides held at observed values, so these are UPPER bounds). 1.667x = the old 2.5% tolerance.

| condition | 1x (as run) | 1.667x | 2x | 3x |
|---|---|---|---|---|
| qw_ablate_image | 17% | 33% | 40% | 57% |
| qw_ablate_text | 10% | 10% | 10% | 20% |
| qw_base_image | 13% | 27% | 27% | 47% |
| qw_base_text | 17% | 27% | 30% | 37% |

## By fault type

**qw_ablate_image**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 1 | 10% | 2-10  med 10 / mean 9 | 2-2  med 2 / mean 2 |
| scale | 10 | 1 | 10% | 3-10  med 10 / mean 8.5 | 3-3  med 3 / mean 3 |
| translate | 10 | 4 | 40% | 2-10  med 6 / mean 5.9 | 2-4  med 2.5 / mean 2.75 |

**qw_ablate_text**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale | 10 | 1 | 10% | 3-10  med 10 / mean 9.3 | 3-3  med 3 / mean 3 |
| translate | 10 | 2 | 20% | 2-10  med 10 / mean 8.6 | 2-4  med 3 / mean 3 |

**qw_base_image**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 3 | 30% | 2-10  med 10 / mean 8.6 | 2-8  med 6 / mean 5.33 |
| scale | 10 | 0 | 0% | 9-10  med 10 / mean 9.7 | - |
| translate | 10 | 2 | 20% | 4-10  med 10 / mean 8.8 | 4-10  med 7 / mean 7 |

**qw_base_text**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 2 | 20% | 2-10  med 10 / mean 8.9 | 2-7  med 4.5 / mean 4.5 |
| scale | 10 | 1 | 10% | 2-10  med 10 / mean 9.2 | 2-2  med 2 / mean 2 |
| translate | 10 | 2 | 20% | 1-10  med 10 / mean 8.2 | 1-1  med 1 / mean 1 |

