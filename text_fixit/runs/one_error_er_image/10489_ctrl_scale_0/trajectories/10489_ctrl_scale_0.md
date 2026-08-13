# 10489_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): scale  on ['link_2']
- ground-truth fix sequence: SCALE(P2, Y, 0.771644)
- **terminal: PASS=True  score=0.766  deviation=5.4 mm  simulates=6**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 8.1s

**action** `TRANSLATE(P2, Y, -0.11600)`

- PASS=False  score=0.0001  deviation=194.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 194.079 | False | False |

![turn 1](images/10489_ctrl_scale_0/t01_0.png)
![turn 1](images/10489_ctrl_scale_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 10.0s

**action** `SCALE(P2, Y, 0.924000)`

- PASS=False  score=0.0001  deviation=188.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 188.355 | False | False |

![turn 2](images/10489_ctrl_scale_0/t02_0.png)
![turn 2](images/10489_ctrl_scale_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 49.0s

**action** `SCALE(P1, Y, 0.758000)`

- PASS=False  score=0.0  deviation=282.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 282.312 | False | False |

![turn 3](images/10489_ctrl_scale_0/t03_0.png)
![turn 3](images/10489_ctrl_scale_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 25.7s

**action** `TRANSLATE(P1, Y, 0.11600)`

- PASS=False  score=0.0  deviation=282.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 282.312 | False | False |

![turn 4](images/10489_ctrl_scale_0/t04_0.png)
![turn 4](images/10489_ctrl_scale_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 126.9s

**action** `SCALE(P2, Y, 0.797000)`

- PASS=False  score=0.2114  deviation=31.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 31.347 | False | False |

![turn 5](images/10489_ctrl_scale_0/t05_0.png)
![turn 5](images/10489_ctrl_scale_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 8.2s

**action** `SCALE(P2, Y, 0.776000)`

- PASS=True  score=0.7657  deviation=5.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 5.385 | True | True |

![turn 6](images/10489_ctrl_scale_0/t06_0.png)
![turn 6](images/10489_ctrl_scale_0/t06_1.png)

## turn 7  (COMMIT)

- budget left: 4  ·  images sent: 2  ·  latency: 3.8s

**action** `SCALE(P2, Y, 0.776000)`

- PASS=True  score=0.7657  deviation=5.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 5.385 | True | True |

![turn 7](images/10489_ctrl_scale_0/t07_0.png)
![turn 7](images/10489_ctrl_scale_0/t07_1.png)
