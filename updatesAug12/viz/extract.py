#!/usr/bin/env python
"""Pull the series every figure needs out of the run tree, into the scratchpad JSONs."""
import json, glob, os, re, sys
from collections import defaultdict
SP = '/tmp/claude-1003/-home-sammathew-Code-FixIt/08bc4717-a546-4ce7-8e91-49e526b7b9a5/scratchpad'
CALL = re.compile(r'(TRANSLATE|ROTATE|SCALE)\((P\d+),\s*([XYZ]),\s*(-?[\d.]+)\)')

def recs(cond):
    out = []
    for f in glob.glob(f'text_fixit/runs/one_error_{cond}/*/records.jsonl'):
        L = open(f).read().splitlines()
        if L: out.append(json.loads(L[0]))
    return out

# --- per-iteration distance from threshold, by fault type
ALL = ["er_image","g3_image","er_text","g3_text","qw8_image","dev_qw8_image","scale_qw8_image",
       "qw8_text","dev_qw8_text","scale_qw8_text"]
series = {}
for c in ALL:
    if not os.path.exists(f'text_fixit/runs/one_error_{c}/summary.json'): continue
    rs = recs(c)
    if not rs: continue
    byt, sv = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: [0, 0])
    start = defaultdict(list)
    for r in rs:
        t = r['corruption_type']
        sv[t][1] += 1; sv[t][0] += r['terminal_pass']
        start[t].append(r['initial_deviation_mm'] / r['tau_mm'])
        for i, h in enumerate(r['history'], 1):
            byt[t][i].append(h['deviation_over_tau'])
    series[c] = {"n_episodes": len(rs), "solved": sum(1 for r in rs if r['terminal_pass']),
                 "n": len(rs),
                 "by_type": {t: {"solved": v[0], "n": v[1]} for t, v in sorted(sv.items())},
                 "types": {t: [{"i": i, "mean": round(sum(v)/len(v), 2), "n": len(v)}
                               for i, v in sorted(byt[t].items())]
                           for t in ("translate","rotate","scale") if byt[t]}}
json.dump(series, open(f'{SP}/all_series.json','w'))

qw = {c: {"n_episodes": series[c]["n_episodes"],
          "types": {t: {"start": round(sum(start_)/len(start_),2) if (start_:=[]) else 0,
                        "pts": series[c]["types"][t]} for t in series[c]["types"]}}
      for c in ("qw8_image","qw8_text","dev_qw8_image","dev_qw8_text") if c in series}
for c in qw:
    for t in qw[c]["types"]:
        st = [r['initial_deviation_mm']/r['tau_mm'] for r in recs(c) if r['corruption_type']==t]
        qw[c]["types"][t]["start"] = round(sum(st)/len(st), 2) if st else 0
json.dump(qw, open(f'{SP}/qwen_series.json','w'))

# --- emitted vs required magnitude
mag = {}
for c in ["er_image","g3_image","er_text","g3_text","qw8_image","scale_qw8_image"]:
    if c not in series: continue
    pts = {"TRANSLATE": [], "ROTATE": [], "SCALE": []}
    for r in recs(c):
        g = CALL.search(r.get('gt_fix_actions') or '')
        if not g: continue
        gt_t, gt_p, gt_ax, gt_v = g.group(1), g.group(2), g.group(3), abs(float(g.group(4)))
        for h in r['history']:
            for m in CALL.finditer(h.get('action') or ''):
                if m.group(1) != gt_t: continue
                pts[gt_t].append({"emitted": abs(float(m.group(4))), "gt": gt_v,
                                  "right_axis": m.group(2)==gt_p and m.group(3)==gt_ax})
    mag[c] = pts
json.dump(mag, open(f'{SP}/mag.json','w'))
print(f'  extracted {len(series)} conditions')
