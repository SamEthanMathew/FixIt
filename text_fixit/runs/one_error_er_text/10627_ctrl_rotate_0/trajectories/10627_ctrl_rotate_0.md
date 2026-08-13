# 10627_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): rotate  on ['link_2']
- ground-truth fix sequence: ROTATE(P2, Z, -43.8612)
- **terminal: PASS=False  score=0.000  deviation=387.1 mm  simulates=9**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 16.9s

**action** `TRANSLATE(P2, Y, 0.30000)`

- PASS=False  score=0.0  deviation=355.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 355.648 | False | True |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 4.9s

**action** `TRANSLATE(P2, Y, -0.30000)`

- PASS=False  score=0.0  deviation=329.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 329.299 | False | False |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 4.4s

**action** `TRANSLATE(P2, Y, 0.40000)`

- PASS=False  score=0.0  deviation=436.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 436.632 | False | True |

## turn 4  (SIMULATE)

- budget left: 7  ·  latency: 6.8s

**action** `TRANSLATE(P2, Y, 0.15000)`

- PASS=False  score=0.0  deviation=248.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 248.233 | False | False |

## turn 5  (SIMULATE)

- budget left: 6  ·  latency: 10.8s

**action** `TRANSLATE(P2, Y, 0.35000)`

- PASS=False  score=0.0  deviation=395.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 395.165 | False | True |

## turn 6  (SIMULATE)

- budget left: 5  ·  latency: 3.8s

**action** `TRANSLATE(P2, Y, 0.32000)`

- PASS=False  score=0.0  deviation=371.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 371.261 | False | True |

## turn 7  (SIMULATE)

- budget left: 4  ·  latency: 12.6s

**action** `TRANSLATE(P2, Y, 0.38000)`

- PASS=False  score=0.0  deviation=419.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 419.727 | False | True |

## turn 8  (SIMULATE)

- budget left: 3  ·  latency: 3.5s

**action** `TRANSLATE(P2, Y, 0.33000)`

- PASS=False  score=0.0  deviation=379.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 379.163 | False | True |

## turn 9  (SIMULATE)

- budget left: 2  ·  latency: 12.0s

**action** `TRANSLATE(P1, Y, -0.35000)`

- PASS=False  score=0.0  deviation=170.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 170.39 | False | True |

## turn 10  (COMMIT)

- budget left: 1  ·  latency: 19.6s

**action** `TRANSLATE(P2, Y, 0.34000)`

- PASS=False  score=0.0  deviation=387.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 387.131 | False | True |
