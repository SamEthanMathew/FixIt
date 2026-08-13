# 11178_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_1']
- ground-truth fix sequence: TRANSLATE(P1, Y, -0.14547)
- **terminal: PASS=True  score=0.683  deviation=9.5 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 9.3s

**action** `TRANSLATE(P1, Y, -0.13600)`

- PASS=True  score=0.6831  deviation=9.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 9.467 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 0.8s

**action** `TRANSLATE(P1, Y, -0.13600)`

- PASS=True  score=0.6831  deviation=9.5 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_1 | 9.467 | True | True |
