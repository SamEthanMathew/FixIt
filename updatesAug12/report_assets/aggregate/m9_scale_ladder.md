# m9_scale_ladder

Scale ladder, like-for-like: Qwen3-VL-8B vs 32B-FP8, BOTH under history=window3 (history=full makes the 32B drift into prose and fail to emit <act> tags -- 58% invalid). Rungs: the M8 easy set (median D=1.6) and M7 easy baseline (er 57% / g3 49%).

| condition | N | solved | success | tries all (min-max med/mean) | tries when solved | invalid | resets | API give-ups |
|---|---|---|---|---|---|---|---|---|
| qw32_easy_image | 30 | 7 | 23% | 1-10  med 10 / mean 8.17 | 1-7  med 2 / mean 2.43 | 0 | 0 | 1 |
| qw32_easy_text | 30 | 5 | 17% | 2-10  med 10 / mean 9.23 | 2-10  med 4 / mean 5.4 | 10 | 0 | 0 |
| qw32_m7easy_image | 75 | 6 | 8% | 1-10  med 10 / mean 9.33 | 1-4  med 1 / mean 1.67 | 0 | 0 | 0 |
| qw8_easy_image | 30 | 5 | 17% | 1-10  med 10 / mean 9.13 | 1-9  med 6 / mean 4.8 | 0 | 0 | 0 |
| qw8_easy_text | 30 | 4 | 13% | 1-10  med 10 / mean 9.2 | 1-7  med 4 / mean 4 | 5 | 0 | 0 |
| qw8_m7easy_image | 75 | 1 | 1% | 5-10  med 10 / mean 9.93 | 5-5  med 5 / mean 5 | 0 | 0 | 0 |

## Graded progress (informative when PASS floors at 0)

| condition | parts within tol | deviation closed | made worse | ever simulated a PASS |
|---|---|---|---|---|
| qw32_easy_image | 23% | -1% | 50% | 23% |
| qw32_easy_text | 17% | -43% | 60% | 17% |
| qw32_m7easy_image | 8% | 1% | 51% | 8% |
| qw8_easy_image | 17% | -26% | 53% | 17% |
| qw8_easy_text | 13% | -36% | 57% | 20% |
| qw8_m7easy_image | 1% | -25% | 56% | 1% |

## Tolerance sweep  (geometry only; closes/collides held at observed values, so these are UPPER bounds). 1.667x = the old 2.5% tolerance.

| condition | 1x (as run) | 1.667x | 2x | 3x |
|---|---|---|---|---|
| qw32_easy_image | 23% | 33% | 37% | 67% |
| qw32_easy_text | 13% | 20% | 27% | 33% |
| qw32_m7easy_image | 8% | 9% | 9% | 12% |
| qw8_easy_image | 17% | 20% | 20% | 37% |
| qw8_easy_text | 13% | 13% | 17% | 33% |
| qw8_m7easy_image | 1% | 1% | 1% | 3% |

## By fault type

**qw32_easy_image**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 2 | 20% | 2-10  med 10 / mean 8.4 | 2-2  med 2 / mean 2 |
| scale | 10 | 4 | 40% | 1-10  med 10 / mean 7.2 | 1-7  med 2 / mean 3 |
| translate | 10 | 1 | 10% | 1-10  med 10 / mean 8.9 | 1-1  med 1 / mean 1 |

**qw32_easy_text**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 1 | 10% | 9-10  med 10 / mean 9.9 | 9-9  med 9 / mean 9 |
| scale | 10 | 2 | 20% | 2-10  med 10 / mean 8.6 | 2-4  med 3 / mean 3 |
| translate | 10 | 2 | 20% | 2-10  med 10 / mean 9.2 | 2-10  med 6 / mean 6 |

**qw32_m7easy_image**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale | 25 | 6 | 24% | 1-10  med 10 / mean 8 | 1-4  med 1 / mean 1.67 |
| translate | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - |

**qw8_easy_image**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 2 | 20% | 7-10  med 10 / mean 9.6 | 7-9  med 8 / mean 8 |
| scale | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| translate | 10 | 3 | 30% | 1-10  med 10 / mean 7.8 | 1-6  med 1 / mean 2.67 |

**qw8_easy_text**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 10 | 2 | 20% | 7-10  med 10 / mean 9.4 | 7-7  med 7 / mean 7 |
| scale | 10 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| translate | 10 | 2 | 20% | 1-10  med 10 / mean 8.2 | 1-1  med 1 / mean 1 |

**qw8_m7easy_image**

| group | N | solved | success | tries all | tries when solved |
|---|---|---|---|---|---|
| rotate | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| scale | 25 | 0 | 0% | 10-10  med 10 / mean 10 | - |
| translate | 25 | 1 | 4% | 5-10  med 10 / mean 9.8 | 5-5  med 5 / mean 5 |

