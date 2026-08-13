# 12055_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, -0.08777)
- **terminal: PASS=False  score=0.000  deviation=409.5 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 7.4s

**action** `TRANSLATE(P0, X, 0.20000)`

- PASS=False  score=0.0  deviation=287.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 287.768 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 4.3s

**action** `TRANSLATE(P0, Y, 0.20000)`

- PASS=False  score=0.0004  deviation=218.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 218.411 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 4.4s

**action** `TRANSLATE(P0, Z, 0.20000)`

- PASS=False  score=0.0004  deviation=218.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 218.411 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 19.3s

**action** `TRANSLATE(P0, Y, -0.40000)`

- PASS=False  score=0.0  deviation=409.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 409.516 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 22.6s

**action** `TRANSLATE(P0, Y, -0.30000)`

- PASS=False  score=0.0  deviation=312.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 312.575 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 14.3s

**action** `TRANSLATE(P0, Y, 0.40000)`

- PASS=False  score=0.0  deviation=409.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 409.516 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 33.1s

**action** `TRANSLATE(P0, Y, -0.37000)`

- PASS=False  score=0.0  deviation=380.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 380.267 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 9.8s

**action** `ROTATE(P0, Z, 10.0000)`

- PASS=False  score=0.0199  deviation=108.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 108.5 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 8.7s

**action** `TRANSLATE(P0, Y, -0.38000)`

- PASS=False  score=0.0  deviation=390.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 390.004 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 11.9s

**action** `TRANSLATE(P0, Y, -0.40000)`

- PASS=False  score=0.0  deviation=409.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 409.516 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 1.7s

**action** `TRANSLATE(P0, Y, -0.40000)`

- PASS=False  score=0.0  deviation=409.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 409.516 | False | True |
