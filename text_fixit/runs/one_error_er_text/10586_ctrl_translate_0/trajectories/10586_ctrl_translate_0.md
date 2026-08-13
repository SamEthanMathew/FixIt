# 10586_ctrl_translate_0  (control_single)

- agent: `loop_gemini_full`  ·  contract: `batch`  ·  modality: `text`  ·  deviation: `False`
- faults (1): translate  on ['link_2']
- ground-truth fix sequence: TRANSLATE(P2, Y, -0.14191)
- **terminal: PASS=True  score=0.388  deviation=21.9 mm  simulates=1**

## turn 1  (SIMULATE)

- budget left: 10  ·  latency: 17.8s

**action** `TRANSLATE(P2, Y, -0.12000)`

- PASS=True  score=0.3882  deviation=21.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 21.911 | True | True |

## turn 2  (COMMIT)

- budget left: 9  ·  latency: 0.9s

**action** `TRANSLATE(P2, Y, -0.12000)`

- PASS=True  score=0.3882  deviation=21.9 mm

| part | deviation mm | within tol | closes |
|---|---|---|---|
| link_2 | 21.911 | True | True |
