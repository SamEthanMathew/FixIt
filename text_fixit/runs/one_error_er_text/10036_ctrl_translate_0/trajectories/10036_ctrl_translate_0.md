# 10036_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_1']
- ground-truth fix sequence: TRANSLATE(P1, X, -0.19847)
- **terminal: PASS=False  score=0.001  deviation=198.5 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 18.7s

**action** `TRANSLATE(P1, Y, 0.10200)`

- PASS=False  score=0.0002  deviation=223.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 223.147 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 9.6s

**action** `TRANSLATE(P2, Y, -0.10200)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 30.5s

**action** `ROTATE(P2, X, 10.0000)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 4.6s

**action** `TRANSLATE(P2, Z, 0.10000)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 23.0s

**action** `ROTATE(P2, Y, -10.0000)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 44.4s

**action** `TRANSLATE(P2, X, -0.05000)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 35.3s

**action** `ROTATE(P2, Z, 10.0000)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 26.2s

**action** `SCALE(P2, Z, 0.550000)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 45.0s

**action** `TRANSLATE(P2, Z, 0.03300)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 36.8s

**action** `TRANSLATE(P1, X, 0.05000)`

- PASS=False  score=0.0001  deviation=248.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 248.47 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 1.2s

**action** `TRANSLATE(P2, Z, 0.03300)`

- PASS=False  score=0.0005  deviation=198.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 198.47 | False | True |
