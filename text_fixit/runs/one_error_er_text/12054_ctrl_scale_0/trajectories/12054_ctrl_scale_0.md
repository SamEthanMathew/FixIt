# 12054_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_0']
- ground-truth fix sequence: SCALE(P0, X, 0.715502)
- **terminal: PASS=True  score=0.995  deviation=0.1 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 6.9s

**action** `SCALE(P0, X, 0.715300)`

- PASS=True  score=0.9949  deviation=0.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 0.148 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 0.9s

**action** `SCALE(P0, X, 0.715300)`

- PASS=True  score=0.9949  deviation=0.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 0.148 | True | True |
