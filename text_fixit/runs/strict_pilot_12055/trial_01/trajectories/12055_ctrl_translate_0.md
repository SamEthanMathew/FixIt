# 12055_ctrl_translate_0  (control_single)

- agent: `loop_qwen_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, -0.08777)
- **terminal: PASS=False  score=0.011  deviation=123.7 mm  simulates=10**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 0.8s

**action** `ROTATE(P0, Z, -4.5000)`

- PASS=False  score=0.0359  deviation=92.1 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 92.136 | False | True |

![turn 1](images/12055_ctrl_translate_0/t01_0.png)
![turn 1](images/12055_ctrl_translate_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 1.1s

**action** `ROTATE(P0, Z, -5.0000)`

- PASS=False  score=0.0324  deviation=95.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 94.957 | False | True |

![turn 2](images/12055_ctrl_translate_0/t02_0.png)
![turn 2](images/12055_ctrl_translate_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 1.1s

**action** `ROTATE(P0, Z, -5.5000)`

- PASS=False  score=0.0288  deviation=98.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 98.226 | False | True |

![turn 3](images/12055_ctrl_translate_0/t03_0.png)
![turn 3](images/12055_ctrl_translate_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 1.3s

**action** `ROTATE(P0, Z, -6.0000)`

- PASS=False  score=0.0254  deviation=101.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 101.688 | False | True |

![turn 4](images/12055_ctrl_translate_0/t04_0.png)
![turn 4](images/12055_ctrl_translate_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 1.3s

**action** `ROTATE(P0, Z, -6.5000)`

- PASS=False  score=0.0223  deviation=105.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 105.249 | False | True |

![turn 5](images/12055_ctrl_translate_0/t05_0.png)
![turn 5](images/12055_ctrl_translate_0/t05_1.png)

## turn 6  (SIMULATE)

- budget left: 5  ·  images sent: 2  ·  latency: 1.2s

**action** `ROTATE(P0, Z, -7.0000)`

- PASS=False  score=0.0196  deviation=108.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 108.873 | False | True |

![turn 6](images/12055_ctrl_translate_0/t06_0.png)
![turn 6](images/12055_ctrl_translate_0/t06_1.png)

## turn 7  (SIMULATE)

- budget left: 4  ·  images sent: 2  ·  latency: 1.3s

**action** `ROTATE(P0, Z, -7.5000)`

- PASS=False  score=0.0172  deviation=112.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 112.54 | False | True |

![turn 7](images/12055_ctrl_translate_0/t07_0.png)
![turn 7](images/12055_ctrl_translate_0/t07_1.png)

## turn 8  (SIMULATE)

- budget left: 3  ·  images sent: 2  ·  latency: 1.3s

**action** `ROTATE(P0, Z, -8.0000)`

- PASS=False  score=0.015  deviation=116.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 116.243 | False | True |

![turn 8](images/12055_ctrl_translate_0/t08_0.png)
![turn 8](images/12055_ctrl_translate_0/t08_1.png)

## turn 9  (SIMULATE)

- budget left: 2  ·  images sent: 2  ·  latency: 1.2s

**action** `ROTATE(P0, Z, -8.5000)`

- PASS=False  score=0.0131  deviation=120.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 119.975 | False | True |

![turn 9](images/12055_ctrl_translate_0/t09_0.png)
![turn 9](images/12055_ctrl_translate_0/t09_1.png)

## turn 10  (SIMULATE)

- budget left: 1  ·  images sent: 2  ·  latency: 1.3s

**action** `ROTATE(P0, Z, -9.0000)`

- PASS=False  score=0.0115  deviation=123.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 123.735 | False | True |

![turn 10](images/12055_ctrl_translate_0/t10_0.png)
![turn 10](images/12055_ctrl_translate_0/t10_1.png)

## turn 11  (COMMIT)

- budget left: 0  ·  images sent: 2  ·  latency: 1.2s

**action** `ROTATE(P0, Z, -9.0000)`

- PASS=False  score=0.0115  deviation=123.7 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 123.735 | False | True |

![turn 11](images/12055_ctrl_translate_0/t11_0.png)
![turn 11](images/12055_ctrl_translate_0/t11_1.png)
