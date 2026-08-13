# 10620_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): translate  on ['link_2']
- ground-truth fix sequence: TRANSLATE(P2, X, 0.08216)
- **terminal: PASS=True  score=0.501  deviation=17.8 mm  simulates=6**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 5.6s

**action** `TRANSLATE(P2, Z, -0.10000)`

- PASS=False  score=0.0066  deviation=129.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 129.425 | False | True |

![turn 1](images/10620_ctrl_translate_0/t01_0.png)
![turn 1](images/10620_ctrl_translate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 15.2s

**action** `TRANSLATE(P2, Z, -0.12000)`

- PASS=False  score=0.0036  deviation=145.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 145.433 | False | True |

![turn 2](images/10620_ctrl_translate_0/t02_0.png)
![turn 2](images/10620_ctrl_translate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 5.6s

**action** `TRANSLATE(P2, Z, -0.15000)`

- PASS=False  score=0.0013  deviation=171.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 171.029 | False | True |

![turn 3](images/10620_ctrl_translate_0/t03_0.png)
![turn 3](images/10620_ctrl_translate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 7.0s

**action** `TRANSLATE(P2, Z, -0.20000)`

- PASS=False  score=0.0002  deviation=216.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 216.219 | False | True |

![turn 4](images/10620_ctrl_translate_0/t04_0.png)
![turn 4](images/10620_ctrl_translate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 3.6s

**action** `TRANSLATE(P2, Z, -0.25000)`

- PASS=False  score=0.0  deviation=263.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 263.155 | False | True |

![turn 5](images/10620_ctrl_translate_0/t05_0.png)
![turn 5](images/10620_ctrl_translate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 2.1s

**action** `TRANSLATE(P2, X, 0.10000)`

- PASS=True  score=0.501  deviation=17.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 17.837 | True | True |

![turn 6](images/10620_ctrl_translate_0/t06_0.png)
![turn 6](images/10620_ctrl_translate_0/t06_1.png)

## turn 7  (COMMIT)

- budget left: 4  ·  images sent: 2  ·  latency: 1.7s

**action** `TRANSLATE(P2, X, 0.10000)`

- PASS=True  score=0.501  deviation=17.8 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 17.837 | True | True |

![turn 7](images/10620_ctrl_translate_0/t07_0.png)
![turn 7](images/10620_ctrl_translate_0/t07_1.png)
