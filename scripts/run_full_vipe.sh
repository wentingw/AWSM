#!/usr/bin/env bash
set -euo pipefail
BLOG_ROOT=/home/hchen/Documents/astraBlenderTest/world_model_blog
SCAN_BASE=/home/hchen/Documents/astraBlenderTest/reconstruction
export CUDA_HOME="$SCAN_BASE/runtime/cuda"
export LD_PRELOAD="$SCAN_BASE/runtime/lib/libjitprofiling.so${LD_PRELOAD:+:$LD_PRELOAD}"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:/home/hchen/anaconda3/envs/trellis/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$SCAN_BASE/.venv/bin:$CUDA_HOME/bin:/home/hchen/anaconda3/envs/trellis/bin:$PATH"
export PYTHONPATH="$SCAN_BASE/vendor/vipe${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export HF_HOME="$SCAN_BASE/runtime/huggingface"
export TORCH_HOME="$SCAN_BASE/runtime/torch"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_PROGRESS_BARS=1
export TORCH_EXTENSIONS_DIR="$BLOG_ROOT/runtime/torch_extensions"
export XDG_CACHE_HOME="$BLOG_ROOT/runtime/cache"
export VIPE_SLAM_TARGET_PIXELS=98304
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
VIPE_OUTPUT="$BLOG_ROOT/experiments/world_lobby/M2/vipe_full_20260923"
mkdir -p "$VIPE_OUTPUT"
cd "$BLOG_ROOT"
exec flock "$BLOG_ROOT/runtime/gpu.lock" python "$BLOG_ROOT/src/vipe/run_full_vipe.py" pipeline=no_vda streams=frame_dir_stream \
  streams.base_path="$BLOG_ROOT/data/world_lobby/rgb_all" \
  streams.frame_start=0 streams.frame_end=-1 streams.frame_skip=1 \
  pipeline.init.async_prefetch=false pipeline.init.instance=null \
  pipeline.slam.buffer=384 pipeline.slam.keyframe_depth=unidepth-s \
  pipeline.slam.infill_chunk_size=4 pipeline.post.depth_align_model=adaptive_unidepth-s \
  pipeline.output.save_artifacts=true pipeline.output.save_slam_map=true \
  pipeline.output.save_viz=false pipeline.output.path="$VIPE_OUTPUT" \
  hydra.run.dir="$VIPE_OUTPUT/run"
