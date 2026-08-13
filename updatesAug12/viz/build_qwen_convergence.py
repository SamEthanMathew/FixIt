import json

D = json.load(open('/tmp/claude-1003/-home-sammathew-Code-FixIt/08bc4717-a546-4ce7-8e91-49e526b7b9a5/scratchpad/qwen_series.json'))
TYPES = ["translate", "rotate", "scale"]
SLOT = {"translate": 0, "rotate": 1, "scale": 2}          # fixed order, never cycled
YMAX, W, H = 11.0, 470, 300
PL, PR, PT, PB = 46, 18, 16, 40


def xy(i, v):
    x = PL + (W - PL - PR) * ((i - 1) / 10)
    y = PT + (H - PT - PB) * (1 - min(v, YMAX) / YMAX)
    return x, y


def panel(cond, title, sub):
    d = D[cond]["types"]
    g = "".join(
        f'<line x1="{PL}" y1="{xy(1, v)[1]:.1f}" x2="{W - PR}" y2="{xy(1, v)[1]:.1f}" class="grid"/>'
        f'<text x="{PL - 8}" y="{xy(1, v)[1] + 3.5:.1f}" class="tick">{v:g}×</text>'
        for v in (0, 2, 4, 6, 8, 10))
    xt = "".join(f'<text x="{xy(i, 0)[0]:.1f}" y="{H - PB + 17:.1f}" class="tick mid">{i}</text>'
                 for i in (1, 2, 4, 6, 8, 10))
    ty = xy(1, 1.0)[1]
    thr = (f'<line x1="{PL}" y1="{ty:.1f}" x2="{W - PR}" y2="{ty:.1f}" class="thr"/>'
           f'<text x="{W - PR}" y="{ty - 7:.1f}" class="thrlab" text-anchor="end">'
           f'threshold — a repair passes below this line</text>')
    series = ""
    for t in TYPES:
        if t not in d: continue
        pts = d[t]["pts"]
        path = " ".join(f"{xy(p['i'], p['mean'])[0]:.1f},{xy(p['i'], p['mean'])[1]:.1f}" for p in pts)
        dots = "".join(
            f'<circle cx="{xy(p["i"], p["mean"])[0]:.1f}" cy="{xy(p["i"], p["mean"])[1]:.1f}" r="4.5" '
            f'class="dot s{SLOT[t]}"><title>{t} · iteration {p["i"]}: {p["mean"]}× tolerance '
            f'(mean of {p["n"]} problems)</title></circle>' for p in pts)
        lp = pts[-1]
        lx, ly = xy(lp["i"], lp["mean"])
        series += (f'<polyline points="{path}" class="ln s{SLOT[t]}"/>{dots}'
                   f'<text x="{lx + 8:.1f}" y="{ly + 4:.1f}" class="dlab s{SLOT[t]}">{t}</text>')
    return f'''<figure class="panel">
  <figcaption><h3>{title}</h3><p class="sub">{sub}</p></figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{title}: mean distance from threshold per iteration, by fault type">
    {g}{xt}{thr}{series}
    <text x="{PL + (W - PL - PR) / 2:.0f}" y="{H - 4}" class="axlab mid">iteration</text>
  </svg>
</figure>'''


CONDS = [("qw8_image", "image", "baseline"), ("dev_qw8_image", "image", "error shown"),
         ("qw8_text", "text", "baseline"), ("dev_qw8_text", "text", "error shown")]
rows = ""
for t in TYPES:
    for cond, mod, lab in CONDS:
        pts = {x["i"]: x for x in D[cond]["types"][t]["pts"]}
        a, b = pts.get(1), pts.get(8)
        delta = f"{b['mean'] - a['mean']:+.1f}×" if a and b else "—"
        rows += (f"<tr><td>{t}</td><td>{mod}</td><td>{lab}</td>"
                 f"<td>{D[cond]['types'][t]['start']}×</td>"
                 f"<td>{a['mean']}×</td><td>{b['mean'] if b else '—'}×</td>"
                 f"<td class=\"d\">{delta}</td></tr>")

page = f'''<title>Qwen's Flat Line</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
:root {{
  --ground:#F4F2ED; --surface:#FCFCFB; --ink:#1A1B19; --muted:#6C6F68; --rule:#E2DFD7;
  --thr:#9C3328; --s0:#1F6FB2; --s1:#C2620E; --s2:#5B4B8A;
  --mono: ui-monospace, "SFMono-Regular", "JetBrains Mono", Menlo, Consolas, monospace;
  --serif: "Iowan Old Style", Charter, Georgia, "Times New Roman", serif;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#131412; --surface:#1A1A19; --ink:#ECEAE3; --muted:#9A9E95; --rule:#2C2F2A;
    --thr:#E08A7E; --s0:#2E86C8; --s1:#CF7020; --s2:#7E6BC0;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#131412; --surface:#1A1A19; --ink:#ECEAE3; --muted:#9A9E95; --rule:#2C2F2A;
  --thr:#E08A7E; --s0:#2E86C8; --s1:#CF7020; --s2:#7E6BC0;
}}
*{{box-sizing:border-box}}
body {{ margin:0; background:var(--ground); color:var(--ink); font-family:var(--serif);
  line-height:1.6; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:1060px; margin:0 auto; padding:44px 22px 72px; }}
.eyebrow {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--muted); display:block; margin-bottom:10px; }}
h1 {{ font-family:var(--mono); font-size:clamp(23px,3.2vw,33px); line-height:1.15; margin:0 0 14px;
  font-weight:600; letter-spacing:-.01em; text-wrap:balance; }}
h3 {{ font-family:var(--mono); font-size:14px; margin:0 0 2px; font-weight:600; }}
p {{ margin:0 0 14px; max-width:66ch; }}
.lede {{ font-size:16.5px; color:var(--muted); }}
.panels {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(400px,1fr)); gap:20px;
  margin:26px 0 8px; }}
.panel {{ margin:0; background:var(--surface); border:1px solid var(--rule); border-radius:3px;
  padding:14px 14px 6px; }}
.panel figcaption {{ margin-bottom:6px; }}
.sub {{ font-family:var(--mono); font-size:11px; color:var(--muted); }}
svg {{ width:100%; height:auto; display:block; overflow:visible; }}
.grid {{ stroke:var(--rule); stroke-width:1; }}
.tick {{ font-family:var(--mono); font-size:9.5px; fill:var(--muted); text-anchor:end; }}
.tick.mid, .axlab.mid {{ text-anchor:middle; }}
.axlab {{ font-family:var(--mono); font-size:10px; fill:var(--muted); }}
.thr {{ stroke:var(--thr); stroke-width:1.5; stroke-dasharray:5 3; }}
.thrlab {{ font-family:var(--mono); font-size:9.5px; fill:var(--thr); }}
.ln {{ fill:none; stroke-width:2; stroke-linejoin:round; stroke-linecap:round; }}
.dot {{ stroke:var(--surface); stroke-width:2; }}
.dlab {{ font-family:var(--mono); font-size:10.5px; font-weight:600; }}
.s0 {{ stroke:var(--s0); }} .s1 {{ stroke:var(--s1); }} .s2 {{ stroke:var(--s2); }}
circle.s0,text.s0 {{ fill:var(--s0); }} circle.s1,text.s1 {{ fill:var(--s1); }}
circle.s2,text.s2 {{ fill:var(--s2); }}
table {{ border-collapse:collapse; width:100%; font-family:var(--mono); font-size:12px;
  font-variant-numeric:tabular-nums; margin-top:10px; }}
th,td {{ text-align:right; padding:6px 9px; border-bottom:1px solid var(--rule); }}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2) {{ text-align:left; }}
th {{ font-size:10px; letter-spacing:.07em; text-transform:uppercase; color:var(--muted);
  font-weight:600; }}
.note {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--thr);
  border-radius:3px; padding:13px 15px; margin:22px 0; }}
.note p {{ margin:0; font-size:14px; }}
td.d {{ font-weight:600; }}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>
<div class="wrap">
  <span class="eyebrow">Qwen3-VL-8B · 30 problems × 4 conditions · τ = 1.5%</span>
  <h1>No, it is not going down</h1>
  <p class="lede">Each line is the mean distance from the passing threshold across the 10 problems of
  one fault type, at each iteration. Lower is better; below the dashed line is a repair. The right
  column adds the one thing that should fix a magnitude problem — telling the model, every turn,
  exactly how many millimetres off it still is. It changes nothing: <strong>1 solve in 120
  episodes</strong>, and the lines stay flat.</p>

  <div class="panels">
    {panel("qw8_image", "Image · baseline", "the model is never told its error")}
    {panel("dev_qw8_image", "Image · error shown", "every turn reports “off by N mm (tolerance M mm)”")}
    {panel("qw8_text", "Text · baseline", "the model is never told its error")}
    {panel("dev_qw8_text", "Text · error shown", "every turn reports “off by N mm (tolerance M mm)”")}
  </div>

  <div class="note"><p>Later iterations average over fewer problems, because an episode that commits
  early stops contributing. Point counts are in the tooltips and the final column below — the
  right-hand end of each line is the thinnest evidence on the chart.</p></div>

  <table>
    <thead><tr><th>fault type</th><th>modality</th><th>condition</th><th>start</th>
      <th>iter 1</th><th>iter 8</th><th>change</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="note"><p>The same intervention on the frontier models took them from 20% to 76%.
  Here the largest movement between iteration 1 and iteration 8 is 1.0× tolerance, in either
  direction, against a starting distance of 6–10×. The model would have to close a gap of roughly
  7× to pass, so this is not slow progress — it is no progress.</p></div>

  <p style="margin-top:22px">Distance is expressed in multiples of each problem's own tolerance,
  because tolerance is a fraction of the part and varies from 17 to 28 mm across these 30 fridges —
  raw millimetres would not be comparable between them.</p>
</div>'''

open('/home/sammathew/Code/FixIt/updatesAug12/qwen_convergence.html', 'w').write(page)
print("written", round(len(page) / 1024, 1), "KB")
