# 12050_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): rotate  on ['link_0']
- ground-truth fix sequence: ROTATE(P0, X, -23.0027)
- **terminal: PASS=False  score=0.022  deviation=45.3 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 47.6s

**action** `TRANSLATE(P2, X, -0.07400)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 22.2s

**action** `TRANSLATE(P2, X, 0.07400)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 13.1s

**action** `TRANSLATE(P0, X, -0.07400)`

- PASS=False  score=0.0005  deviation=90.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 90.327 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 55.8s

**action** `ROTATE(P0, Y, 10.0000)`

- PASS=False  score=0.0104  deviation=54.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 54.466 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 55.6s

**action** `TRANSLATE(P2, Y, 0.05000)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | False |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 31.9s

**action** `TRANSLATE(P2, Y, 0.03800)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | False |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 29.7s

**action** `SCALE(P0, Z, 0.550000)`

- PASS=False  score=0.0007  deviation=87.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 87.159 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 18.2s

**action** `ROTATE(P2, Z, 10.0000)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | False |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 20.1s

**action** `TRANSLATE(P2, Y, -0.05000)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 6.3s

**action** `TRANSLATE(P2, Y, -0.07400)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 2.9s

**action** `TRANSLATE(P2, Y, -0.07200)`

- PASS=False  score=0.0225  deviation=45.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.289 | False | True |
