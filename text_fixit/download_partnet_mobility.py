#!/usr/bin/env python
"""
Download the PartNet-Mobility source meshes (mobility.urdf + textured_objs) for the
FixIt fridge shapes so we can drive them in PyBullet.

The released FixIt data ships only point clouds + choices; the base meshes were stripped.
FixIt shape IDs are PartNet-Mobility model IDs, so this just re-fetches them from SAPIEN.

USAGE
-----
1. Make a (free) account at https://sapien.ucsd.edu/ and accept the PartNet-Mobility
   license, then copy your download token from the account / downloads page.
2. Run:

       export SAPIEN_TOKEN=<your token>
       python text_fixit/download_partnet_mobility.py --split all

   (or pass --token <tok>). Assets unpack to text_fixit/assets/partnet_mobility/<id>/.

NOTE ON THE URL
---------------
SAPIEN's public download endpoint has historically been:
    https://sapien.ucsd.edu/api/download/compressed/<id>.zip?token=<TOKEN>
If SAPIEN changes it, override with --base-url. The script detects an HTML/error
response (e.g. bad token) instead of a zip and reports it clearly rather than
writing a corrupt file.
"""
import argparse
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE = Path(__file__).resolve().parent
IDS_JSON = HERE / "data" / "fridge_ids.json"
DEFAULT_OUT = HERE / "assets" / "partnet_mobility"
DEFAULT_BASE_URL = "https://sapien.ucsd.edu/api/download/compressed/{id}.zip?token={token}"


def load_ids(split: str):
    d = json.loads(IDS_JSON.read_text())
    if split == "train":
        return d["train"]
    if split == "test":
        return d["test"]
    return d["train"] + d["test"]


def already_have(dst: Path) -> bool:
    return (dst / "mobility.urdf").is_file()


def fetch(model_id: str, base_url: str, token: str, out_dir: Path) -> str:
    """Returns one of: 'skip', 'ok', or an error string."""
    dst = out_dir / model_id
    if already_have(dst):
        return "skip"
    url = base_url.format(id=model_id, token=token)
    try:
        req = Request(url, headers={"User-Agent": "text-fixit/0.1"})
        with urlopen(req, timeout=120) as resp:
            blob = resp.read()
    except HTTPError as e:
        return f"http {e.code} ({e.reason})"
    except URLError as e:
        return f"url error ({e.reason})"

    # A valid zip starts with 'PK'. Anything else (HTML login page, JSON error) => auth/URL problem.
    if blob[:2] != b"PK":
        snippet = blob[:120].decode("utf-8", "replace").replace("\n", " ")
        return f"not-a-zip (got: {snippet!r})"

    dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        # Zips unpack as "<id>/..."; strip that leading dir so files land directly in dst.
        for member in zf.infolist():
            name = member.filename
            parts = name.split("/", 1)
            rel = parts[1] if len(parts) == 2 and parts[0] == model_id else name
            if not rel or member.is_dir():
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as f:
                f.write(src.read())
    if not already_have(dst):
        return "unpacked but no mobility.urdf (unexpected archive layout)"
    return "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["train", "test", "all"], default="all")
    ap.add_argument("--token", default=os.environ.get("SAPIEN_TOKEN", ""))
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL,
                    help="Override if SAPIEN changes its endpoint. Must contain {id} and {token}.")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not args.token:
        sys.exit("ERROR: no token. Set SAPIEN_TOKEN or pass --token "
                 "(get it from your sapien.ucsd.edu account after accepting the license).")

    ids = load_ids(args.split)
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {len(ids)} PartNet-Mobility fridge model(s) [{args.split}] -> {args.out}")

    counts = {"ok": 0, "skip": 0, "fail": 0}
    failures = []
    for i, mid in enumerate(ids, 1):
        res = fetch(mid, args.base_url, args.token, args.out)
        if res in ("ok", "skip"):
            counts[res] += 1
            tag = res.upper()
        else:
            counts["fail"] += 1
            failures.append((mid, res))
            tag = f"FAIL: {res}"
        print(f"  [{i:>2}/{len(ids)}] {mid}: {tag}")

    print(f"\nDone. ok={counts['ok']} skip={counts['skip']} fail={counts['fail']}")
    if failures:
        print("Failures:")
        for mid, res in failures:
            print(f"  {mid}: {res}")
        print("\nIf every download says 'not-a-zip', your token is wrong/expired or the "
              "endpoint changed — check the account page and/or pass --base-url.")
        sys.exit(1)


if __name__ == "__main__":
    main()
