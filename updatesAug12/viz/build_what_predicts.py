import json
S = json.load(open('/tmp/claude-1003/-home-sammathew-Code-FixIt/08bc4717-a546-4ce7-8e91-49e526b7b9a5/scratchpad/all_series.json'))
M = json.load(open('/tmp/claude-1003/-home-sammathew-Code-FixIt/08bc4717-a546-4ce7-8e91-49e526b7b9a5/scratchpad/mag.json'))
TYPES = [("translate","TRANSLATE"),("rotate","ROTATE"),("scale","SCALE")]
GRID = [("er_image","robotics-er-2 · image"),("g3_image","gemini-3.1-pro · image"),
        ("er_text","robotics-er-2 · text"),("g3_text","gemini-3.1-pro · text"),
        ("qw8_image","Qwen-8B · image"),
        ("scale_qw8_image","Qwen-8B · image + fault scale"),("qw8_text","Qwen-8B · text")]

# ---- heatmap: sequential, ONE hue, light->dark by rate. Numbers stay in ink, never colour-only.
def cell(s):
    if not s: return '<td class="na">—</td>'
    r = s["solved"]/s["n"]
    return (f'<td style="--a:{0.06 + 0.5*r:.2f}"><b>{s["solved"]}</b>/{s["n"]}'
            f'<span class="pct">{100*r:.0f}%</span></td>')
hm = "".join(f'<tr><th>{lab}</th>' + "".join(cell(S[k]["by_type"].get(t)) for t,_ in TYPES)
             + f'<td class="tot">{S[k]["solved"]}/{S[k]["n"]}</td></tr>'
             for k, lab in GRID if k in S)

# ---- magnitude: median + p10-p90 of emitted/required, target line at 1.0
RW, RH, RL, RR = 560, 30, 178, 26
XMAX = 2.0
def x(v): return RL + (RW-RL-RR) * min(v, XMAX)/XMAX
rows, y = "", 0
for k, lab in [("er_image","robotics-er-2"),("g3_image","gemini-3.1-pro"),("g3_text","gemini-3.1-pro · text"),
               ("qw8_image","Qwen-8B baseline"),("scale_qw8_image","Qwen-8B + fault scale")]:
    if k not in M: continue
    rows += f'<text x="0" y="{y+16}" class="grp">{lab}</text>'
    y += 22
    for ti,(t,key) in enumerate(TYPES):
        p = [q["emitted"]/q["gt"] for q in M[k][key] if q["gt"]]
        if not p:
            y += RH; continue
        p.sort()
        med, lo, hi = p[len(p)//2], p[int(.1*len(p))], p[min(len(p)-1,int(.9*len(p)))]
        rows += (f'<text x="14" y="{y+15}" class="rlab">{t}</text>'
                 f'<line x1="{x(lo):.1f}" y1="{y+11}" x2="{x(hi):.1f}" y2="{y+11}" class="rng s{ti}"/>'
                 f'<circle cx="{x(med):.1f}" cy="{y+11}" r="5" class="pt s{ti}">'
                 f'<title>{lab} · {t}: median {med:.2f}× required (n={len(p)}, p10 {lo:.2f}, p90 {hi:.2f})</title></circle>'
                 f'<text x="{x(hi)+8:.1f}" y="{y+15}" class="val">{med:.2f}×</text>')
        y += RH
    y += 8
H2 = y + 26
ticks = "".join(f'<line x1="{x(v):.1f}" y1="0" x2="{x(v):.1f}" y2="{y}" class="{ "target" if v==1 else "vg" }"/>'
                f'<text x="{x(v):.1f}" y="{y+16}" class="tick">{v:g}×</text>' for v in (0,0.5,1.0,1.5,2.0))

page = f'''<title>What Predicts a Repair</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
:root {{ --ground:#F4F2ED; --surface:#FCFCFB; --ink:#1A1B19; --muted:#6C6F68; --rule:#E2DFD7;
  --thr:#9C3328; --s0:#1F6FB2; --s1:#C2620E; --s2:#5B4B8A; --heat:31,111,178;
  --mono: ui-monospace,"SFMono-Regular","JetBrains Mono",Menlo,Consolas,monospace;
  --serif:"Iowan Old Style",Charter,Georgia,"Times New Roman",serif; }}
@media (prefers-color-scheme:dark){{ :root:not([data-theme="light"]){{
  --ground:#131412; --surface:#1A1A19; --ink:#ECEAE3; --muted:#9A9E95; --rule:#2C2F2A;
  --thr:#E08A7E; --s0:#2E86C8; --s1:#CF7020; --s2:#7E6BC0; --heat:46,134,200; }} }}
:root[data-theme="dark"]{{ --ground:#131412; --surface:#1A1A19; --ink:#ECEAE3; --muted:#9A9E95;
  --rule:#2C2F2A; --thr:#E08A7E; --s0:#2E86C8; --s1:#CF7020; --s2:#7E6BC0; --heat:46,134,200; }}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--serif);line-height:1.6;
  -webkit-font-smoothing:antialiased}}
.wrap{{max-width:900px;margin:0 auto;padding:44px 22px 72px}}
.eyebrow{{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);display:block;margin-bottom:10px}}
h1{{font-family:var(--mono);font-size:clamp(23px,3.2vw,32px);line-height:1.15;margin:0 0 14px;
  font-weight:600;letter-spacing:-.01em;text-wrap:balance}}
h2{{font-family:var(--mono);font-size:14px;font-weight:600;margin:38px 0 4px}}
p{{margin:0 0 14px;max-width:68ch}} .lede{{font-size:16px;color:var(--muted)}}
.cap{{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin:0 0 14px}}
table{{border-collapse:separate;border-spacing:3px;font-family:var(--mono);font-size:12.5px;
  font-variant-numeric:tabular-nums;margin:6px 0 4px}}
th{{font-weight:600;font-size:11px;color:var(--muted);text-align:right;padding:4px 9px;
  letter-spacing:.04em}}
thead th{{text-align:center}}
td{{background:rgba(var(--heat),var(--a,0));border-radius:3px;padding:8px 12px;text-align:center;
  min-width:74px}}
td b{{font-size:14px}} .pct{{display:block;font-size:9.5px;color:var(--muted)}}
td.tot{{background:none;border-left:1px solid var(--rule);color:var(--muted)}}
td.na{{background:none;color:var(--muted)}}
svg{{width:100%;height:auto;display:block;overflow:visible;font-family:var(--mono)}}
.grp{{font-size:11.5px;font-weight:600;fill:var(--ink)}}
.rlab{{font-size:11px;fill:var(--muted)}}
.val{{font-size:10.5px;fill:var(--muted)}}
.tick{{font-size:9.5px;fill:var(--muted);text-anchor:middle}}
.vg{{stroke:var(--rule);stroke-width:1}}
.target{{stroke:var(--thr);stroke-width:1.5;stroke-dasharray:4 3}}
.rng{{stroke-width:2;opacity:.4}} .pt{{stroke:var(--surface);stroke-width:1.5}}
.rng.s0,.pt.s0{{stroke:var(--s0)}} circle.s0{{fill:var(--s0)}}
.rng.s1,.pt.s1{{stroke:var(--s1)}} circle.s1{{fill:var(--s1)}}
.rng.s2,.pt.s2{{stroke:var(--s2)}} circle.s2{{fill:var(--s2)}}
.note{{background:var(--surface);border:1px solid var(--rule);border-left:3px solid var(--thr);
  border-radius:3px;padding:13px 15px;margin:22px 0}} .note p{{margin:0;font-size:14px}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>
<div class="wrap">
  <span class="eyebrow">30 problems per condition · 10 per fault type · τ = 1.5%</span>
  <h1>Which faults get fixed, and why</h1>
  <p class="lede">Two views of the same 270 episodes. The first says success depends more on the kind
  of fault — and the observation channel — than on which model you pick. The second says why.</p>

  <h2>1 · Repairs by fault type</h2>
  <p class="cap">solved out of 10 · darker is better</p>
  <table><thead><tr><th></th><th>translate</th><th>rotate</th><th>scale</th><th>overall</th></tr></thead>
  <tbody>{hm}</tbody></table>
  <p>robotics-er-2 solves <b>every</b> rotation from images and <b>none</b> from text. gemini-3.1-pro
  is the mirror image on translation — 0/10 — while taking 9/10 on scale. The two frontier models
  have different competencies, not different amounts of one competence.</p>

  <h2>2 · How big a correction each model actually proposes</h2>
  <p class="cap">emitted ÷ required magnitude, on attempts of the correct action type · dot = median,
  bar = 10th–90th percentile · 1.0× is exactly right</p>
  <svg viewBox="0 0 {RW} {H2}" role="img" aria-label="Emitted over required magnitude by model and fault type">
    {ticks}{rows}
  </svg>

  <div class="note"><p><b>Magnitude accuracy predicts the outcome almost perfectly.</b> Order each
  model's fault types by how close its median correction is to 1.0× and you recover the success
  ordering: er 1.05×→10/10, 1.10×→6/10, 0.76×→3/10; g3 1.00×→9/10, 0.93×→7/10, 0.53×→0/10.
  <b>Every model undershoots translation</b>, and translation is every model's weakest type on
  images.</p></div>

  <p>Qwen sits far left: 0.24× on translate and 0.13× on rotate — corrections four to eight times too
  small. Stating the typical fault size fixes translate (0.24×→0.90×) and scale (1.31×→0.98×) but
  barely touches rotate (0.13×→0.23×), and success stays at 1/30 — because sizing the correction is
  only useful once the right part and axis have been chosen, which Qwen manages about half the time.</p>
</div>'''
open('/home/sammathew/Code/FixIt/updatesAug12/what_predicts_repair.html','w').write(page)
print("written", round(len(page)/1024,1), "KB")
