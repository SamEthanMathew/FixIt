# 10849_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, -0.08517)
- **terminal: PASS=False  score=0.027  deviation=90.3 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 9.5s

**action** `TRANSLATE(P0, Y, 0.08000)`

- PASS=False  score=0.0095  deviation=116.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 116.85 | False | True |

![turn 1](images/10849_ctrl_translate_0/t01_0.png)
![turn 1](images/10849_ctrl_translate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 17.0s

**action** `TRANSLATE(P0, X, 0.05000)`

- PASS=False  score=0.0046  deviation=135.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 135.17 | False | True |

![turn 2](images/10849_ctrl_translate_0/t02_0.png)
![turn 2](images/10849_ctrl_translate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 8.6s

**action** `ROTATE(P0, Y, -5.0000)`

- PASS=False  score=0.0286  deviation=89.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 89.105 | False | True |

![turn 3](images/10849_ctrl_translate_0/t03_0.png)
![turn 3](images/10849_ctrl_translate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 4.8s

**action** `TRANSLATE(P0, Z, 0.05000)`

- PASS=False  score=0.0195  deviation=98.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 98.762 | False | True |

![turn 4](images/10849_ctrl_translate_0/t04_0.png)
![turn 4](images/10849_ctrl_translate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 4.4s

**action** `TRANSLATE(P0, Y, -0.05000)`

- PASS=False  score=0.0195  deviation=98.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 98.762 | False | True |

![turn 5](images/10849_ctrl_translate_0/t05_0.png)
![turn 5](images/10849_ctrl_translate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 21.1s

**action** `ROTATE(P0, Y, -15.0000)`

- PASS=False  score=0.0117  deviation=111.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 111.566 | False | True |

![turn 6](images/10849_ctrl_translate_0/t06_0.png)
![turn 6](images/10849_ctrl_translate_0/t06_1.png)

## turn 7  (SIMULATE)

- budget left: 4  ·  images sent: 2  ·  latency: 7.2s

**action** `TRANSLATE(P0, Z, -0.05000)`

- PASS=False  score=0.0195  deviation=98.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 98.762 | False | True |

![turn 7](images/10849_ctrl_translate_0/t07_0.png)
![turn 7](images/10849_ctrl_translate_0/t07_1.png)

## turn 8  (SIMULATE)

- budget left: 3  ·  images sent: 2  ·  latency: 9.1s

**action** `TRANSLATE(P0, Z, -0.03000)`

- PASS=False  score=0.0273  deviation=90.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 90.299 | False | True |

![turn 8](images/10849_ctrl_translate_0/t08_0.png)
![turn 8](images/10849_ctrl_translate_0/t08_1.png)

## turn 9  (SIMULATE)

- budget left: 2  ·  images sent: 2  ·  latency: 5.9s

**action** `ROTATE(P0, Y, 10.0000)`

- PASS=False  score=0.0192  deviation=99.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 99.089 | False | True |

![turn 9](images/10849_ctrl_translate_0/t09_0.png)
![turn 9](images/10849_ctrl_translate_0/t09_1.png)

## turn 10  (SIMULATE)

- budget left: 1  ·  images sent: 2  ·  latency: 8.0s

**action** `TRANSLATE(P0, Y, -0.03000)`

- PASS=False  score=0.0273  deviation=90.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 90.299 | False | True |

![turn 10](images/10849_ctrl_translate_0/t10_0.png)
![turn 10](images/10849_ctrl_translate_0/t10_1.png)

## turn 11  (COMMIT)

- budget left: 0  ·  images sent: 2  ·  latency: 2.1s

**action** `TRANSLATE(P0, Y, -0.03000)`

- PASS=False  score=0.0273  deviation=90.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 90.299 | False | True |

![turn 11](images/10849_ctrl_translate_0/t11_0.png)
![turn 11](images/10849_ctrl_translate_0/t11_1.png)
