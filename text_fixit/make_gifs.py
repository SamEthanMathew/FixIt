#!/usr/bin/env python
"""
Error GIFs for the broken-fridge instances, in the house style of visualizations/7_error_*.gif.

Same look as the point-cloud originals -- 540x590 canvas, isometric view, axes off, 10 frames
with the final state held, 2.5 fps, two-line title plus a `frame t/10` footer -- but the frames
are PyBullet MESH renders instead of point-cloud scatter.

Deliberate difference: these animate the door CLOSING (90 deg -> shut) rather than the dataset's
opening rollout, because closing is the motion the physical gate evaluates, so the animation
actually shows the failure. Camera framing is computed once from the healthy shape and reused for
every frame (the mesh analogue of the originals' shared-extent cube), so nothing rescales.

    python text_fixit/make_gifs.py [--split test]
"""
import argparse
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
import numpy as np                                    # noqa: E402
from PIL import Image                                 # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# House style (visualizations/error_gifs_blue.py)
BG, INK, SEC = "#fcfcfb", "#0b0b0b", "#52514e"
FIGSIZE, DPI = (5.4, 5.9), 100                        # -> 540 x 590 px
NFRAMES, FPS, HOLD = 10, 2.5, 3
RES = 520                                             # render resolution per frame
OPEN_DEG = 90.0


def _label(spec):
    ax = "xyz"[spec["axis"]]
    if spec["type"] == "translate":
        return f"translate {ax} {spec['value']:+.3f} m"
    if spec["type"] == "rotate":
        return f"rotate {ax} {math.degrees(spec['value']):+.0f}deg"
    return f"scale {ax} x{spec['value']:.2f}"


def make_gif(rec, out_path, healthy=False):
    """Render one closing animation. `healthy` renders the intact fridge (the no-error case)."""
    hu = os.path.join(HERE, rec["healthy_urdf"])
    urdf = hu if healthy else os.path.join(HERE, rec["broken_urdf"])
    jn = rec["joint"]
    center, dist = R.camera_from_urdf(hu)             # framed once, from the healthy shape

    angles = [math.radians(OPEN_DEG) * (1 - i / (NFRAMES - 1)) for i in range(NFRAMES)]
    imgs = [R.render_urdf(urdf, jn, a, center, dist, res=RES, yaw=-45, pitch=-30) for a in angles]

    if healthy:
        title = f"fridge {rec['base']} — no error"
        sub = (f"intact {rec['part_name']} · deviation 0 mm (tau {rec['tau_mm']:.0f} mm) · "
               f"closes: yes")
        colour = SEC
    else:
        title = f"fridge {rec['base']} — {rec['corruption']['type']} error"
        sub = (f"GT fix: {_label(rec['gt_fix'])} · deviation {rec['broken_deviation_mm']:.0f} mm "
               f"(tau {rec['tau_mm']:.0f} mm) · closes: {'no' if not rec['closes_broken'] else 'yes'}")
        colour = "#a33" if not rec["closes_broken"] else SEC

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0.04, 1, 0.86])
    ax.set_facecolor(BG)

    # Compose each PyBullet render into the matplotlib figure (so the typography matches the
    # point-cloud originals), then grab the canvas as a PIL frame.
    frames = []
    for t in range(NFRAMES):
        ax.clear()
        ax.imshow(imgs[t])
        ax.set_axis_off()
        ax.set_title(f"{title}\n{sub}", fontsize=10.5, color=INK, pad=6)
        ax.text(0.5, -0.03, f"frame {t+1}/{NFRAMES}   ·   door {math.degrees(angles[t]):.0f}° open",
                transform=ax.transAxes, ha="center", fontsize=10, color=colour)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()))
    plt.close(fig)

    # Write with explicit per-frame durations. matplotlib's PillowWriter did not honour fps here
    # (every frame came out 1600 ms), so the GIF is written directly: 400 ms per frame with the
    # final state held for HOLD extra frames, matching visualizations/7_error_*.gif.
    step_ms = int(1000 / FPS)
    durations = [step_ms] * (NFRAMES - 1) + [step_ms * (HOLD + 1)]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    print(f"  {os.path.basename(out_path)}")
    return out_path


def pick(instances, ctype):
    """Prefer an instance whose break also stops the door closing -- the animation then shows a
    real jam rather than a merely mis-shaped door."""
    cands = [r for r in instances if r["corruption"]["type"] == ctype]
    if not cands:
        return None
    return sorted(cands, key=lambda r: (r["closes_broken"], -r["broken_deviation_mm"]))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", default=os.path.join(HERE, "runs", "gallery"))
    args = ap.parse_args()

    instances = [json.loads(l) for l in open(os.path.join(HERE, "data", f"instances_{args.split}.jsonl"))]
    print(f"Building GIFs from {len(instances)} {args.split} instances:")
    for ctype in ("scale", "translate", "rotate"):
        rec = pick(instances, ctype)
        if rec:
            make_gif(rec, os.path.join(args.out, f"error_{ctype}.gif"))
    healthy_ref = pick(instances, "rotate") or instances[0]
    make_gif(healthy_ref, os.path.join(args.out, "no_error.gif"), healthy=True)


if __name__ == "__main__":
    main()
