#!/usr/bin/env bash
# Serve Qwen3-VL for the qwen agents in agents/qwen_vl.py.
#
# Runs in its own conda env (qwenvl) because vLLM/transformers>=4.57 would break the torch
# 2.5.1+cu121 pin the `fixing` env needs for the compiled point-cloud ops.
#
#   bash text_fixit/serve_qwen.sh              # GPU 0, port 8001
#   GPU=1 PORT=8002 bash text_fixit/serve_qwen.sh
#
# Port 8001, not 8000: another user's service already listens on 8000 on this box.
#
# Then, in the `fixing` env:
#   python text_fixit/run_episode.py --agent loop_qwen_full --modality image --verbose
set -euo pipefail

MODEL="${QWEN_MODEL:-Qwen/Qwen3-VL-8B-Instruct}"
GPU="${GPU:-0}"                    # GPU 1 is often busy with another user's job -- default to 0
PORT="${PORT:-8001}"
UTIL="${UTIL:-0.60}"               # fraction of the card; leave room for a co-tenant
MAXLEN="${MAXLEN:-32768}"
VENV=/home/sammathew/miniconda3/envs/qwenvl

# 4 images/turn (before closed+open, after closed+open) + the labelled reset view.
exec env CUDA_VISIBLE_DEVICES="$GPU" "$VENV/bin/vllm" serve "$MODEL" \
  --port "$PORT" \
  --gpu-memory-utilization "$UTIL" \
  --max-model-len "$MAXLEN" \
  --limit-mm-per-prompt '{"image": 6}' \
  --served-model-name "$MODEL"
