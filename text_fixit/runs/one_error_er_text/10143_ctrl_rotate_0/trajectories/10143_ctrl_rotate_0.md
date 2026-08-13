# 10143_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): rotate  on ['link_2']
- ground-truth fix sequence: ROTATE(P2, Z, -23.7176)
- **terminal: PASS=False  score=0.000  deviation=134.3 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 9.4s

**action** `TRANSLATE(P2, Z, 0.09000)`

- PASS=False  score=0.0006  deviation=108.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 108.269 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 2.5s

**action** `TRANSLATE(P2, Z, 0.14000)`

- PASS=False  score=0.0  deviation=153.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 153.603 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 8.3s

**action** `TRANSLATE(P2, Z, 0.12000)`

- PASS=False  score=0.0001  deviation=135.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 135.179 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 10.2s

**action** `TRANSLATE(P2, Z, 0.12100)`

- PASS=False  score=0.0001  deviation=136.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 136.093 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 4.5s

**action** `TRANSLATE(P2, Z, 0.11000)`

- PASS=False  score=0.0002  deviation=126.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 126.097 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 1.4s

**action** `TRANSLATE(P2, Z, 0.11500)`

- PASS=False  score=0.0001  deviation=130.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 130.626 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 1.9s

**action** `TRANSLATE(P2, Z, 0.11700)`

- PASS=False  score=0.0001  deviation=132.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 132.445 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 1.6s

**action** `TRANSLATE(P2, Z, 0.11800)`

- PASS=False  score=0.0001  deviation=133.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 133.355 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 2.4s

**action** `TRANSLATE(P2, Z, 0.11600)`

- PASS=False  score=0.0001  deviation=131.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 131.535 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 21.6s

**action** `TRANSLATE(P2, Z, 0.11900)`

- PASS=False  score=0.0001  deviation=134.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 134.267 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 1.1s

**action** `TRANSLATE(P2, Z, 0.11900)`

- PASS=False  score=0.0001  deviation=134.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 134.267 | False | True |
