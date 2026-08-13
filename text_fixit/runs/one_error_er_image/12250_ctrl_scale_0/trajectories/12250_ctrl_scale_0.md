# 12250_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): scale  on ['link_1']
- ground-truth fix sequence: SCALE(P1, Y, 0.733483)
- **terminal: PASS=True  score=0.918  deviation=2.5 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 7.2s

**action** `SCALE(P1, Y, 0.730000)`

- PASS=True  score=0.9177  deviation=2.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 2.495 | True | True |

![turn 1](images/12250_ctrl_scale_0/t01_0.png)
![turn 1](images/12250_ctrl_scale_0/t01_1.png)

## turn 2  (COMMIT)

- budget left: 9  ·  images sent: 2  ·  latency: 3.0s

**action** `SCALE(P1, Y, 0.730000)`

- PASS=True  score=0.9177  deviation=2.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 2.495 | True | True |

![turn 2](images/12250_ctrl_scale_0/t02_0.png)
![turn 2](images/12250_ctrl_scale_0/t02_1.png)
