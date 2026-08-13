# 12042_ctrl_rotate_0  (control_single)

- agent: `oracle`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): rotate  on ['link_1']
- ground-truth fix sequence: ROTATE(P1, Z, -38.0044)
- **terminal: PASS=True  score=1.000  deviation=0.0 mm  simulates=0**

## turn 1  (COMMIT)

- budget left: 10

**reasoning**

> apply the exact inverse sequence (1 action(s))

**action** `ROTATE(P1, Z, -38.0044)`

- PASS=True  score=1.0  deviation=0.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.0 | True | True |
