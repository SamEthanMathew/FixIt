# 10143_ctrl_rotate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): rotate  on ['link_2']
- ground-truth fix sequence: ROTATE(P2, Z, -23.7176)
- **terminal: PASS=True  score=0.962  deviation=0.6 mm  simulates=9**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 8.2s

**action** `ROTATE(P2, Z, 30.0000)`

- PASS=False  score=0.0008  deviation=105.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 105.299 | False | False |

![turn 1](images/10143_ctrl_rotate_0/t01_0.png)
![turn 1](images/10143_ctrl_rotate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 3.3s

**action** `ROTATE(P2, Z, -30.0000)`

- PASS=False  score=0.4181  deviation=12.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 12.771 | True | False |

![turn 2](images/10143_ctrl_rotate_0/t02_0.png)
![turn 2](images/10143_ctrl_rotate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 5.8s

**action** `ROTATE(P2, Z, -45.0000)`

- PASS=False  score=0.053  deviation=43.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 43.038 | False | False |

![turn 3](images/10143_ctrl_rotate_0/t03_0.png)
![turn 3](images/10143_ctrl_rotate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 4.6s

**action** `ROTATE(P2, Z, -20.0000)`

- PASS=False  score=0.5968  deviation=7.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 7.56 | True | False |

![turn 4](images/10143_ctrl_rotate_0/t04_0.png)
![turn 4](images/10143_ctrl_rotate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 4.5s

**action** `ROTATE(P2, Z, -15.0000)`

- PASS=False  score=0.2984  deviation=17.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 17.714 | False | False |

![turn 5](images/10143_ctrl_rotate_0/t05_0.png)
![turn 5](images/10143_ctrl_rotate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 4.8s

**action** `ROTATE(P2, Z, -23.0000)`

- PASS=False  score=0.9052  deviation=1.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 1.46 | True | False |

![turn 6](images/10143_ctrl_rotate_0/t06_0.png)
![turn 6](images/10143_ctrl_rotate_0/t06_1.png)

## turn 7  (SIMULATE)

- budget left: 4  ·  images sent: 2  ·  latency: 2.7s

**action** `ROTATE(P2, Z, -25.0000)`

- PASS=False  score=0.8369  deviation=2.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 2.608 | True | False |

![turn 7](images/10143_ctrl_rotate_0/t07_0.png)
![turn 7](images/10143_ctrl_rotate_0/t07_1.png)

## turn 8  (SIMULATE)

- budget left: 3  ·  images sent: 2  ·  latency: 8.5s

**action** `ROTATE(P2, Z, -22.0000)`

- PASS=False  score=0.7878  deviation=3.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 3.493 | True | False |

![turn 8](images/10143_ctrl_rotate_0/t08_0.png)
![turn 8](images/10143_ctrl_rotate_0/t08_1.png)

## turn 9  (SIMULATE)

- budget left: 2  ·  images sent: 2  ·  latency: 3.4s

**action** `ROTATE(P2, Z, -24.0000)`

- PASS=True  score=0.9615  deviation=0.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 0.574 | True | True |

![turn 9](images/10143_ctrl_rotate_0/t09_0.png)
![turn 9](images/10143_ctrl_rotate_0/t09_1.png)

## turn 10  (COMMIT)

- budget left: 1  ·  images sent: 2  ·  latency: 1.6s

**action** `ROTATE(P2, Z, -24.0000)`

- PASS=True  score=0.9615  deviation=0.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 0.574 | True | True |

![turn 10](images/10143_ctrl_rotate_0/t10_0.png)
![turn 10](images/10143_ctrl_rotate_0/t10_1.png)
