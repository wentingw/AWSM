# Reproduction commands

Run from `/home/hchen/Documents/astraBlenderTest`.

## Input contract

```bash
python world_lobby_four_trajectory_20260929/code/freeze_contract.py
```

## ViPE default

The run used the environment defined by `world_model_blog/scripts/run_full_vipe.sh`
(`VIPE_SLAM_TARGET_PIXELS=98304`, offline model caches, and the reconstruction
CUDA runtime), with these estimator arguments:

```bash
python world_model_blog/src/vipe/run_full_vipe.py \
  pipeline=no_vda streams=frame_dir_stream \
  streams.base_path=vio-reconstruction/sessions/lobby_orb_success_20260929T123153/inputs/cam0/data \
  streams.frame_start=0 streams.frame_end=-1 streams.frame_skip=1 \
  pipeline.init.async_prefetch=false pipeline.init.instance=null \
  pipeline.slam.buffer=384 pipeline.slam.keyframe_depth=unidepth-s \
  pipeline.slam.infill_chunk_size=4 \
  pipeline.post.depth_align_model=adaptive_unidepth-s \
  pipeline.output.save_artifacts=true pipeline.output.save_slam_map=true \
  pipeline.output.save_viz=false \
  pipeline.output.path=world_model_blog/experiments/world_lobby/four_trajectory_20260929/vipe_default_full
```

The pose comparison only requires the full 4,499-frame camera solution.
`VIPE_DEPTH_PHASE=keyframes` therefore stops after the 90 scheduled keyframe
depths; this does not alter the already checkpointed ViPE trajectory.

```bash
python world_lobby_four_trajectory_20260929/code/freeze_vipe.py
```

## OpenVINS

```bash
/home/hchen/anaconda3/envs/ov_jazzy_min/bin/cmake \
  --build stable_orbit_da3_rerun_20260923/code/openvins/offline/build -j2

source /home/hchen/anaconda3/envs/ov_jazzy_min/setup.bash
source vio-reconstruction/estimator/vendor/openvins_ws/install/setup.bash

stable_orbit_da3_rerun_20260923/code/openvins/offline/build/openvins_offline_runner \
  --config stable_orbit_da3_rerun_20260923/configs/openvins/openvins_maxclones31.yaml \
  --cam-csv vio-reconstruction/sessions/lobby_orb_success_20260929T123153/inputs/cam0/data.csv \
  --imu-csv vio-reconstruction/sessions/lobby_orb_success_20260929T123153/inputs/imu0/data.csv \
  --image-dir vio-reconstruction/sessions/lobby_orb_success_20260929T123153/inputs/cam0/data \
  --output world_lobby_four_trajectory_20260929/openvins/full/pose_cam.tum \
  --state-output world_lobby_four_trajectory_20260929/openvins/full/state.txt \
  --metadata world_lobby_four_trajectory_20260929/openvins/full/metadata.json \
  --all-camera-frames true

python world_lobby_four_trajectory_20260929/code/freeze_openvins.py
```

## Evaluation and verification

```bash
python world_lobby_four_trajectory_20260929/code/evaluate_and_plot.py
python world_lobby_four_trajectory_20260929/code/verify_results.py
python world_lobby_four_trajectory_20260929/code/generate_canvas.py
```

Run the Python post-processing commands in an environment containing NumPy,
SciPy, Matplotlib, and Pillow, with ROS/OpenVINS `PYTHONPATH` variables unset.

## Pose-conditioned DA3 depth

Create the disjoint 180-frame modelling and 500-frame evaluation schedules:

```bash
python world_lobby_four_trajectory_20260929/code/prepare_depth_samples.py
python -m unittest world_lobby_four_trajectory_20260929/code/test_depth_pipeline.py
```

Pose-conditioned inference uses the cached `depth-anything/DA3-GIANT`
checkpoint. `DA3METRIC-LARGE` is not used because it has no camera encoder;
metric output scale comes from alignment to each method's native metric poses.
The four-view process resolution is 392: 504 exceeds the available 10 GB GPU.
DA3 uses the reconstruction runtime. Run one smoke window first:

```bash
source reconstruction/scripts/scan_env.sh
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

python world_lobby_four_trajectory_20260929/code/run_da3_depth.py \
  --method M4 --split modeling_180 --window-index 0
```

After the smoke check, run both splits for `M2`, `M3`, and `M4`:

```bash
for method in M2 M3 M4; do
  for split in modeling_180 eval_500; do
    python world_lobby_four_trajectory_20260929/code/run_da3_depth.py \
      --method "$method" --split "$split"
  done
  python world_lobby_four_trajectory_20260929/code/build_depth_packets.py \
    --method "$method" --split both
done
```

Do not generate or open GT depth until all six prediction runs have completed
and their hashes have been recorded. Then generate GT optical-Z in Blender:

```bash
blender --background --python \
  world_lobby_four_trajectory_20260929/code/generate_gt_depth_blender.py \
  -- --split modeling_180

blender --background --python \
  world_lobby_four_trajectory_20260929/code/generate_gt_depth_blender.py \
  -- --split eval_500
```

Evaluate and require all artifacts:

```bash
python world_lobby_four_trajectory_20260929/code/evaluate_da3_depth.py \
  --split modeling_180
python world_lobby_four_trajectory_20260929/code/evaluate_da3_depth.py \
  --split eval_500
python world_lobby_four_trajectory_20260929/code/verify_depth_pipeline.py \
  --require-results
```
