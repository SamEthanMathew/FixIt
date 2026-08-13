# 11211_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_0']
- ground-truth fix sequence: ROTATE(P0, Z, 22.5051)
- **terminal: PASS=True  score=0.384  deviation=24.1 mm  simulates=2**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 6.4s

**action** `ROTATE(P0, Z, 30.0000)`

- PASS=False  score=0.0565  deviation=72.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 72.431 | False | True |

![turn 1](images/11211_ctrl_rotate_0/t01_0.png)
![turn 1](images/11211_ctrl_rotate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 4.7s

**action** `ROTATE(P0, Z, 25.0000)`

- PASS=True  score=0.384  deviation=24.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 24.126 | True | True |

![turn 2](images/11211_ctrl_rotate_0/t02_0.png)
![turn 2](images/11211_ctrl_rotate_0/t02_1.png)

## turn 3  (COMMIT)

- budget left: 8  ·  images sent: 2  ·  latency: 2.8s

**reasoning**

> The simulation with ROTATE(P0, Z, 25) returned ALL PASS, which means the door is correctly restored to its pose, closes flush without interpenetration, and meets all criteria. I will commit this action.

**action** `ROTATE(P0, Z, 25.0000)`

- PASS=True  score=0.384  deviation=24.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 24.126 | True | True |

![turn 3](images/11211_ctrl_rotate_0/t03_0.png)
![turn 3](images/11211_ctrl_rotate_0/t03_1.png)
