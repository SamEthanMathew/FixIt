#!/usr/bin/env python
"""
Per-run diagnostics: what each condition found, and what it did with it.

Two views the aggregate charts cannot give:

  BEST vs COMMITTED   one point per problem. x = closest the model ever came, y = what it actually
                      committed, both in multiples of that problem's tolerance. Every point sits on
                      or above the diagonal (you cannot commit better than your best). The quadrant
                      that matters is x <= 1 < y: a repair the model FOUND and then threw away.

  DIAGNOSIS GRID      one row per problem, four columns — did it ever target the right part, use the
                      right action type, the right axis, and size the correction to within 25%.
                      The aggregate funnel says "44% got the axis"; this says WHICH problems, which
                      is what an SFT curriculum is built from.

    python text_fixit/viz_per_run.py --out updatesAug12/per_run_diagnostics.html
"""
import argparse
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
CALL = re.compile(r"(TRANSLATE|ROTATE|SCALE)\((P\d+),\s*([XYZ]),\s*(-?[\d.]+)\)")

ORDER = [("er_image", "robotics-er-2 · image"), ("g3_image", "gemini-3.1-pro · image"),
         ("er_text", "robotics-er-2 · text"), ("g3_text", "gemini-3.1-pro · text"),
         ("qw8_image", "Qwen-8B · image"), ("qw8_text", "Qwen-8B · text"),
         ("dev_qw8_image", "Qwen-8B · image + error shown"),
         ("dev_qw8_text", "Qwen-8B · text + error shown"),
         ("scale_qw8_image", "Qwen-8B · image + fault scale"),
         ("scale_qw8_text", "Qwen-8B · text + fault scale")]


def load(cond):
    """Per problem: closest approach, committed, and which diagnosis stages were ever reached."""
    out = []
    for f in sorted(glob.glob(os.path.join(RUNS, f"one_error_{cond}", "*", "records.jsonl"))):
        lines = open(f).read().splitlines()
        if not lines:
            continue
        r = json.loads(lines[0])
        if not r.get("history"):
            continue
        g = CALL.search(r.get("gt_fix_actions") or "")
        hit = {"part": False, "type": False, "axis": False, "mag": False}
        if g:
            gt_t, gt_p, gt_ax, gt_v = g.group(1), g.group(2), g.group(3), abs(float(g.group(4)))
            best = None
            for h in r["history"]:
                for m in CALL.finditer(h.get("action") or ""):
                    if m.group(2) == gt_p:
                        hit["part"] = True
                        if m.group(1) == gt_t:
                            hit["type"] = True
                        if m.group(3) == gt_ax:
                            hit["axis"] = True
                        if m.group(1) == gt_t and m.group(3) == gt_ax and gt_v:
                            rr = abs(float(m.group(4))) / gt_v
                            if best is None or abs(rr - 1) < abs(best - 1):
                                best = rr
            hit["mag"] = best is not None and 0.75 <= best <= 1.25
        out.append({
            "id": r["id"], "type": r["corruption_type"], "passed": r["terminal_pass"],
            "best": min(h["deviation_over_tau"] for h in r["history"]),
            "final": r["terminal_deviation_over_tau"], "iters": r["n_simulate"], "hit": hit,
        })
    return out


SW, SH, SP = 250, 250, 34
XMAX = 12.0


def sxy(v):
    v = min(max(v, 0.4), XMAX)
    import math
    lo, hi = math.log(0.4), math.log(XMAX)
    return SP + (SW - SP - 10) * (math.log(v) - lo) / (hi - lo)


def scatter(rows):
    t = sxy(1.0)
    # Two distinct failures, and they turned out to differ sharply:
    #   disc  — committed something worse than a state that ALREADY PASSED. Zero, everywhere.
    #   worse — committed worse than its own best attempt, passing or not. Common.
    disc = sum(1 for r in rows if r["best"] <= 1 < r["final"])
    worse = sum(1 for r in rows if r["final"] > r["best"] * 1.10)
    pts = ""
    for r in rows:
        x, y = sxy(r["best"]), SH - SP - (sxy(r["final"]) - SP)
        cls = "ok" if r["passed"] else ("lost" if r["best"] <= 1 else "miss")
        pts += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="pt {cls}">'
                f'<title>{r["id"]} ({r["type"]}) — best {r["best"]:.2f}×, committed '
                f'{r["final"]:.2f}×, {r["iters"]} iterations</title></circle>')
    ax = "".join(
        f'<text x="{sxy(v):.1f}" y="{SH-SP+14:.0f}" class="tk mid">{v:g}×</text>'
        f'<text x="{SP-6:.0f}" y="{SH-SP-(sxy(v)-SP)+3:.1f}" class="tk">{v:g}×</text>'
        for v in (1, 3, 10))
    return f'''<svg viewBox="0 0 {SW} {SH}" role="img" aria-label="Best reached versus committed">
  <rect x="{SP}" y="{SH-SP-(t-SP):.1f}" width="{t-SP:.1f}" height="{t-SP:.1f}" class="zone"/>
  <line x1="{SP}" y1="{SH-SP}" x2="{SW-10}" y2="{SP-SW+SH-10:.1f}" class="diag"/>
  <line x1="{t:.1f}" y1="{SP-14}" x2="{t:.1f}" y2="{SH-SP}" class="thr"/>
  <line x1="{SP}" y1="{SH-SP-(t-SP):.1f}" x2="{SW-10}" y2="{SH-SP-(t-SP):.1f}" class="thr"/>
  {ax}{pts}
  <text x="{SW/2:.0f}" y="{SH-4}" class="tk mid">closest reached →</text>
  <text x="10" y="{SH/2:.0f}" class="tk" transform="rotate(-90 10 {SH/2:.0f})"
        text-anchor="middle">committed →</text>
</svg><p class="sub">{disc} discarded a <b>passing</b> state · {worse}/{len(rows)} committed worse
than their own best attempt</p>'''


def grid(rows):
    cols = [("part", "part"), ("type", "type"), ("axis", "axis"), ("mag", "size")]
    body = ""
    for r in sorted(rows, key=lambda r: (not r["passed"], r["type"], r["id"])):
        cells = "".join(
            f'<td class="{"y" if r["hit"][k] else "n"}">{"✓" if r["hit"][k] else "✗"}</td>'
            for k, _ in cols)
        body += (f'<tr><td class="pid">{r["id"].replace("_ctrl","").replace("_0","")}</td>'
                 f'<td class="ty">{r["type"][:5]}</td>{cells}'
                 f'<td class="res {"p" if r["passed"] else "f"}">'
                 f'{"PASS" if r["passed"] else f"{r['final']:.1f}×"}</td></tr>')
    head = "".join(f"<th>{lab}</th>" for _, lab in cols)
    return (f'<table class="dg"><thead><tr><th></th><th></th>{head}<th>result</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="updatesAug12/per_run_diagnostics.html")
    a = ap.parse_args()

    secs = ""
    for cond, label in ORDER:
        if not os.path.exists(os.path.join(RUNS, f"one_error_{cond}", "summary.json")):
            continue
        rows = load(cond)
        if not rows:
            continue
        k = sum(1 for r in rows if r["passed"])
        found = sum(1 for r in rows if r["best"] <= 1)
        secs += (f'<section><h2>{label}</h2>'
                 f'<p class="score"><b>{k}/{len(rows)}</b> solved · '
                 f'{found} reached a passing state at some point</p>'
                 f'<div class="two"><div class="c">{scatter(rows)}</div>'
                 f'<div class="c">{grid(rows)}</div></div></section>')

    page = f'''<title>Per-Run Diagnostics</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
:root {{ --ground:#F4F2ED; --surface:#FCFCFB; --ink:#1A1B19; --muted:#6C6F68; --rule:#E2DFD7;
  --thr:#9C3328; --ok:#2E6B4A; --lost:#C2620E; --miss:#8A8D86;
  --mono:ui-monospace,"SFMono-Regular","JetBrains Mono",Menlo,Consolas,monospace;
  --serif:"Iowan Old Style",Charter,Georgia,"Times New Roman",serif; }}
@media (prefers-color-scheme:dark) {{ :root:not([data-theme="light"]) {{
  --ground:#131412; --surface:#1A1A19; --ink:#ECEAE3; --muted:#9A9E95; --rule:#2C2F2A;
  --thr:#E08A7E; --ok:#6FBF92; --lost:#CF7020; --miss:#6E726A; }} }}
:root[data-theme="dark"] {{ --ground:#131412; --surface:#1A1A19; --ink:#ECEAE3; --muted:#9A9E95;
  --rule:#2C2F2A; --thr:#E08A7E; --ok:#6FBF92; --lost:#CF7020; --miss:#6E726A; }}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--serif);line-height:1.6}}
.wrap{{max-width:1000px;margin:0 auto;padding:44px 22px 72px}}
.eyebrow{{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);display:block;margin-bottom:10px}}
h1{{font-family:var(--mono);font-size:clamp(22px,3vw,30px);margin:0 0 14px;font-weight:600;
  letter-spacing:-.01em;text-wrap:balance;line-height:1.15}}
h2{{font-family:var(--mono);font-size:14px;font-weight:600;margin:0 0 2px}}
p{{margin:0 0 14px;max-width:68ch}} .lede{{font-size:16px;color:var(--muted)}}
section{{background:var(--surface);border:1px solid var(--rule);border-radius:3px;padding:16px;
  margin:16px 0}}
.score{{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin:0 0 10px}}
.score b{{color:var(--ink)}}
.two{{display:grid;grid-template-columns:minmax(250px,300px) 1fr;gap:20px;align-items:start}}
@media(max-width:760px){{.two{{grid-template-columns:1fr}}}}
svg{{width:100%;height:auto;display:block;font-family:var(--mono)}}
.zone{{fill:var(--ok);opacity:.09}}
.diag{{stroke:var(--rule);stroke-width:1}}
.thr{{stroke:var(--thr);stroke-width:1.2;stroke-dasharray:3 3}}
.tk{{font-size:9px;fill:var(--muted);text-anchor:end}} .tk.mid{{text-anchor:middle}}
.pt{{stroke:var(--surface);stroke-width:1.2}}
.pt.ok{{fill:var(--ok)}} .pt.lost{{fill:var(--lost)}} .pt.miss{{fill:var(--miss)}}
.sub{{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin:6px 0 0}}
table.dg{{border-collapse:collapse;font-family:var(--mono);font-size:10.5px;width:100%}}
.dg th{{font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  padding:3px 4px;font-weight:600}}
.dg td{{padding:2px 4px;text-align:center;border-bottom:1px solid var(--rule)}}
.dg td.pid{{text-align:left;color:var(--muted);font-size:9.5px}}
.dg td.ty{{text-align:left;color:var(--muted)}}
.dg td.y{{color:var(--ok);font-weight:700}} .dg td.n{{color:var(--miss)}}
.dg td.res{{text-align:right;font-weight:600}} .dg td.res.p{{color:var(--ok)}}
.dg td.res.f{{color:var(--muted)}}
.key{{display:flex;gap:16px;flex-wrap:wrap;font-family:var(--mono);font-size:11px;margin:16px 0 0}}
.key i{{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:5px}}
</style>
<div class="wrap">
  <span class="eyebrow">One point, and one row, per problem</span>
  <h1>What each run found — and what it did with it</h1>
  <p class="lede">Left: how close the model ever came, against what it finally committed. Points can
  only sit on or above the diagonal, because you cannot commit better than your best attempt. The
  shaded corner is success. Right: for every problem, whether the model ever identified the correct
  part, action type, axis, and magnitude.</p>
  <p><b>No model ever discarded a passing repair</b> — in all nine runs, "ever reached threshold"
  equals "solved" exactly. Commit policy is not a failure mode here; the loop commits what it finds.
  Models do routinely commit worse than their own <em>best</em> attempt (6–13 problems per run), but
  those bests were never good enough to pass anyway, so it costs nothing on this benchmark.</p>
  <div class="key">
    <span><i style="background:var(--ok)"></i>solved</span>
    <span><i style="background:var(--lost)"></i>found a passing state, committed worse</span>
    <span><i style="background:var(--miss)"></i>never reached threshold</span>
    <span style="color:var(--muted)">both axes: multiples of tolerance, log scale</span>
  </div>
  {secs}
</div>'''
    out = a.out if os.path.isabs(a.out) else os.path.join(os.path.dirname(HERE), a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(page)
    print(f"-> {out}  ({len(page)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
