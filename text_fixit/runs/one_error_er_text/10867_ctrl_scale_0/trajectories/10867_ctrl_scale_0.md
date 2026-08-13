# 10867_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_0']
- ground-truth fix sequence: SCALE(P0, X, 0.724298)
- **terminal: PASS=False  score=0.001  deviation=162.0 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 4.0s

**action** `TRANSLATE(P2, X, 0.04500)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | False |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 3.1s

**action** `TRANSLATE(P2, Y, -0.05000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | False |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 3.9s

**action** `TRANSLATE(P2, Z, 0.05000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | False |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 9.4s

**action** `TRANSLATE(P2, Z, -0.10000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 5.1s

**action** `TRANSLATE(P2, Z, -0.07000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 1.5s

**action** `TRANSLATE(P2, Z, -0.11000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 2.9s

**action** `TRANSLATE(P2, Z, -0.09000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 1.8s

**action** `TRANSLATE(P2, Z, -0.08000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 1.4s

**action** `TRANSLATE(P2, Z, -0.08500)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 1.4s

**action** `TRANSLATE(P2, Z, -0.08800)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 1.6s

**action** `TRANSLATE(P2, Z, -0.09000)`

- PASS=False  score=0.0012  deviation=162.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 161.996 | False | True |
