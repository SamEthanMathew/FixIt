# 10373_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): rotate  on ['link_0']
- ground-truth fix sequence: ROTATE(P0, Y, -35.2125)
- **terminal: PASS=False  score=0.298  deviation=25.2 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 4.3s

**action** `ROTATE(P0, X, 30.0000)`

- PASS=False  score=0.0  deviation=357.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 357.083 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 3.4s

**action** `ROTATE(P0, Y, 30.0000)`

- PASS=False  score=0.0  deviation=298.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 298.387 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 2.7s

**action** `ROTATE(P0, Z, 30.0000)`

- PASS=False  score=0.0  deviation=371.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 371.128 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 5.8s

**action** `ROTATE(P0, Z, -30.0000)`

- PASS=False  score=0.0  deviation=388.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 388.212 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 3.8s

**action** `ROTATE(P0, Y, -45.0000)`

- PASS=False  score=0.1034  deviation=47.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 47.238 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 5.2s

**action** `ROTATE(P0, Y, -60.0000)`

- PASS=False  score=0.0033  deviation=118.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 118.847 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 3.2s

**action** `TRANSLATE(P0, X, 0.10000)`

- PASS=False  score=0.0001  deviation=195.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 195.2 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 6.3s

**action** `ROTATE(P0, X, -30.0000)`

- PASS=False  score=0.0  deviation=295.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 295.23 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 15.7s

**action** `ROTATE(P0, Y, 45.0000)`

- PASS=False  score=0.0  deviation=356.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 356.72 | False | True |

## turn 10  (SIMULATE)

- budget left: 1  ·  latency: 52.7s

**action** `ROTATE(P0, Y, -30.0000)`

- PASS=False  score=0.2983  deviation=25.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 25.18 | False | True |

## turn 11  (COMMIT)

- budget left: 0  ·  latency: 13.8s

**action** `ROTATE(P0, Y, -30.0000)`

- PASS=False  score=0.2983  deviation=25.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 25.18 | False | True |
