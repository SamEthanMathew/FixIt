# 11299_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_1']
- ground-truth fix sequence: TRANSLATE(P1, X, -0.12826)
- **terminal: PASS=True  score=0.634  deviation=11.3 mm  simulates=3**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 19.4s

**action** `TRANSLATE(P1, X, -0.08000)`

- PASS=False  score=0.1421  deviation=48.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 48.258 | False | False |

## turn 2  (SIMULATE)

- budget left: 9  ·  latency: 5.0s

**action** `TRANSLATE(P1, X, -0.25000)`

- PASS=False  score=0.0073  deviation=121.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 121.742 | False | True |

## turn 3  (SIMULATE)

- budget left: 8  ·  latency: 11.3s

**action** `TRANSLATE(P1, X, -0.11700)`

- PASS=True  score=0.6343  deviation=11.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 11.258 | True | True |

## turn 4  (COMMIT)

- budget left: 7  ·  latency: 0.9s

**action** `TRANSLATE(P1, X, -0.11700)`

- PASS=True  score=0.6343  deviation=11.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 11.258 | True | True |
