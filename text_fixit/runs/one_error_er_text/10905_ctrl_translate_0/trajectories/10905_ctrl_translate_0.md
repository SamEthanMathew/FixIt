# 10905_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, Z, 0.17837)
- **terminal: PASS=False  score=0.000  deviation=178.4 mm  simulates=8**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 3.5s

**action** `TRANSLATE(P0, X, 0.10000)`

- PASS=False  score=0.0  deviation=204.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 204.491 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 6.6s

**action** `TRANSLATE(P0, Y, 0.10000)`

- PASS=False  score=0.0  deviation=204.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 204.491 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 3.0s

**action** `TRANSLATE(P0, Z, 0.10000)`

- PASS=False  score=0.0109  deviation=78.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 78.372 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 4.7s

**action** `TRANSLATE(P0, Y, 0.27000)`

- PASS=False  score=0.0  deviation=323.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 323.599 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 15.5s

**action** `TRANSLATE(P0, Y, 0.40000)`

- PASS=False  score=0.0  deviation=438.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 437.968 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 13.3s

**action** `TRANSLATE(P0, Y, 0.27100)`

- PASS=False  score=0.0  deviation=324.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 324.434 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 10.6s

**action** `TRANSLATE(P0, Y, 0.25200)`

- PASS=False  score=0.0  deviation=308.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 308.74 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 12.5s

**action** `TRANSLATE(P0, Y, 0.28200)`

- PASS=False  score=0.0  deviation=333.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 333.677 | False | True |

## turn 9  (COMMIT)

- budget left: 2  ·  latency: 68.0s

**reasoning**

> api error: None

**action** `NO_FIX()`

- PASS=False  score=0.0  deviation=178.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 178.372 | False | True |
