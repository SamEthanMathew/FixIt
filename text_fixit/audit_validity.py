#!/usr/bin/env python
"""
Validity audit: classify every run against every KNOWN harness defect.

Four defects were found and fixed during the project. Each one silently changed what a run measured,
and each was fixed at a specific commit, so a run's exposure is decidable from its manifest and logs
rather than from memory. This script does that and emits a table with a verdict per run.

    python text_fixit/audit_validity.py            # markdown to stdout
    python text_fixit/audit_validity.py --csv      # machine-readable

DEFECTS

  D1  image transport        Fixed cda9eba. The stateless agent path (history=window3, and EVERY
                             oneshot agent) never attached obs["images"] to the request. In image
                             modality the model was told images were attached and received none.
                             Detect: modality==image AND stateless path AND no images_sent_to_model
                             field in the turn log.

  D2  PyBullet name cache    Fixed 8b53a6b (env._eval_seq). Candidates were written to one reused
                             temp path; PyBullet caches parsed URDF and collision geometry BY
                             FILENAME within a client, so `closes` and `collides` froze at their
                             first-candidate values. `deviation`/`within_tol` (read from XML) stayed
                             correct, so headline numbers are directionally sound but the physical
                             gates are stale after the first SIMULATE.
                             Detect: no manifest (predates logging) or git_commit is an ancestor.

  D3  Qwen give-up blindness Fixed dcda1cb. QwenVLAgent._call never populated last_meta, so
                             n_api_giveup was structurally 0 and a dead vLLM server would score a
                             whole condition as legitimate NO_FIX commits. Integrity counters for
                             these runs are unreliable (they are not evidence of clean runs).
                             Detect: a qwen agent and a commit predating the fix.

  D4  180s client timeout    Fixed dcda1cb (QWEN_TIMEOUT). Long generations exceeded the hardcoded
                             read timeout, retried, then fell back to COMMIT NO_FIX() -- an
                             infrastructure failure scored as the model declining to repair.
                             Detect: ReadTimeout entries in errors.jsonl.

  D5  truncated              Fewer episodes than the manifest planned (stopped early).
"""
import argparse
import glob
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")

FIX = {"D1": "cda9eba", "D2": "8b53a6b", "D3": "dcda1cb", "D4": "dcda1cb"}
SMOKE = ("smoke", "pt_smoke", "pt_smoke2", "wire_smoke", "qwen_smoke", "probe32_window3",
         "verify_imgfix", "hist_cmp")


def _predates(commit, fix):
    """Is `commit` an ancestor of `fix` (i.e. does the run predate the fix)?"""
    if not commit:
        return True                      # no manifest at all => predates manifest logging
    r = subprocess.run(["git", "merge-base", "--is-ancestor", commit, fix],
                       capture_output=True, cwd=os.path.dirname(HERE))
    return r.returncode == 0


def _turn_field(d, key):
    f = os.path.join(d, "turns.jsonl")
    if not os.path.exists(f):
        return None
    for line in open(f):
        v = json.loads(line).get(key)
        if v is not None:
            return v
    return None


def audit():
    rows = []
    for recs in sorted(glob.glob(os.path.join(RUNS, "*", "*", "records.jsonl"))):
        d = os.path.dirname(recs)
        run, agent = recs.split(os.sep)[-3], recs.split(os.sep)[-2]
        mf = os.path.join(d, "manifest.json")
        m = json.load(open(mf)) if os.path.exists(mf) else {}
        rs = [json.loads(line) for line in open(recs)]
        if not rs:
            continue
        n, k = len(rs), sum(1 for r in rs if r["terminal_pass"])
        mod = m.get("modality") or rs[0].get("state_modality")
        hist = m.get("history_mode")
        commit = m.get("git_commit")

        stateless = agent.startswith("oneshot") or hist == "window3"
        d1 = (mod == "image" and stateless and not _turn_field(d, "images_sent_to_model"))
        d2 = _predates(commit, FIX["D2"])
        d3 = ("qwen" in agent) and _predates(commit, FIX["D3"])
        errs = os.path.join(d, "errors.jsonl")
        d4 = (os.path.exists(errs)
              and sum(1 for line in open(errs) if "ReadTimeout" in line or "Read timed out" in line) > 0)
        planned = m.get("n_instances")
        d5 = bool(planned) and n < planned

        flags = [f for f, on in (("D1", d1), ("D2", d2), ("D3", d3), ("D4", d4), ("D5", d5)) if on]
        if run.startswith("_contaminated") or any(run == s or run.startswith(s) for s in SMOKE):
            verdict = "DEV / SUPERSEDED"
        elif d1:
            verdict = "INVALID as an image result"
        elif d4:
            verdict = "SUSPECT (timeouts)"
        elif d2 or d3:
            verdict = "CITE WITH WARNING"
        elif d5:
            verdict = "PARTIAL"
        else:
            verdict = "OK"
        rows.append(dict(run=run, agent=agent, mod=mod, n=n, k=k, flags=",".join(flags) or "-",
                         verdict=verdict))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true")
    a = ap.parse_args()
    rows = audit()
    if a.csv:
        print("run,agent,modality,n,solved,defects,verdict")
        for r in rows:
            print(f"{r['run']},{r['agent']},{r['mod']},{r['n']},{r['k']},{r['flags']},{r['verdict']}")
        return

    order = ["INVALID as an image result", "SUSPECT (timeouts)", "CITE WITH WARNING", "PARTIAL",
             "DEV / SUPERSEDED", "OK"]
    print("# Validity audit — every run against every known harness defect\n")
    print("Generated by `text_fixit/audit_validity.py` from manifests, turn logs and git ancestry.\n")
    for v in order:
        sel = [r for r in rows if r["verdict"] == v]
        if not sel:
            continue
        eps = sum(r["n"] for r in sel)
        print(f"## {v} — {len(sel)} runs / {eps} episodes\n")
        print("| run | agent | modality | n | solved | defects |")
        print("|---|---|---|---|---|---|")
        for r in sorted(sel, key=lambda r: r["run"]):
            print(f"| `{r['run']}` | {r['agent']} | {r['mod']} | {r['n']} | {r['k']} | {r['flags']} |")
        print()


if __name__ == "__main__":
    main()
