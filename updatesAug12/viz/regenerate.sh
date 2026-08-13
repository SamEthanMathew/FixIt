#!/usr/bin/env bash
# Rebuild every figure from the run tree. Run after any condition finishes.
#   bash updatesAug12/viz/regenerate.sh
set -euo pipefail
cd /home/sammathew/Code/FixIt
SP=/tmp/claude-1003/-home-sammathew-Code-FixIt/08bc4717-a546-4ce7-8e91-49e526b7b9a5/scratchpad
PY=python3

echo "1/4  extracting series ..."
$PY updatesAug12/viz/extract.py

echo "2/4  qwen convergence (baseline vs the two ablations) ..."
$PY updatesAug12/viz/build_qwen_convergence.py

echo "3/4  all-condition convergence + what-predicts-repair ..."
$PY updatesAug12/viz/build_convergence_all.py
$PY updatesAug12/viz/build_what_predicts.py

echo "4/4  per-run diagnostics ..."
$PY text_fixit/viz_per_run.py --out updatesAug12/per_run_diagnostics.html
echo "done — updatesAug12/*.html"
