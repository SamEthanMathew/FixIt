# 11231_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_1']
- ground-truth fix sequence: TRANSLATE(P1, X, 0.18806)
- **terminal: PASS=False  score=0.000  deviation=188.1 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 8.7s

**action** `TRANSLATE(P2, Y, 0.32000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 49.0s

**action** `TRANSLATE(P1, Y, -0.32000)`

- PASS=False  score=0.0  deviation=371.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 371.171 | False | False |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 58.8s

**action** `TRANSLATE(P2, X, 0.08000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 52.7s

**action** `TRANSLATE(P2, X, -0.08000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 44.1s

**action** `TRANSLATE(P2, Z, 0.10000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 52.8s

**action** `ROTATE(P2, Y, 45.0000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 46.9s

**action** `TRANSLATE(P2, Y, 0.38000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 14.3s

**action** `SCALE(P2, X, 1.077000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | False |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 6.7s

**action** `TRANSLATE(P2, Z, -0.10000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 24.3s

**action** `TRANSLATE(P2, Z, -0.08000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 2.4s

**action** `TRANSLATE(P2, Z, -0.09000)`

- PASS=False  score=0.0003  deviation=188.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 188.064 | False | True |
