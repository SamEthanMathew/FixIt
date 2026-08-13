# Run archive — complete experimental record

`fixit_runs_full_2026-08-13.tar.zst` is the entire `text_fixit/runs/` tree at the end of the
2026-08 work, archived because that directory is gitignored and was about to be deleted locally.

**Contents — 20,947 files, 397 MB uncompressed, 74 MB archived**

| | |
|---|---|
| run directories | 103 |
| episode records (`records.jsonl`) | 3,764 across 140 files |
| turn records (`turns.jsonl`) | 14,189 |
| rendered images (PNG) | 8,623 |
| exact prompts sent (`prompts/*.txt`) | 9,079 |
| derived tables | `runs/_analysis/*.{md,json}` |

Every experiment from M1 through M13 is in here: manifests (model, contract, tolerance, git commit,
instance sha256), per-episode results, per-turn reasoning and raw API metadata, every image the
environment rendered, and the exact system+user text sent on every turn.

## Extract

```bash
tar -I zstd -xf fixit_runs_full_2026-08-13.tar.zst -C text_fixit/
# -> recreates text_fixit/runs/
```

If `zstd` is unavailable: `apt install zstd` or `conda install zstd`.

## Verified before the originals were deleted

- file count on disk == file count in archive (20,947)
- all 140 `records.jsonl` and all 8,623 PNGs present
- a round-trip extraction was byte-identical to its original

## Reading it

`text_fixit/summarize_runs.py --group <m4|m5|…|m13>` and `text_fixit/episode_report.py --glob 'm13_*'`
both read this tree directly once extracted. `updatesAug12/INVALIDATED_DATA.md` lists which runs are
invalid and why — read that before citing any image-modality result from `m9`/`m10`/`m11`.
