# 12250_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_1']
- ground-truth fix sequence: SCALE(P1, Y, 0.733483)
- **terminal: PASS=True  score=0.998  deviation=0.1 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 3.0s

**action** `SCALE(P1, Y, 0.733570)`

- PASS=True  score=0.9979  deviation=0.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.062 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 1.0s

**action** `SCALE(P1, Y, 0.733570)`

- PASS=True  score=0.9979  deviation=0.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.062 | True | True |
