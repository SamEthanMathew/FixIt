# 12054_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): scale  on ['link_0']
- ground-truth fix sequence: SCALE(P0, X, 0.715502)
- **terminal: PASS=True  score=0.871  deviation=4.0 mm  simulates=5**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 10.0s

**action** `ROTATE(P0, Y, 15.0000)`

- PASS=False  score=0.0006  deviation=219.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 218.969 | False | True |

![turn 1](images/12054_ctrl_scale_0/t01_0.png)
![turn 1](images/12054_ctrl_scale_0/t01_1.png)

## turn 2  (SIMULATE)

- budget left: 9  ·  images sent: 2  ·  latency: 21.5s

**action** `SCALE(P0, X, 1.200000)`

- PASS=False  score=0.0  deviation=355.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 355.204 | False | True |

![turn 2](images/12054_ctrl_scale_0/t02_0.png)
![turn 2](images/12054_ctrl_scale_0/t02_1.png)

## turn 3  (SIMULATE)

- budget left: 8  ·  images sent: 2  ·  latency: 23.7s

**action** `SCALE(P0, X, 0.550000)`

- PASS=False  score=0.0157  deviation=121.3 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 121.336 | False | True |

![turn 3](images/12054_ctrl_scale_0/t03_0.png)
![turn 3](images/12054_ctrl_scale_0/t03_1.png)

## turn 4  (SIMULATE)

- budget left: 7  ·  images sent: 2  ·  latency: 14.7s

**action** `ROTATE(P0, Y, -10.0000)`

- PASS=False  score=0.0006  deviation=216.4 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 216.377 | False | True |

![turn 4](images/12054_ctrl_scale_0/t04_0.png)
![turn 4](images/12054_ctrl_scale_0/t04_1.png)

## turn 5  (SIMULATE)

- budget left: 6  ·  images sent: 2  ·  latency: 45.5s

**action** `SCALE(P0, X, 0.710000)`

- PASS=True  score=0.8711  deviation=4.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 4.034 | True | True |

![turn 5](images/12054_ctrl_scale_0/t05_0.png)
![turn 5](images/12054_ctrl_scale_0/t05_1.png)

## turn 6  (COMMIT)

- budget left: 5  ·  images sent: 2  ·  latency: 3.0s

**action** `SCALE(P0, X, 0.710000)`

- PASS=True  score=0.8711  deviation=4.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 4.034 | True | True |

![turn 6](images/12054_ctrl_scale_0/t06_0.png)
![turn 6](images/12054_ctrl_scale_0/t06_1.png)
