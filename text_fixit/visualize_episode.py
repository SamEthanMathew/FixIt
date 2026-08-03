#!/usr/bin/env python
"""
Visualise ONE episode: for every action the agent took, reconstruct the fridge with that fix
applied and render the target door CLOSING (90 deg -> shut, the motion the physical gate scores),
then stitch the turns together so you can watch what the agent changed and how it played out.

Reconstructs each turn's URDF from the saved trajectory (runs/<run>/<agent>/records.jsonl) -- no
extra model calls. Outputs an animated GIF (turns concatenated) and a static filmstrip PNG
(one row per turn, columns = closing angles).

    python text_fixit/visualize_episode.py --run iter1 --agent loop_gemini \
        --id 12050_link_2_translate_2 --split test
"""
import argparse
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
from PIL import Image                    # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import action_parser                     # noqa: E402
import canonical                         # noqa: E402
import corruption as corr                # noqa: E402
import render as R                       # noqa: E402
from part_table import build_part_table  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BG, INK = "#fcfcfb", "#0b0b0b"
FIGSIZE, DPI = (5.4, 5.9), 100
RES = 460
OPEN_DEG = 90.0
FRAMES_PER = 5                            # closing frames per turn


def _abs(pth):
    return pth if os.path.isabs(pth) else os.path.join(HERE, pth)


def _inject_canonical(spec, urdf):
    if spec["type"] == "rotate":
        return dict(spec, centroid=canonical.part_centroid(urdf, spec["link"]))
    if spec["type"] == "scale":
        return dict(spec, pivot=canonical.scale_pivot(urdf, spec["link"], spec["axis"]))
    return spec


def _candidate_urdf(broken, action_str, id_map, tag):
    """Apply one recorded action to the broken URDF -> candidate path (None-op for NO_FIX)."""
    res = action_parser.parse(f"<act>COMMIT {action_str}</act>", id_map)
    if not res["valid"] or res["action"]["type"] == "no_fix":
        return broken, None
    spec = _inject_canonical(res["action"]["spec"], broken)
    out = corr.apply(broken, spec, f"_viz_{tag}.urdf")
    return out, out


def _scene_frames(urdf, joint, center, dist):
    angles = [math.radians(OPEN_DEG) * (1 - i / (FRAMES_PER - 1)) for i in range(FRAMES_PER)]
    return [R.render_urdf(urdf, joint, a, center, dist, res=RES, yaw=-45, pitch=-30) for a in angles], angles


def build(rec_inst, record, out_gif, out_png):
    broken = _abs(rec_inst["broken_urdf"])
    healthy = _abs(rec_inst["healthy_urdf"])
    joint = rec_inst["joint"]
    _, id_map = build_part_table(broken)
    center, dist = R.camera_from_urdf(healthy)

    # scene list: initial broken, then one per recorded action
    scenes = [{"label": "Initial broken", "action": None,
               "dev": rec_inst["broken_deviation_mm"], "pass": False, "urdf": broken, "tmp": None}]
    for k, h in enumerate(record["history"]):
        urdf, tmp = _candidate_urdf(broken, h["action"], id_map, f"{record['agent']}_{k}")
        scenes.append({"label": f"{h['mode']} #{k+1}", "action": h["action"],
                       "dev": h["deviation_mm"], "pass": h["pass"], "urdf": urdf, "tmp": tmp})

    # render every scene's closing rollout
    for s in scenes:
        s["frames"], s["angles"] = _scene_frames(s["urdf"], joint, center, dist)
        if s["tmp"] and os.path.exists(s["tmp"]):
            os.remove(s["tmp"])

    _write_gif(rec_inst, record, scenes, out_gif)
    _write_filmstrip(rec_inst, record, scenes, out_png)
    return out_gif, out_png


def _caption(rec_inst, s):
    act = s["action"] or "(no change)"
    verdict = "PASS" if s["pass"] else "fail"
    return (f"{rec_inst['id']}  ·  gt={rec_inst['corruption']['type']}\n"
            f"{s['label']}: {act}  ·  dev={s['dev']:.0f} mm  ·  {verdict}")


def _write_gif(rec_inst, record, scenes, out_gif):
    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0.04, 1, 0.85])
    frames = []
    for s in scenes:
        colour = "#2a7" if s["pass"] else ("#a33" if s["dev"] > rec_inst["tau_mm"] else INK)
        for t, img in enumerate(s["frames"]):
            ax.clear()
            ax.imshow(img)
            ax.set_axis_off()
            ax.set_title(_caption(rec_inst, s), fontsize=10.5, color=INK, pad=6)
            ax.text(0.5, -0.03, f"door {math.degrees(s['angles'][t]):.0f}° open  ·  closing",
                    transform=ax.transAxes, ha="center", fontsize=10, color=colour)
            fig.canvas.draw()
            frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()))
    plt.close(fig)
    # hold the last frame of each scene a touch longer so each turn reads
    dur = []
    for si, s in enumerate(scenes):
        dur += [260] * (FRAMES_PER - 1) + [900]
    os.makedirs(os.path.dirname(out_gif), exist_ok=True)
    frames[0].save(out_gif, save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
    print(f"  gif -> {out_gif}  ({len(frames)} frames, {len(scenes)} turns)")


def _write_filmstrip(rec_inst, record, scenes, out_png):
    rows, cols = len(scenes), FRAMES_PER
    cell = 190
    capw = 360
    pad = 8
    W = capw + cols * cell + pad * 2
    H = rows * cell + pad * 2
    canvas = Image.new("RGB", (W, H), (252, 252, 251))
    from PIL import ImageDraw
    d = ImageDraw.Draw(canvas)
    for r, s in enumerate(scenes):
        y = pad + r * cell
        verdict = "PASS" if s["pass"] else "fail"
        cap = (f"{s['label']}\n{(s['action'] or '(no change)')}\n"
               f"dev={s['dev']:.0f}mm  {verdict}")
        d.multiline_text((pad, y + cell // 3), cap, fill=(11, 11, 11), spacing=4)
        for c, img in enumerate(s["frames"]):
            im = img.resize((cell, cell))
            canvas.paste(im, (capw + pad + c * cell, y))
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    canvas.save(out_png)
    print(f"  filmstrip -> {out_png}  ({rows} turns x {cols} closing frames)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="iter1")
    ap.add_argument("--agent", default="loop_gemini")
    ap.add_argument("--id", default=None, help="instance id (default: first solved, else first)")
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", default=os.path.join(HERE, "runs", "gallery"))
    args = ap.parse_args()

    recs = [json.loads(l) for l in
            open(os.path.join(HERE, "runs", args.run, args.agent, "records.jsonl"))]
    insts = {json.loads(l)["id"]: json.loads(l) for l in
             open(os.path.join(HERE, "data", f"instances_{args.split}.jsonl"))}
    if args.id:
        record = next(r for r in recs if r["id"] == args.id)
    else:
        record = next((r for r in recs if r["terminal_pass"]), recs[0])
    rec_inst = insts[record["id"]]
    print(f"episode {record['id']}  agent={record['agent']}  turns={len(record['history'])}  "
          f"terminal_pass={record['terminal_pass']}")
    build(rec_inst, record,
          os.path.join(args.out, f"episode_{record['agent']}_{record['id']}.gif"),
          os.path.join(args.out, f"episode_{record['agent']}_{record['id']}.png"))


if __name__ == "__main__":
    main()
