# 11712_ctrl_scale_0  (control_single)

- agent: `oracle`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): scale  on ['link_1']
- ground-truth fix sequence: SCALE(P1, X, 0.704582)
- **terminal: PASS=True  score=1.000  deviation=0.0 mm  simulates=0**

## turn 1  (COMMIT)

- budget left: 10

**reasoning**

> apply the exact inverse sequence (1 action(s))

**action** `SCALE(P1, X, 0.704582)`

- PASS=True  score=1.0  deviation=0.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.0 | True | True |
