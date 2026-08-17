#!/usr/bin/env python
"""Measure ONLY the bottleneck: can a model name the fault's type and axis from our renders?

The full loop conflates four things -- perception, output format, search strategy, and magnitude
calibration. std30 showed Qwen3-VL-8B failing at the first one (fault TYPE 39% against 33% chance,
AXIS 36% against 33%), so evaluating a candidate model by running the whole loop is slow and
ambiguous: a 30-problem run costs an hour and still cannot tell you WHICH stage improved.

This asks one question per problem, from the same turn-1 images the agent sees, and scores the
answer against ground truth. One call per problem instead of ten, no loop, no action grammar, no
magnitude. If a model cannot beat chance here it cannot do the task, and that is worth knowing
before downloading 50 GB of weights.

    # local vLLM (OpenAI-compatible)
    python text_fixit/perception_probe.py --base-url http://127.0.0.1:8001/v1 \
        --model Qwen/Qwen3-VL-8B-Instruct

    # any other OpenAI-compatible endpoint
    python text_fixit/perception_probe.py --base-url https://... --model ... --api-key-env MY_KEY

    # google genai (reference ceiling)
    python text_fixit/perception_probe.py --provider gemini --model gemini-3.1-pro-preview

Images come from an existing run tree (--from-run), so the probe compares models on byte-identical
inputs rather than on fresh renders.
"""
import argparse
import base64
import glob
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CALL = re.compile(r"(TRANSLATE|ROTATE|SCALE)\((P\d+),\s*([XYZ]),\s*(-?[\d.]+)\)")
TYPE_WORD = {"TRANSLATE": "MISPLACED", "ROTATE": "MISTURNED", "SCALE": "MIS-SIZED"}

QUESTION = """You are shown two rendered views of the same refrigerator, doors closed.
Image 1 labels each repairable door with its part id (P0, P1, ...).
Image 2 is the object in its CURRENT, FAULTY state.

Exactly one part is faulty. It is wrong in exactly one of three ways:
  MISPLACED  - correct size and squarely aligned, but shifted off to one side.
  MISTURNED  - correct size and roughly the right place, but tilted, so its edges are no longer
               parallel to the body's and the gap it leaves is a wedge.
  MIS-SIZED  - its proportions differ from the other door or from the opening it must fill.

{legend}
{table}

Answer with exactly one line and nothing else:
PART=<P#> FAULT=<MISPLACED|MISTURNED|MIS-SIZED> AXIS=<X|Y|Z>
"""

QUESTION_IMG = """You are shown two rendered views of the same refrigerator, doors closed.
Image 1 labels each repairable door with its part id (P0, P1, ...).
Image 2 is the object in its CURRENT, FAULTY state.

Exactly one part is faulty. It is wrong in exactly one of three ways:
  MISPLACED  - correct size and squarely aligned, but shifted off to one side.
  MISTURNED  - correct size and roughly the right place, but tilted, so its edges are no longer
               parallel to the body's and the gap it leaves is a wedge.
  MIS-SIZED  - its proportions differ from the other door or from the opening it must fill.

Describe the error using the PICTURE only. Do not use X, Y or Z. Pick the direction, as seen on
screen, along which the faulty part is wrong:
  UPDOWN     - it is too high or too low, or too tall or too short (vertical on screen)
  LEFTRIGHT  - it is shifted or stretched across the face of the door (horizontal on screen)
  INOUT      - it is too far forward or back, or too thick or thin (toward or away from you)

{table}

Answer with exactly one line and nothing else:
PART=<P#> FAULT=<MISPLACED|MISTURNED|MIS-SIZED> DIR=<UPDOWN|LEFTRIGHT|INOUT>
"""

ANS_IMG = re.compile(r"PART\s*=\s*(P\d+).*?FAULT\s*=\s*([A-Z-]+).*?DIR\s*=\s*([A-Z]+)",
                     re.IGNORECASE | re.DOTALL)

ANS = re.compile(r"PART\s*=\s*(P\d+).*?FAULT\s*=\s*([A-Z-]+).*?AXIS\s*=\s*([XYZ])",
                 re.IGNORECASE | re.DOTALL)


def _abs(path):
    """Instance URDF paths are stored relative to text_fixit/, not to the cwd."""
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode("ascii")


def episodes(run, instances):
    """(instance, [img_paths]) for every episode of `run` that has turn-1 images."""
    by_id = {json.loads(l)["id"]: json.loads(l) for l in open(instances)}
    out = []
    for d in sorted(glob.glob(os.path.join(HERE, "runs", run, "*", ""))):
        eid = os.path.basename(os.path.dirname(d))
        if eid not in by_id:
            continue
        imgs = sorted(glob.glob(os.path.join(d, "images", eid, "t01_*.png")))
        if len(imgs) >= 2:
            out.append((by_id[eid], imgs[:2]))
    return out


def ask_openai(base_url, model, key, text, imgs, timeout):
    import requests
    content = [{"type": "text", "text": text}]
    content += [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(p)}"}}
                for p in imgs]
    h = {"Authorization": f"Bearer {key}"} if key else {}
    r = requests.post(f"{base_url.rstrip('/')}/chat/completions", headers=h, timeout=timeout,
                      json={"model": model, "temperature": 0.0, "max_tokens": 200,
                            "messages": [{"role": "user", "content": content}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def ask_gemini(model, text, imgs, timeout):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["RPAD_GEMINI_API_KEY"])
    parts = [types.Part.from_text(text=text)]
    parts += [types.Part.from_bytes(data=open(p, "rb").read(), mime_type="image/png") for p in imgs]
    r = client.models.generate_content(model=model, contents=parts)
    return r.text or ""


def screen_dir_to_axis(urdf, id_map, center, dist, hard=False):
    """{"UPDOWN": "Y", "LEFTRIGHT": "X", "INOUT": "Z"} for THIS instance, derived from the camera.

    Computed the same way as views.axis_image_legend -- project each object axis onto the camera
    basis and label it by which screen direction dominates -- so it stays correct under a different
    camera (hard=True swings the yaw 80 degrees) and for any asset."""
    import numpy as np
    import views
    links = [pt["link"] for pt in id_map.values() if pt.get("corruptible")]
    axes = views._link_axes_world(urdf, links[0])
    yaw = views.HARD_YAW if hard else views.EASY_YAW
    right, up, toward = views._camera_basis(center, dist, yaw, -30)
    out = {}
    for name, v in zip("XYZ", axes):
        r, u, t = (float(np.dot(v, right)), float(np.dot(v, up)), float(np.dot(v, toward)))
        best = max((abs(u), "UPDOWN"), (abs(r), "LEFTRIGHT"), (abs(t), "INOUT"))[1]
        out.setdefault(best, name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="openai", choices=["openai", "gemini"])
    ap.add_argument("--base-url", default="http://127.0.0.1:8001/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key-env", default=None)
    ap.add_argument("--from-run", default="strict_qw8_image")
    ap.add_argument("--instances", default=os.path.join(HERE, "data", "instances_std30.jsonl"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-legend", action="store_true", help="withhold the axis->image legend")
    ap.add_argument("--no-table", action="store_true", help="withhold the part table")
    ap.add_argument("--frame", default="object", choices=["object", "image"],
                    help="object: ask for X/Y/Z directly. image: ask for a screen direction "
                         "and convert to an axis here.")
    ap.add_argument("--res", type=int, default=0,
                    help="re-render the views at this resolution instead of reusing the run tree's "
                         "768px PNGs. The fault spans ~1.1 vision tokens at 768; raising this is the "
                         "only way to give the encoder more evidence per centimetre.")
    ap.add_argument("--margin", type=float, default=0,
                    help="camera framing margin (render.camera_from_urdf default 1.7). Lower = "
                         "tighter crop = more pixels on the object.")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import views, render as R
    from part_table import build_part_table

    eps = episodes(args.from_run, args.instances)
    if args.limit:
        eps = eps[:args.limit]
    if not eps:
        sys.exit(f"no episodes with turn-1 images under runs/{args.from_run}/")

    key = os.environ.get(args.api_key_env, "") if args.api_key_env else ""
    rows, hit, conf = [], Counter(), Counter()

    for inst, imgs in eps:
        table, id_map = build_part_table(_abs(inst["broken_urdf"]))
        if args.res:
            # Re-render rather than reuse the cached 768px views, so resolution and framing are the
            # only things that change. Same camera code path the env uses.
            kw = {"margin": args.margin} if args.margin else {}
            cc, dd = R.camera_from_urdf(_abs(inst["healthy_urdf"]), **kw)
            ann = views.annotated_part_view(_abs(inst["broken_urdf"]), id_map, cc, dd, res=args.res)
            cur = views.closed_view(_abs(inst["broken_urdf"]), cc, dd, id_map, res=args.res)[0]
            tmp = os.path.join(HERE, "runs", "_probe_tmp")
            os.makedirs(tmp, exist_ok=True)
            imgs = [os.path.join(tmp, f"{inst['id']}_a.png"), os.path.join(tmp, f"{inst['id']}_b.png")]
            ann.save(imgs[0]); cur.save(imgs[1])
        # gt_fix is a dict (or None on composites); gt_fix_actions lives only in run
        # records, never in the instance JSONL. Read the structured spec instead.
        if True:
            spec = inst["faults"][0]["spec"]
            gt_type = {"translate": "TRANSLATE", "rotate": "ROTATE", "scale": "SCALE"}[spec["type"]]
            gt_axis = "XYZ"[spec["axis"]]
            gt_part = next((p for p, v in id_map.items() if v["link"] == spec["link"]), "?")
        else:
            gt_type, gt_part, gt_axis = g.group(1), g.group(2), g.group(3)

        dirmap = {}
        if args.frame == "image":
            c, d = R.camera_from_urdf(_abs(inst["healthy_urdf"]))
            dirmap = screen_dir_to_axis(_abs(inst["broken_urdf"]), id_map, c, d)
        legend = ""
        if not args.no_legend and args.frame == "object":
            c, d = R.camera_from_urdf(_abs(inst["healthy_urdf"]))
            legend = views.axis_image_legend(_abs(inst["broken_urdf"]), id_map, c, d) or ""
        text = (QUESTION_IMG.format(table="" if args.no_table else table)
                if args.frame == "image"
                else QUESTION.format(legend=legend, table="" if args.no_table else table))

        try:
            raw = (ask_gemini(args.model, text, imgs, args.timeout) if args.provider == "gemini"
                   else ask_openai(args.base_url, args.model, key, text, imgs, args.timeout))
        except Exception as e:
            raw = f"<error: {type(e).__name__}: {e}>"

        if args.frame == "image":
            m = ANS_IMG.search(raw or "")
            p, f = (m.group(1).upper(), m.group(2).upper()) if m else ("?", "?")
            a = dirmap.get(m.group(3).upper(), "?") if m else "?"
        else:
            m = ANS.search(raw or "")
            p, f, a = (m.group(1).upper(), m.group(2).upper(), m.group(3).upper()) if m else ("?", "?", "?")
        ok_p, ok_t, ok_a = p == gt_part, f == TYPE_WORD[gt_type], a == gt_axis
        hit["part"] += ok_p; hit["type"] += ok_t; hit["axis"] += ok_a
        hit["all"] += ok_p and ok_t and ok_a
        hit["parsed"] += bool(m)
        conf[(gt_axis, a)] += 1
        rows.append({"id": inst["id"], "gt": f"{gt_type}({gt_part},{gt_axis})",
                     "said": f"{f}({p},{a})", "part": ok_p, "type": ok_t, "axis": ok_a,
                     "raw": (raw or "")[:200]})
        mark = "".join("+" if x else "." for x in (ok_p, ok_t, ok_a))
        print(f"  {inst['id'][:26]:28} gt {gt_type:9} {gt_axis}   said {f:10} {a}   {mark}")

    n = len(rows)
    pc = lambda k: 100 * hit[k] / n
    print(f"\n{args.model}   n={n}   (parsed {hit['parsed']}/{n})")
    print(f"  part  {pc('part'):5.1f}%     type  {pc('type'):5.1f}%  (chance 33.3)"
          f"     axis  {pc('axis'):5.1f}%  (chance 33.3)     all three {pc('all'):5.1f}%  (chance ~5.6)")
    print("\n  axis confusion (row = truth, col = said):")
    print("        " + "".join(f"{a:>5}" for a in "XYZ"))
    for gt in "XYZ":
        print(f"    {gt}   " + "".join(f"{conf.get((gt, e), 0):>5}" for e in "XYZ"))

    if args.out:
        json.dump({"model": args.model, "n": n, "hits": dict(hit), "rows": rows},
                  open(args.out, "w"), indent=1)
        print(f"\n  -> {args.out}")


if __name__ == "__main__":
    main()
