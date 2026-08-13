# 12249_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_0']
- ground-truth fix sequence: TRANSLATE(P0, X, 0.17520)
- **terminal: PASS=True  score=0.915  deviation=2.2 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 191.2s

**reasoning**

> The door's X position is currently -0.166, while the fridge body is centered at 0.007 with a width of 0.981. Translating the door by 0.173 in X perfectly centers it on the body, leaving a symmetric 10mm gap on both sides, and correctly aligns its right edge with the hinge at X=0.48.

**action** `TRANSLATE(P0, X, 0.17300)`

- PASS=True  score=0.9151  deviation=2.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 2.197 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 6.7s

**reasoning**

> The simulation confirms that translating the door by 0.173 along the X axis perfectly aligns it with the refrigerator body, satisfying all success criteria.

**action** `TRANSLATE(P0, X, 0.17300)`

- PASS=True  score=0.9151  deviation=2.2 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_0 | 2.197 | True | True |
