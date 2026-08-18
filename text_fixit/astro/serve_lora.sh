#!/usr/bin/env bash
# Serve the ASTRO LoRA adapter on top of the base Qwen3-VL, for evaluation with the existing
# harness. Mirrors text_fixit/serve_qwen.sh -- same env, same port, same limits -- so a post-SFT
# run differs from the pre-SFT baseline in the adapter and nothing else.
#
#   bash text_fixit/astro/serve_lora.sh runs_sft/astro_qwen8_text
#   GPU=1 PORT=8002 bash text_fixit/astro/serve_lora.sh <adapter_dir>
#
# Then evaluate against it. `--model astro` is what routes the request to the adapter, and
# run_trials now forwards it to QWEN_MODEL for qwen agents (it used to set GEMINI_MODEL only,
# which silently scored the BASE model):
#
#   FIXIT_TAU_FRAC=0.015 FIXIT_PROMPT_SET=one_error_search \
#   conda run -n fixing python text_fixit/run_trials.py \
#       --agent loop_qwen --model astro --modality text --deviation on \
#       --instances data/instances_astro_heldout.jsonl --sweep \
#       --budget 10 --max-actions 1 --run astro_sft_heldout_text
#
# Serve the BASE model with serve_qwen.sh and run the identical command with
# `--model Qwen/Qwen3-VL-8B-Instruct --run astro_base_heldout_text` for the paired baseline.
set -euo pipefail

ADAPTER="${1:?usage: serve_lora.sh <adapter_dir> -- the --out directory from train_lora.py}"
[ -d "$ADAPTER" ] || { echo "no such adapter dir: $ADAPTER" >&2; exit 1; }
[ -f "$ADAPTER/adapter_config.json" ] || {
  echo "$ADAPTER has no adapter_config.json -- is this a LoRA output dir?" >&2; exit 1; }

MODEL="${QWEN_MODEL:-Qwen/Qwen3-VL-8B-Instruct}"
NAME="${LORA_NAME:-astro}"
GPU="${GPU:-0}"
PORT="${PORT:-8001}"
UTIL="${UTIL:-0.60}"
MAXLEN="${MAXLEN:-32768}"
# Must be >= the r used in train_lora.py (default 16); vLLM rejects an adapter above this.
MAXRANK="${MAXRANK:-16}"
VENV=/home/sammathew/miniconda3/envs/qwenvl

exec env CUDA_VISIBLE_DEVICES="$GPU" "$VENV/bin/vllm" serve "$MODEL" \
  --port "$PORT" \
  --gpu-memory-utilization "$UTIL" \
  --max-model-len "$MAXLEN" \
  --limit-mm-per-prompt '{"image": 6}' \
  --served-model-name "$MODEL" \
  --enable-lora \
  --max-lora-rank "$MAXRANK" \
  --lora-modules "$NAME=$(readlink -f "$ADAPTER")"
