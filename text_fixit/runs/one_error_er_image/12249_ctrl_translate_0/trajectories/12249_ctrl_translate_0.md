# 12249_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, 0.17520)
- **terminal: PASS=False  score=0.252  deviation=34.2 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 5.1s

**action** `ROTATE(P0, X, 10.0000)`

- PASS=False  score=0.0005  deviation=190.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 190.173 | False | True |

![turn 1](images/12249_ctrl_translate_0/t01_0.png)
![turn 1](images/12249_ctrl_translate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 8.1s

**action** `TRANSLATE(P0, X, 0.10000)`

- PASS=False  score=0.0481  deviation=75.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 75.197 | False | True |

![turn 2](images/12249_ctrl_translate_0/t02_0.png)
![turn 2](images/12249_ctrl_translate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 6.8s

**action** `TRANSLATE(P0, X, 0.08000)`

- PASS=False  score=0.0214  deviation=95.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 95.197 | False | True |

![turn 3](images/12249_ctrl_translate_0/t03_0.png)
![turn 3](images/12249_ctrl_translate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 10.3s

**action** `TRANSLATE(P0, X, 0.15000)`

- PASS=False  score=0.3617  deviation=25.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 25.197 | False | True |

![turn 4](images/12249_ctrl_translate_0/t04_0.png)
![turn 4](images/12249_ctrl_translate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 5.3s

**action** `TRANSLATE(P0, X, 0.13000)`

- PASS=False  score=0.1613  deviation=45.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 45.197 | False | True |

![turn 5](images/12249_ctrl_translate_0/t05_0.png)
![turn 5](images/12249_ctrl_translate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 4.5s

**action** `TRANSLATE(P0, X, 0.14000)`

- PASS=False  score=0.2416  deviation=35.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 35.197 | False | True |

![turn 6](images/12249_ctrl_translate_0/t06_0.png)
![turn 6](images/12249_ctrl_translate_0/t06_1.png)

## turn 7  (SIMULATE)

- budget left: 4  ·  images sent: 2  ·  latency: 6.0s

**action** `TRANSLATE(P0, X, 0.13500)`

- PASS=False  score=0.1974  deviation=40.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 40.197 | False | True |

![turn 7](images/12249_ctrl_translate_0/t07_0.png)
![turn 7](images/12249_ctrl_translate_0/t07_1.png)

## turn 8  (SIMULATE)

- budget left: 3  ·  images sent: 2  ·  latency: 10.6s

**action** `TRANSLATE(P0, X, 0.14500)`

- PASS=False  score=0.2956  deviation=30.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 30.197 | False | True |

![turn 8](images/12249_ctrl_translate_0/t08_0.png)
![turn 8](images/12249_ctrl_translate_0/t08_1.png)

## turn 9  (SIMULATE)

- budget left: 2  ·  images sent: 2  ·  latency: 6.3s

**action** `TRANSLATE(P0, X, 0.14300)`

- PASS=False  score=0.2727  deviation=32.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 32.197 | False | True |

![turn 9](images/12249_ctrl_translate_0/t09_0.png)
![turn 9](images/12249_ctrl_translate_0/t09_1.png)

## turn 10  (SIMULATE)

- budget left: 1  ·  images sent: 2  ·  latency: 3.8s

**action** `TRANSLATE(P0, X, 0.14100)`

- PASS=False  score=0.2515  deviation=34.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 34.197 | False | True |

![turn 10](images/12249_ctrl_translate_0/t10_0.png)
![turn 10](images/12249_ctrl_translate_0/t10_1.png)

## turn 11  (COMMIT)

- budget left: 0  ·  images sent: 2  ·  latency: 2.0s

**action** `TRANSLATE(P0, X, 0.14100)`

- PASS=False  score=0.2515  deviation=34.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 34.197 | False | True |

![turn 11](images/12249_ctrl_translate_0/t11_0.png)
![turn 11](images/12249_ctrl_translate_0/t11_1.png)
