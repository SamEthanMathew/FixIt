# 10612_ctrl_scale_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `image`  ·  deviation: `False`
- faults (1): scale  on ['link_2']
- ground-truth fix sequence: SCALE(P2, Y, 0.771633)
- **terminal: PASS=True  score=0.953  deviation=1.2 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  images sent: 2  ·  latency: 6.0s

**action** `SCALE(P2, Y, 0.770000)`

- PASS=True  score=0.9528  deviation=1.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 1.202 | True | True |

![turn 1](images/10612_ctrl_scale_0/t01_0.png)
![turn 1](images/10612_ctrl_scale_0/t01_1.png)

## turn 2  (COMMIT)

- budget left: 9  ·  images sent: 2  ·  latency: 2.0s

**action** `SCALE(P2, Y, 0.770000)`

- PASS=True  score=0.9528  deviation=1.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 1.202 | True | True |

![turn 2](images/10612_ctrl_scale_0/t02_0.png)
![turn 2](images/10612_ctrl_scale_0/t02_1.png)
