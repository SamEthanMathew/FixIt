# 11304_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): rotate  on ['link_0']
- ground-truth fix sequence: ROTATE(P0, X, 29.4375)
- **terminal: PASS=False  score=0.003  deviation=127.8 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 23.0s

**action** `TRANSLATE(P1, X, -0.21700)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 27.8s

**action** `ROTATE(P1, Y, 15.0000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 49.3s

**action** `TRANSLATE(P1, X, -0.24000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 29.4s

**action** `SCALE(P1, X, 1.350000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 12.1s

**action** `TRANSLATE(P1, Z, 0.05000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 17.9s

**action** `TRANSLATE(P1, Y, -0.12800)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | False |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 6.9s

**action** `TRANSLATE(P1, Y, -0.05000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | False |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 47.6s

**action** `TRANSLATE(P1, Z, -0.05000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 20.8s

**action** `TRANSLATE(P1, Y, -0.11000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | False |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 22.2s

**action** `SCALE(P1, X, 1.580000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 17.0s

**action** `TRANSLATE(P1, Z, -0.05000)`

- PASS=False  score=0.0025  deviation=127.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 127.82 | False | True |
