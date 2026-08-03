#!/usr/bin/env python
"""
Build contact sheets of the generated broken-fridge instances.

For a sample of instances: render HEALTHY | BROKEN (closed) | BROKEN (door open 90 deg),
all with identical camera framing, and tile them into a labelled grid per corruption type.

    python text_fixit/visualize_instances.py --split test --per-type 4
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CTYPES = ("scale", "translate", "rotate")
CELL = 300
PAD = 8
CAPTION_H = 34
HEADER_H = 58


def _font(size=13):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def pick(instances, ctype, n):
    """n instances of this corruption type, each from a distinct base shape."""
    seen, out = set(), []
    for r in instances:
        if r["corruption"]["type"] != ctype or r["base"] in seen:
            continue
        seen.add(r["base"])
        out.append(r)
        if len(out) == n:
            break
    return out


def sheet_for_type(instances, ctype, n, out_path):
    rows = pick(instances, ctype, n)
    if not rows:
        return None
    cols = ["healthy", "broken (closed)", "broken (open 90°)"]
    W = len(cols) * CELL + (len(cols) + 1) * PAD
    H = HEADER_H + len(rows) * (CELL + CAPTION_H + PAD) + PAD
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    f, fb = _font(13), _font(15)

    d.text((PAD, 8), f"Corruption type: {ctype.upper()}   "
                     f"(score = geometric similarity to healthy; 1.00 = perfect)",
           fill="black", font=fb)

    for i, rec in enumerate(rows):
        healthy = os.path.join(HERE, rec["healthy_urdf"])
        broken = os.path.join(HERE, rec["broken_urdf"])
        jn = rec["joint"]
        center, dist = R.camera_from_urdf(healthy)          # SAME framing for all three
        imgs = [
            R.render_urdf(healthy, jn, 0.0, center, dist, res=CELL),
            R.render_urdf(broken, jn, 0.0, center, dist, res=CELL),
            R.render_urdf(broken, jn, math.pi / 2, center, dist, res=CELL),
        ]
        y = HEADER_H + i * (CELL + CAPTION_H + PAD)
        for c, im in enumerate(imgs):
            x = PAD + c * (CELL + PAD)
            sheet.paste(im, (x, y))
            d.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline=(210, 210, 210))
            if i == 0:
                d.text((x + 4, y - 18), cols[c], fill=(90, 90, 90), font=f)
        cv = rec["corruption"]
        amt = (f"x{cv['value']:.2f}" if cv["type"] == "scale" else
               f"{math.degrees(cv['value']):+.0f}°" if cv["type"] == "rotate" else
               f"{cv['value']:+.3f}m")
        d.text((PAD, y + CELL + 4),
               f"fridge {rec['base']}  ·  part {rec['part_name']} ({rec['link']})  ·  "
               f"{cv['type']} axis-{'xyz'[cv['axis']]} {amt}",
               fill="black", font=f)
        d.text((PAD, y + CELL + 19),
               f"broken score {rec['broken_score']:.2f}  ·  error {rec['broken_error_mm']:.0f}mm  ·  "
               f"GT-fix restores to {rec['gt_fixed_score']:.2f}",
               fill=(120, 60, 60), font=f)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    print(f"  {ctype:10s} {len(rows)} instances -> {out_path}")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--per-type", type=int, default=4)
    args = ap.parse_args()

    src = os.path.join(HERE, "data", f"instances_{args.split}.jsonl")
    instances = [json.loads(l) for l in open(src)]
    out_dir = os.path.join(HERE, "runs", "gallery")
    print(f"Rendering galleries from {len(instances)} {args.split} instances:")
    for ctype in CTYPES:
        sheet_for_type(instances, ctype, args.per_type,
                       os.path.join(out_dir, f"gallery_{ctype}.png"))


if __name__ == "__main__":
    main()
