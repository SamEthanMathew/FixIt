# 10489_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_2']
- ground-truth fix sequence: SCALE(P2, Y, 0.771644)
- **terminal: PASS=True  score=0.904  deviation=2.0 mm  simulates=8**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 19.7s

**action** `TRANSLATE(P2, Y, -0.12000)`

- PASS=False  score=0.0001  deviation=191.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 191.049 | False | False |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 17.8s

**action** `ROTATE(P2, Y, 20.0000)`

- PASS=False  score=0.0  deviation=295.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 295.354 | False | False |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 17.2s

**action** `TRANSLATE(P2, X, 0.21000)`

- PASS=False  score=0.0  deviation=362.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 362.87 | False | False |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 88.2s

**action** `ROTATE(P2, Y, 60.0000)`

- PASS=False  score=0.0  deviation=330.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 330.183 | False | False |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 20.4s

**action** `SCALE(P2, Y, 0.924000)`

- PASS=False  score=0.0001  deviation=188.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 188.355 | False | False |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 15.4s

**action** `SCALE(P2, Y, 0.798000)`

- PASS=False  score=0.1988  deviation=32.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 32.583 | False | False |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 22.1s

**action** `SCALE(P2, Y, 0.750000)`

- PASS=False  score=0.2654  deviation=26.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 26.758 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 6.6s

**action** `SCALE(P2, Y, 0.770000)`

- PASS=True  score=0.9041  deviation=2.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 2.033 | True | True |

## turn 9  (COMMIT)

- budget left: 2  ·  latency: 0.8s

**action** `SCALE(P2, Y, 0.770000)`

- PASS=True  score=0.9041  deviation=2.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 2.033 | True | True |
