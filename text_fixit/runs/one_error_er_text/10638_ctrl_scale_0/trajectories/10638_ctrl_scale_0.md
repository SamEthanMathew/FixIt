# 10638_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_1']
- ground-truth fix sequence: SCALE(P1, X, 0.739679)
- **terminal: PASS=True  score=0.979  deviation=0.5 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 6.7s

**action** `SCALE(P1, X, 0.739300)`

- PASS=True  score=0.9788  deviation=0.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.482 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 0.7s

**action** `SCALE(P1, X, 0.739300)`

- PASS=True  score=0.9788  deviation=0.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.482 | True | True |
