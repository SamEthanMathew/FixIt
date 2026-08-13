# 11304_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_0']
- ground-truth fix sequence: ROTATE(P0, X, 29.4375)
- **terminal: PASS=True  score=0.891  deviation=2.5 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 5.8s

**action** `ROTATE(P0, X, 30.0000)`

- PASS=True  score=0.8907  deviation=2.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 2.47 | True | True |

![turn 1](images/11304_ctrl_rotate_0/t01_0.png)
![turn 1](images/11304_ctrl_rotate_0/t01_1.png)

## turn 2  (COMMIT)

- budget left: 9  ·  images sent: 2  ·  latency: 1.7s

**action** `ROTATE(P0, X, 30.0000)`

- PASS=True  score=0.8907  deviation=2.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 2.47 | True | True |

![turn 2](images/11304_ctrl_rotate_0/t02_0.png)
![turn 2](images/11304_ctrl_rotate_0/t02_1.png)
