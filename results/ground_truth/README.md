# GT evaluation assets

`manifest.json` is a references-only manifest. It records the original GT
camera/IMU calibration, hashes, the fixed 180 mapping frames, and 20 same-video
diagnostic views. The latter are **not** independent holdout: front ends may
have observed the same video.

`independent_holdout.status` is intentionally `missing`. A genuine holdout
requires a new camera trajectory with RGB, pose, and depth hidden from every
front end. No GT mesh or depth is copied into a modelling input package.

The 10M-triangle USD remains read-only at the source path in the manifest.
`render_gt_depth_blender.py` is the CPU-only renderer for GT optical-z depth;
its output is separate from method manifests.
