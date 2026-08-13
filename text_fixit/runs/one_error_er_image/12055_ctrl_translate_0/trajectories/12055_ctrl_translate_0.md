# 12055_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, -0.08777)
- **terminal: PASS=False  score=0.003  deviation=160.7 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 12.9s

**action** `ROTATE(P0, Y, -20.0000)`

- PASS=False  score=0.016  deviation=114.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 114.506 | False | True |

![turn 1](images/12055_ctrl_translate_0/t01_0.png)
![turn 1](images/12055_ctrl_translate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 4.1s

**action** `ROTATE(P0, Y, 25.0000)`

- PASS=False  score=0.0089  deviation=130.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 130.7 | False | True |

![turn 2](images/12055_ctrl_translate_0/t02_0.png)
![turn 2](images/12055_ctrl_translate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 5.1s

**action** `ROTATE(P0, Y, 30.0000)`

- PASS=False  score=0.0052  deviation=145.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 145.35 | False | True |

![turn 3](images/12055_ctrl_translate_0/t03_0.png)
![turn 3](images/12055_ctrl_translate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 10.2s

**action** `ROTATE(P0, Z, 5.0000)`

- PASS=False  score=0.0382  deviation=90.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 90.425 | False | True |

![turn 4](images/12055_ctrl_translate_0/t04_0.png)
![turn 4](images/12055_ctrl_translate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 3.1s

**action** `ROTATE(P0, Z, -10.0000)`

- PASS=False  score=0.0087  deviation=131.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 131.325 | False | True |

![turn 5](images/12055_ctrl_translate_0/t05_0.png)
![turn 5](images/12055_ctrl_translate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 5.4s

**action** `ROTATE(P0, Z, -3.0000)`

- PASS=False  score=0.0406  deviation=88.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 88.687 | False | True |

![turn 6](images/12055_ctrl_translate_0/t06_0.png)
![turn 6](images/12055_ctrl_translate_0/t06_1.png)

## turn 7  (SIMULATE)

- budget left: 4  ·  images sent: 2  ·  latency: 2.1s

**action** `ROTATE(P0, Z, -5.0000)`

- PASS=False  score=0.0324  deviation=95.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 94.957 | False | True |

![turn 7](images/12055_ctrl_translate_0/t07_0.png)
![turn 7](images/12055_ctrl_translate_0/t07_1.png)

## turn 8  (SIMULATE)

- budget left: 3  ·  images sent: 2  ·  latency: 2.0s

**action** `ROTATE(P0, Z, -7.0000)`

- PASS=False  score=0.0196  deviation=108.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 108.873 | False | True |

![turn 8](images/12055_ctrl_translate_0/t08_0.png)
![turn 8](images/12055_ctrl_translate_0/t08_1.png)

## turn 9  (SIMULATE)

- budget left: 2  ·  images sent: 2  ·  latency: 6.1s

**action** `ROTATE(P0, Y, 45.0000)`

- PASS=False  score=0.001  deviation=192.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 192.211 | False | True |

![turn 9](images/12055_ctrl_translate_0/t09_0.png)
![turn 9](images/12055_ctrl_translate_0/t09_1.png)

## turn 10  (SIMULATE)

- budget left: 1  ·  images sent: 2  ·  latency: 3.3s

**action** `ROTATE(P0, Y, 35.0000)`

- PASS=False  score=0.003  deviation=160.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 160.664 | False | True |

![turn 10](images/12055_ctrl_translate_0/t10_0.png)
![turn 10](images/12055_ctrl_translate_0/t10_1.png)

## turn 11  (COMMIT)

- budget left: 0  ·  images sent: 2  ·  latency: 3.7s

**action** `ROTATE(P0, Y, 35.0000)`

- PASS=False  score=0.003  deviation=160.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 160.664 | False | True |

![turn 11](images/12055_ctrl_translate_0/t11_0.png)
![turn 11](images/12055_ctrl_translate_0/t11_1.png)
