# 12249_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, 0.17520)
- **terminal: PASS=True  score=0.915  deviation=2.2 mm  simulates=7**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 8.6s

**action** `TRANSLATE(P0, Z, 0.20000)`

- PASS=False  score=0.0  deviation=265.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 265.883 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 4.7s

**action** `TRANSLATE(P0, X, 0.20000)`

- PASS=False  score=0.3675  deviation=24.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 24.803 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 4.3s

**action** `TRANSLATE(P0, Y, -0.20000)`

- PASS=False  score=0.0  deviation=265.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 265.883 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 14.0s

**action** `TRANSLATE(P0, X, -0.20000)`

- PASS=False  score=0.0  deviation=375.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 375.197 | False | True |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 14.3s

**action** `TRANSLATE(P0, Y, -0.30000)`

- PASS=False  score=0.0  deviation=347.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 347.41 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 19.9s

**action** `TRANSLATE(P0, Z, 0.30000)`

- PASS=False  score=0.0  deviation=347.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 347.41 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 9.9s

**action** `TRANSLATE(P0, X, 0.17300)`

- PASS=True  score=0.9151  deviation=2.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 2.197 | True | True |

## turn 8  (COMMIT)

- budget left: 3  ·  latency: 0.8s

**action** `TRANSLATE(P0, X, 0.17300)`

- PASS=True  score=0.9151  deviation=2.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 2.197 | True | True |
