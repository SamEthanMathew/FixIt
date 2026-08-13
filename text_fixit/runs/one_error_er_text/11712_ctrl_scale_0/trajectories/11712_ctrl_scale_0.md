# 11712_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_1']
- ground-truth fix sequence: SCALE(P1, X, 0.704582)
- **terminal: PASS=True  score=0.995  deviation=0.1 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 6.2s

**action** `SCALE(P1, X, 0.704400)`

- PASS=True  score=0.9948  deviation=0.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.116 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 0.8s

**action** `SCALE(P1, X, 0.704400)`

- PASS=True  score=0.9948  deviation=0.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.116 | True | True |
