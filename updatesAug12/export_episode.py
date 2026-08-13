#!/usr/bin/env python
"""Export one episode from a run into a self-contained, non-ignored asset folder.

text_fixit/runs/ is gitignored, so report assets must be COPIED out. This keeps every artifact a
reader needs to audit a single episode: the run config, the episode record, every turn, the exact
rendered prompt per turn, every image actually attached, and the raw API metadata.
"""
import argparse, json, os, shutil, sys

def export(run, agent, episode_id, dest):
    src = os.path.join("text_fixit/runs", run, agent)
    os.makedirs(dest, exist_ok=True)
    shutil.copy(os.path.join(src, "manifest.json"), os.path.join(dest, "manifest.json"))

    rec = next(json.loads(l) for l in open(os.path.join(src, "records.jsonl"))
               if json.loads(l)["id"] == episode_id)
    json.dump(rec, open(os.path.join(dest, "record.json"), "w"), indent=2)

    turns = [json.loads(l) for l in open(os.path.join(src, "turns.jsonl"))
             if json.loads(l)["episode"] == episode_id]
    with open(os.path.join(dest, "turns.jsonl"), "w") as f:
        for t in turns:
            f.write(json.dumps(t) + "\n")

    for sub, pat in (("prompts", f"{episode_id}_t"), ("trajectories", f"{episode_id}.md")):
        s = os.path.join(src, sub)
        if not os.path.isdir(s):
            continue
        if sub == "prompts":
            d = os.path.join(dest, "prompts"); os.makedirs(d, exist_ok=True)
            for fn in sorted(os.listdir(s)):
                if fn.startswith(pat):
                    shutil.copy(os.path.join(s, fn), os.path.join(d, fn))
        else:
            if os.path.exists(os.path.join(s, pat)):
                shutil.copy(os.path.join(s, pat), os.path.join(dest, "trajectory.md"))

    si = os.path.join(src, "images", episode_id)
    if os.path.isdir(si):
        di = os.path.join(dest, "images", episode_id); os.makedirs(di, exist_ok=True)
        for fn in sorted(os.listdir(si)):
            shutil.copy(os.path.join(si, fn), os.path.join(di, fn))

    raw = os.path.join(src, "raw", f"{episode_id}.jsonl")
    if os.path.exists(raw):
        shutil.copy(raw, os.path.join(dest, "raw.jsonl"))

    n_img = sum(len(os.listdir(os.path.join(dest, "images", d)))
                for d in os.listdir(os.path.join(dest, "images"))) if os.path.isdir(os.path.join(dest, "images")) else 0
    n_pr = len(os.listdir(os.path.join(dest, "prompts"))) if os.path.isdir(os.path.join(dest, "prompts")) else 0
    print(f"{dest}: {len(turns)} turns, {n_pr} prompts, {n_img} images, PASS={rec['terminal_pass']}")
    return rec

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run"); ap.add_argument("--agent"); ap.add_argument("--episode"); ap.add_argument("--dest")
    a = ap.parse_args()
    export(a.run, a.agent, a.episode, a.dest)
