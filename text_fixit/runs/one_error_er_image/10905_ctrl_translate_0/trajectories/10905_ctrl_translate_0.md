# 10905_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, Z, 0.17837)
- **terminal: PASS=False  score=0.000  deviation=364.2 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 4.6s

**action** `ROTATE(P0, Y, -40.0000)`

- PASS=False  score=0.0  deviation=286.6 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 286.565 | False | True |

![turn 1](images/10905_ctrl_translate_0/t01_0.png)
![turn 1](images/10905_ctrl_translate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 7.3s

**action** `TRANSLATE(P0, Z, -0.20000)`

- PASS=False  score=0.0  deviation=378.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 378.372 | False | True |

![turn 2](images/10905_ctrl_translate_0/t02_0.png)
![turn 2](images/10905_ctrl_translate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 47.7s

**action** `ROTATE(P0, Y, 50.0000)`

- PASS=False  score=0.0  deviation=307.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 307.04 | False | True |

![turn 3](images/10905_ctrl_translate_0/t03_0.png)
![turn 3](images/10905_ctrl_translate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 5.4s

**action** `ROTATE(P0, Y, 60.0000)`

- PASS=False  score=0.0  deviation=348.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 348.417 | False | True |

![turn 4](images/10905_ctrl_translate_0/t04_0.png)
![turn 4](images/10905_ctrl_translate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 16.2s

**action** `ROTATE(P0, Y, 60.0000)`

- PASS=False  score=0.0  deviation=348.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 348.417 | False | True |

![turn 5](images/10905_ctrl_translate_0/t05_0.png)
![turn 5](images/10905_ctrl_translate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 24.6s

**action** `ROTATE(P0, Y, -60.0000)`

- PASS=False  score=0.0  deviation=372.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 372.789 | False | True |

![turn 6](images/10905_ctrl_translate_0/t06_0.png)
![turn 6](images/10905_ctrl_translate_0/t06_1.png)

## turn 7  (SIMULATE)

- budget left: 4  ·  images sent: 2  ·  latency: 5.2s

**action** `ROTATE(P0, Y, -60.0000)`

- PASS=False  score=0.0  deviation=372.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 372.789 | False | True |

![turn 7](images/10905_ctrl_translate_0/t07_0.png)
![turn 7](images/10905_ctrl_translate_0/t07_1.png)

## turn 8  (SIMULATE)

- budget left: 3  ·  images sent: 2  ·  latency: 11.6s

**action** `ROTATE(P0, Y, -55.0000)`

- PASS=False  score=0.0  deviation=351.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 351.256 | False | True |

![turn 8](images/10905_ctrl_translate_0/t08_0.png)
![turn 8](images/10905_ctrl_translate_0/t08_1.png)

## turn 9  (SIMULATE)

- budget left: 2  ·  images sent: 2  ·  latency: 1.7s

**action** `ROTATE(P0, Y, -58.0000)`

- PASS=False  score=0.0  deviation=364.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 364.201 | False | True |

![turn 9](images/10905_ctrl_translate_0/t09_0.png)
![turn 9](images/10905_ctrl_translate_0/t09_1.png)

## turn 10  (SIMULATE)

- budget left: 1  ·  images sent: 2  ·  latency: 28.9s

**action** `ROTATE(P0, Y, -60.0000)`

- PASS=False  score=0.0  deviation=372.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 372.789 | False | True |

![turn 10](images/10905_ctrl_translate_0/t10_0.png)
![turn 10](images/10905_ctrl_translate_0/t10_1.png)

## turn 11  (COMMIT)

- budget left: 0  ·  images sent: 2  ·  latency: 4.5s

**action** `ROTATE(P0, Y, -58.0000)`

- PASS=False  score=0.0  deviation=364.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 364.201 | False | True |

![turn 11](images/10905_ctrl_translate_0/t11_0.png)
![turn 11](images/10905_ctrl_translate_0/t11_1.png)
