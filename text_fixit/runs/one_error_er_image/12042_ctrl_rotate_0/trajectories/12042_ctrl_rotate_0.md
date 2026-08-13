# 12042_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_1']
- ground-truth fix sequence: ROTATE(P1, Z, -38.0044)
- **terminal: PASS=True  score=0.718  deviation=9.6 mm  simulates=2**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 6.1s

**action** `ROTATE(P1, Y, 35.0000)`

- PASS=False  score=0.0095  deviation=135.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 135.228 | False | True |

![turn 1](images/12042_ctrl_rotate_0/t01_0.png)
![turn 1](images/12042_ctrl_rotate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 5.3s

**action** `ROTATE(P1, Z, -35.0000)`

- PASS=True  score=0.7176  deviation=9.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 9.649 | True | True |

![turn 2](images/12042_ctrl_rotate_0/t02_0.png)
![turn 2](images/12042_ctrl_rotate_0/t02_1.png)

## turn 3  (COMMIT)

- budget left: 8  ·  images sent: 2  ·  latency: 1.6s

**action** `ROTATE(P1, Z, -35.0000)`

- PASS=True  score=0.7176  deviation=9.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 9.649 | True | True |

![turn 3](images/12042_ctrl_rotate_0/t03_0.png)
![turn 3](images/12042_ctrl_rotate_0/t03_1.png)
