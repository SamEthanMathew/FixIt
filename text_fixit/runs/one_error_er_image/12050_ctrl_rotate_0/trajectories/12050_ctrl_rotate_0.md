# 12050_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_0']
- ground-truth fix sequence: ROTATE(P0, X, -23.0027)
- **terminal: PASS=True  score=0.436  deviation=9.9 mm  simulates=6**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 5.6s

**action** `ROTATE(P0, X, 30.0000)`

- PASS=False  score=0.0002  deviation=101.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 101.352 | False | True |

![turn 1](images/12050_ctrl_rotate_0/t01_0.png)
![turn 1](images/12050_ctrl_rotate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 2.2s

**action** `ROTATE(P0, X, -40.0000)`

- PASS=False  score=0.06  deviation=33.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 33.567 | False | True |

![turn 2](images/12050_ctrl_rotate_0/t02_0.png)
![turn 2](images/12050_ctrl_rotate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 2.4s

**action** `ROTATE(P0, X, -50.0000)`

- PASS=False  score=0.0118  deviation=53.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 53.018 | False | True |

![turn 3](images/12050_ctrl_rotate_0/t03_0.png)
![turn 3](images/12050_ctrl_rotate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 2.8s

**action** `ROTATE(P0, X, -55.0000)`

- PASS=False  score=0.0053  deviation=62.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 62.602 | False | True |

![turn 4](images/12050_ctrl_rotate_0/t04_0.png)
![turn 4](images/12050_ctrl_rotate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 8.9s

**action** `ROTATE(P0, X, -30.0000)`

- PASS=False  score=0.313  deviation=13.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 13.861 | False | True |

![turn 5](images/12050_ctrl_rotate_0/t05_0.png)
![turn 5](images/12050_ctrl_rotate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 3.7s

**action** `ROTATE(P0, X, -28.0000)`

- PASS=True  score=0.4361  deviation=9.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 9.902 | True | True |

![turn 6](images/12050_ctrl_rotate_0/t06_0.png)
![turn 6](images/12050_ctrl_rotate_0/t06_1.png)

## turn 7  (COMMIT)

- budget left: 4  ·  images sent: 2  ·  latency: 2.7s

**action** `ROTATE(P0, X, -28.0000)`

- PASS=True  score=0.4361  deviation=9.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 9.902 | True | True |

![turn 7](images/12050_ctrl_rotate_0/t07_0.png)
![turn 7](images/12050_ctrl_rotate_0/t07_1.png)
