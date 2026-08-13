# 11299_ctrl_translate_0  (control_single)

- agent: `loop_qwen_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_1']
- ground-truth fix sequence: TRANSLATE(P1, X, -0.12826)
- **terminal: PASS=False  score=0.005  deviation=129.3 mm  simulates=8**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 1.4s

**action** `TRANSLATE(P1, Y, -0.05000)`

- PASS=False  score=0.0038  deviation=137.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 137.659 | False | False |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 1.0s

**action** `TRANSLATE(P1, Z, -0.03000)`

- PASS=False  score=0.0049  deviation=131.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 131.72 | False | False |

## turn 3  (invalid)

- budget left: 8  ·  latency: 0.3s

**action** `TRANSLATE(P1, Z, -0.03000)`

- INVALID: missing SIMULATE or COMMIT

## turn 4  (SIMULATE)

- budget left: 8  ·  latency: 1.0s

**action** `ROTATE(P1, X, -10.0000)`

- PASS=False  score=0.0005  deviation=187.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 187.392 | False | False |

## turn 5  (invalid)

- budget left: 7  ·  latency: 0.4s

**action** `ROTATE(P1, X, -10.0000)`

- INVALID: missing SIMULATE or COMMIT

## turn 6  (SIMULATE)

- budget left: 7  ·  latency: 1.4s

**action** `TRANSLATE(P1, Y, 0.03000)`

- PASS=False  score=0.0049  deviation=131.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 131.72 | False | False |

## turn 7  (invalid)

- budget left: 6  ·  latency: 0.3s

**action** `TRANSLATE(P1, Y, 0.03000)`

- INVALID: missing SIMULATE or COMMIT

## turn 8  (SIMULATE)

- budget left: 6  ·  latency: 1.0s

**action** `ROTATE(P1, Z, -5.0000)`

- PASS=False  score=0.0053  deviation=129.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 129.665 | False | False |

## turn 9  (invalid)

- budget left: 5  ·  latency: 0.4s

**action** `ROTATE(P1, Z, -5.0000)`

- INVALID: missing SIMULATE or COMMIT

## turn 10  (SIMULATE)

- budget left: 5  ·  latency: 1.4s

**action** `TRANSLATE(P1, X, 0.02000)`

- PASS=False  score=0.0025  deviation=148.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 148.258 | False | False |

## turn 11  (invalid)

- budget left: 4  ·  latency: 0.3s

**action** `TRANSLATE(P1, X, 0.02000)`

- INVALID: missing SIMULATE or COMMIT

## turn 12  (SIMULATE)

- budget left: 4  ·  latency: 1.5s

**action** `SCALE(P1, Y, 0.710000)`

- PASS=False  score=0.0  deviation=334.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 334.431 | False | False |

## turn 13  (invalid)

- budget left: 3  ·  latency: 0.3s

**action** `SCALE(P1, Y, 0.710000)`

- INVALID: missing SIMULATE or COMMIT

## turn 14  (SIMULATE)

- budget left: 3  ·  latency: 1.5s

**action** `ROTATE(P1, Y, 5.0000)`

- PASS=False  score=0.0054  deviation=129.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 129.345 | False | False |

## turn 15  (invalid)

- budget left: 2  ·  latency: 0.4s

**action** `ROTATE(P1, Y, 5.0000)`

- INVALID: missing SIMULATE or COMMIT
