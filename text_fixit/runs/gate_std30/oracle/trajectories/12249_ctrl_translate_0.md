# 12249_ctrl_translate_0  (control_single)

- agent: `oracle`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, 0.17520)
- **terminal: PASS=True  score=1.000  deviation=0.0 mm  simulates=0**

## turn 1  (COMMIT)

- budget left: 10

**reasoning**

> apply the exact inverse sequence (1 action(s))

**action** `TRANSLATE(P0, X, 0.17520)`

- PASS=True  score=0.9999  deviation=0.0 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 0.003 | True | True |
