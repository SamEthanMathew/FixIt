# 10627_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_2']
- ground-truth fix sequence: ROTATE(P2, Z, -43.8612)
- **terminal: PASS=True  score=0.731  deviation=4.5 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 5.4s

**action** `ROTATE(P2, Z, -45.0000)`

- PASS=True  score=0.7313  deviation=4.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 4.534 | True | True |

![turn 1](images/10627_ctrl_rotate_0/t01_0.png)
![turn 1](images/10627_ctrl_rotate_0/t01_1.png)

## turn 2  (COMMIT)

- budget left: 9  ·  images sent: 2  ·  latency: 1.8s

**action** `ROTATE(P2, Z, -45.0000)`

- PASS=True  score=0.7313  deviation=4.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 4.534 | True | True |

![turn 2](images/10627_ctrl_rotate_0/t02_0.png)
![turn 2](images/10627_ctrl_rotate_0/t02_1.png)
