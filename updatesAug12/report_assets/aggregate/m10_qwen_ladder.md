# m10_qwen_ladder

Qwen difficulty ladder, complete grid: 8B vs 32B-FP8 on every existing rung, all window3 + batch + image + budget 10. Rungs: easy (D~1.6) / M7 baseline (D~4.6) / hardened control (tau 1.5%) / n=2 composite / n=3 composite.

| condition | N | solved | success | tries all (min-max med/mean) | tries when solved | invalid | resets | API give-ups |
|---|---|---|---|---|---|---|---|---|
| qw32_2fault | 30 | 0 | 0% | 10-10  med 10 / mean 10 | - | 0 | 0 | 0 |
| qw32_composite | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - | 0 | 0 | 0 |
| qw32_ctrl | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - | 0 | 0 | 0 |
| qw8_2fault | 30 | 0 | 0% | 10-10  med 10 / mean 10 | - | 0 | 0 | 0 |
| qw8_composite | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - | 0 | 0 | 0 |
| qw8_ctrl | 25 | 1 | 4% | 5-10  med 10 / mean 9.8 | 5-5  med 5 / mean 5 | 0 | 0 | 0 |

## Graded progress (informative when PASS floors at 0)

| condition | parts within tol | deviation closed | made worse | ever simulated a PASS |
|---|---|---|---|---|
| qw32_2fault | 2% | -5% | 63% | 0% |
| qw32_composite | 0% | 6% | 36% | 0% |
| qw32_ctrl | 0% | -12% | 60% | 0% |
| qw8_2fault | 0% | -21% | 60% | 0% |
| qw8_composite | 0% | -21% | 60% | 0% |
| qw8_ctrl | 4% | -48% | 60% | 4% |

## Tolerance sweep  (geometry only; closes/collides held at observed values, so these are UPPER bounds). 1.667x = the old 2.5% tolerance.

| condition | 1x (as run) | 1.667x | 2x | 3x |
|---|---|---|---|---|
| qw32_2fault | 0% | 0% | 0% | 0% |
| qw32_composite | 0% | 0% | 0% | 0% |
| qw32_ctrl | 0% | 4% | 4% | 24% |
| qw8_2fault | 0% | 0% | 0% | 0% |
| qw8_composite | 0% | 0% | 0% | 0% |
| qw8_ctrl | 4% | 4% | 4% | 20% |

## By fault type

**qw32_2fault**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| composite | 30 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw32_composite**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| composite | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw32_ctrl**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 8 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale | 8 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| translate | 9 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_2fault**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| composite | 30 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_composite**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| composite | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_ctrl**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 8 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale | 8 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| translate | 9 | 1 | 11% | 5-10  med 10 / mean 9.44 | 5-5  med 5 / mean 5 |


## By difficulty level

**qw32_2fault**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| 2fault_1door | 15 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| 2fault_2door | 15 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw32_composite**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| composite_1door | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| composite_2door | 15 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_2fault**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| 2fault_1door | 15 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| 2fault_2door | 15 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_composite**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| composite_1door | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| composite_2door | 15 | 0 | 0% | 10-10  med 10 / mean 10 | - |


## By fault-type pair

**qw32_2fault**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate+scale | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| rotate+translate | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale+translate | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_2fault**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate+scale | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| rotate+translate | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale+translate | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |

