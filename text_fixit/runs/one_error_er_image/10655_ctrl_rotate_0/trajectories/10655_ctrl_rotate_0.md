# 10655_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_1']
- ground-truth fix sequence: ROTATE(P1, X, -26.7650)
- **terminal: PASS=True  score=0.518  deviation=16.9 mm  simulates=4**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 7.3s

**action** `ROTATE(P1, X, -30.0000)`

- PASS=False  score=0.1782  deviation=44.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 44.337 | False | True |

![turn 1](images/10655_ctrl_rotate_0/t01_0.png)
![turn 1](images/10655_ctrl_rotate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 4.3s

**action** `ROTATE(P1, X, -45.0000)`

- PASS=False  score=0.0001  deviation=248.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 248.898 | False | False |

![turn 2](images/10655_ctrl_rotate_0/t02_0.png)
![turn 2](images/10655_ctrl_rotate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 3.1s

**action** `ROTATE(P1, X, -33.0000)`

- PASS=False  score=0.0361  deviation=85.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 85.423 | False | False |

![turn 3](images/10655_ctrl_rotate_0/t03_0.png)
![turn 3](images/10655_ctrl_rotate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 7.4s

**action** `ROTATE(P1, X, -28.0000)`

- PASS=True  score=0.5176  deviation=16.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 16.928 | True | True |

![turn 4](images/10655_ctrl_rotate_0/t04_0.png)
![turn 4](images/10655_ctrl_rotate_0/t04_1.png)

## turn 5  (COMMIT)

- budget left: 6  ·  images sent: 2  ·  latency: 2.8s

**action** `ROTATE(P1, X, -28.0000)`

- PASS=True  score=0.5176  deviation=16.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 16.928 | True | True |

![turn 5](images/10655_ctrl_rotate_0/t05_0.png)
![turn 5](images/10655_ctrl_rotate_0/t05_1.png)
