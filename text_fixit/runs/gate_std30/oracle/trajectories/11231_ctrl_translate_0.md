# 11231_ctrl_translate_0  (control_single)

- agent: `oracle`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_1']
- ground-truth fix sequence: TRANSLATE(P1, X, 0.18806)
- **terminal: PASS=True  score=1.000  deviation=0.0 mm  simulates=0**

## turn 1  (COMMIT)

- budget left: 10

**reasoning**

> apply the exact inverse sequence (1 action(s))

**action** `TRANSLATE(P1, X, 0.18806)`

- PASS=True  score=0.9998  deviation=0.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 0.004 | True | True |
