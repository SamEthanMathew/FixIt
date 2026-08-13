# 10849_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, -0.08517)
- **terminal: PASS=False  score=0.000  deviation=227.5 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 7.6s

**action** `TRANSLATE(P0, X, 0.10000)`

- PASS=False  score=0.0006  deviation=185.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 185.17 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 37.8s

**action** `TRANSLATE(P0, Y, -0.35000)`

- PASS=False  score=0.0  deviation=360.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 360.214 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 12.2s

**action** `TRANSLATE(P0, Z, 0.20000)`

- PASS=False  score=0.0002  deviation=217.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 217.38 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 18.0s

**action** `TRANSLATE(P0, Z, -0.10000)`

- PASS=False  score=0.0053  deviation=131.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 131.354 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 30.6s

**action** `TRANSLATE(P0, X, 0.20200)`

- PASS=False  score=0.0  deviation=287.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 287.17 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 12.1s

**action** `TRANSLATE(P0, Y, -0.40000)`

- PASS=False  score=0.0  deviation=409.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 408.967 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 18.0s

**action** `TRANSLATE(P0, Y, -0.21100)`

- PASS=False  score=0.0001  deviation=227.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 227.541 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 21.9s

**action** `TRANSLATE(P0, X, 0.20400)`

- PASS=False  score=0.0  deviation=289.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 289.17 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 32.2s

**action** `TRANSLATE(P0, X, 0.40000)`

- PASS=False  score=0.0  deviation=485.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 485.17 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 84.9s

**action** `TRANSLATE(P0, Y, -0.40000)`

- PASS=False  score=0.0  deviation=409.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 408.967 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 2.2s

**action** `TRANSLATE(P0, Y, -0.21100)`

- PASS=False  score=0.0001  deviation=227.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 227.541 | False | True |
