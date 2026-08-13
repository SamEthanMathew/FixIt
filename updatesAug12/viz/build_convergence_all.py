import json

D = json.load(open('/tmp/claude-1003/-home-sammathew-Code-FixIt/08bc4717-a546-4ce7-8e91-49e526b7b9a5/scratchpad/all_series.json'))
TYPES = ["translate", "rotate", "scale"]
SLOT = {"translate": 0, "rotate": 1, "scale": 2}     # fixed order, never cycled
YMAX, W, H = 11.0, 330, 210
PL, PR, PT, PB = 34, 12, 10, 30

ROWS = [
    ("What convergence looks like — the API models",
     [("er_image", "robotics-er-2 · image"), ("g3_image", "gemini-3.1-pro · image"),
      ("er_text", "robotics-er-2 · text"), ("g3_text", "gemini-3.1-pro · text")]),
    ("Qwen3-VL-8B · image — three prompts, one outcome",
     [("qw8_image", "baseline"), ("dev_qw8_image", "+ error shown in mm"),
      ("scale_qw8_image", "+ fault scale stated")]),
    ("Qwen3-VL-8B · text — the same three",
     [("qw8_text", "baseline"), ("dev_qw8_text", "+ error shown in mm"),
      ("scale_qw8_text", "+ fault scale stated")]),
]


def xy(i, v):
    return (PL + (W - PL - PR) * ((i - 1) / 10),
            PT + (H - PT - PB) * (1 - min(v, YMAX) / YMAX))


def panel(key, label):
    s = D[key]
    grid = "".join(
        f'<line x1="{PL}" y1="{xy(1, v)[1]:.1f}" x2="{W-PR}" y2="{xy(1, v)[1]:.1f}" class="grid"/>'
        f'<text x="{PL-5}" y="{xy(1, v)[1]+3:.1f}" class="tick">{v:g}</text>' for v in (0, 5, 10))
    xt = "".join(f'<text x="{xy(i,0)[0]:.1f}" y="{H-PB+14:.1f}" class="tick mid">{i}</text>'
                 for i in (1, 5, 10))
    ty = xy(1, 1.0)[1]
    thr = (f'<line x1="{PL}" y1="{ty:.1f}" x2="{W-PR}" y2="{ty:.1f}" class="thr"/>')
    ser = ""
    for t in TYPES:
        pts = s["types"].get(t)
        if not pts:
            continue
        path = " ".join(f"{xy(p['i'],p['mean'])[0]:.1f},{xy(p['i'],p['mean'])[1]:.1f}" for p in pts)
        dots = "".join(
            f'<circle cx="{xy(p["i"],p["mean"])[0]:.1f}" cy="{xy(p["i"],p["mean"])[1]:.1f}" r="3.4" '
            f'class="dot s{SLOT[t]}"><title>{t} · iteration {p["i"]}: {p["mean"]}× tolerance '
            f'({p["n"]} problems)</title></circle>' for p in pts)
        ser += f'<polyline points="{path}" class="ln s{SLOT[t]}"/>{dots}'
    bt = " · ".join(f'<span class="s{SLOT[t]}">{v["solved"]}/{v["n"]}</span>'
                    for t, v in s["by_type"].items() if t in SLOT)
    pct = 100 * s["solved"] / s["n"]
    return f'''<figure class="panel">
  <figcaption><h3>{label}</h3>
    <p class="score"><b>{s['solved']}/{s['n']}</b> solved ({pct:.0f}%) &nbsp;·&nbsp; {bt}</p>
  </figcaption>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label="{label}: mean distance from threshold per iteration by fault type">
    {grid}{xt}{thr}{ser}
  </svg>
</figure>'''


body = ""
for title, panels in ROWS:
    body += f'<h2>{title}</h2><div class="row">' + \
            "".join(panel(k, l) for k, l in panels if k in D) + "</div>"

page = f'''<title>Ten Convergence Traces</title>
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
.wrap {{ max-width:1160px; margin:0 auto; padding:44px 22px 72px; }}
.eyebrow {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--muted); display:block; margin-bottom:10px; }}
h1 {{ font-family:var(--mono); font-size:clamp(23px,3.2vw,32px); line-height:1.15; margin:0 0 14px;
  font-weight:600; letter-spacing:-.01em; text-wrap:balance; }}
h2 {{ font-family:var(--mono); font-size:13px; font-weight:600; letter-spacing:.04em;
  margin:30px 0 10px; padding-bottom:7px; border-bottom:1px solid var(--rule); }}
h3 {{ font-family:var(--mono); font-size:12.5px; margin:0 0 2px; font-weight:600; }}
p {{ margin:0 0 14px; max-width:68ch; }}
.lede {{ font-size:16px; color:var(--muted); }}
.row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px; }}
.panel {{ margin:0; background:var(--surface); border:1px solid var(--rule); border-radius:3px;
  padding:11px 11px 4px; }}
.score {{ font-family:var(--mono); font-size:10.5px; color:var(--muted); margin:0 0 4px; }}
.score b {{ color:var(--ink); }}
svg {{ width:100%; height:auto; display:block; }}
.grid {{ stroke:var(--rule); stroke-width:1; }}
.tick {{ font-family:var(--mono); font-size:8.5px; fill:var(--muted); text-anchor:end; }}
.tick.mid {{ text-anchor:middle; }}
.thr {{ stroke:var(--thr); stroke-width:1.4; stroke-dasharray:4 3; }}
.ln {{ fill:none; stroke-width:2; stroke-linejoin:round; stroke-linecap:round; }}
.dot {{ stroke:var(--surface); stroke-width:1.5; }}
.s0 {{ stroke:var(--s0); }} .s1 {{ stroke:var(--s1); }} .s2 {{ stroke:var(--s2); }}
circle.s0 {{ fill:var(--s0); }} circle.s1 {{ fill:var(--s1); }} circle.s2 {{ fill:var(--s2); }}
span.s0 {{ color:var(--s0); font-weight:600; }} span.s1 {{ color:var(--s1); font-weight:600; }}
span.s2 {{ color:var(--s2); font-weight:600; }}
.key {{ display:flex; gap:18px; flex-wrap:wrap; font-family:var(--mono); font-size:11.5px;
  align-items:center; margin:18px 0 4px; }}
.key i {{ width:16px; height:2px; display:inline-block; vertical-align:middle; margin-right:6px; }}
.key .thrk {{ border-top:2px dashed var(--thr); width:16px; display:inline-block;
  vertical-align:middle; margin-right:6px; }}
.note {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--thr);
  border-radius:3px; padding:13px 15px; margin:24px 0; }}
.note p {{ margin:0 0 8px; font-size:14px; }} .note p:last-child {{ margin:0; }}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>
<div class="wrap">
  <span class="eyebrow">30 problems per condition · τ = 1.5% · budget 10</span>
  <h1>How close each model gets to the threshold,<br/>iteration by iteration</h1>
  <p class="lede">Every line is the mean distance from the passing threshold across the 10 problems of
  one fault type. Lower is better; the dashed line is the threshold, and a repair passes below it.
  The top row is what a model that actually converges looks like — the two rows beneath it are the
  same open model under three different prompts.</p>

  <div class="key">
    <span><i style="background:var(--s0)"></i>translate</span>
    <span><i style="background:var(--s1)"></i>rotate</span>
    <span><i style="background:var(--s2)"></i>scale</span>
    <span><span class="thrk"></span>pass threshold (1× tolerance)</span>
    <span style="color:var(--muted)">y-axis: multiples of tolerance · x-axis: iteration 1–10</span>
  </div>

  {body}

  <div class="note">
    <p><b>Modality decides which faults a model can fix, and it decides differently for
    each model.</b> robotics-er-2 fixes <b>10/10</b> rotations from images and <b>0/10</b> from text.
    gemini-3.1-pro runs the other way on translation — <b>0/10</b> from images, <b>6/10</b> from text —
    while its rotation score falls from 7/10 to 2/10. Same faults, same budget; only the observation
    changed. Neither modality dominates, so a single-view harness understates both models.</p>
    <p><b>The three Qwen prompts are indistinguishable.</b> Showing the error in millimetres, and
    stating the typical fault magnitude, both leave the traces flat — even though the fault-scale hint
    verifiably moved the emitted magnitudes into the correct range for scale faults.</p>
  </div>

  <p>Later iterations average over fewer problems, since an episode that commits early stops
  contributing; point counts are in the tooltips. Distance is in multiples of each problem's own
  tolerance because τ varies from 17 to 28 mm across these 30 fridges.</p>
</div>'''

open('/home/sammathew/Code/FixIt/updatesAug12/convergence_all.html', 'w').write(page)
print("written", round(len(page) / 1024, 1), "KB")
