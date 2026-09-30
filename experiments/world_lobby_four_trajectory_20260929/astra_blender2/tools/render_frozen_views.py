"""Render frozen models at common evaluator cameras without changing scene files."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix


def configure_device(scene, device):
    if device == "CPU":
        scene.cycles.device = "CPU"
        return ["CPU"]
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = device
    preferences.get_devices()
    enabled = []
    for candidate in preferences.devices:
        candidate.use = candidate.type == device
        if candidate.use:
            enabled.append(candidate.name)
    if not enabled:
        raise RuntimeError(f"No {device} Cycles device is available")
    scene.cycles.device = "GPU"
    return enabled


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--cameras", required=True)
    parser.add_argument("--registration", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--indices", default="0,45,90,135,179")
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--device", choices=("CPU", "CUDA", "OPTIX"), default="CPU")
    parser.add_argument("--threads", type=int, default=0)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    model = Path(args.model)
    before = hashlib.sha256(model.read_bytes()).hexdigest()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    registration = json.loads(Path(args.registration).read_text())
    model_from_gt = np.linalg.inv(np.array(registration["transform"]))
    cameras = json.loads(Path(args.cameras).read_text())
    intrinsics = np.array(cameras["intrinsics"])
    optical_to_blender = np.diag([1, -1, -1, 1])
    bpy.ops.wm.open_mainfile(filepath=str(model))
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    enabled_devices = configure_device(scene, args.device)
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    if args.threads:
        scene.render.threads_mode = "FIXED"
        scene.render.threads = args.threads
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.pixel_aspect_x = 1
    scene.render.pixel_aspect_y = 1
    camera_data = bpy.data.cameras.new("independent_GT_evaluation_camera")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "PERSP"
    camera_data.sensor_fit = "HORIZONTAL"
    camera_data.sensor_width = 36
    camera_data.lens = intrinsics[0, 0] * 36 / 1280
    camera_data.shift_x = (640 - intrinsics[0, 2]) / 1280
    camera_data.shift_y = (intrinsics[1, 2] - 480) / 1280
    camera_data.clip_start = 0.01
    camera_data.clip_end = 1000
    indices = [int(value) for value in args.indices.split(",")]
    for index in indices:
        camera_to_world = model_from_gt @ np.array(
            cameras["frames"][index]["camera_to_world"]
        )
        camera_to_world[:3, :3] /= np.linalg.norm(camera_to_world[:3, 0])
        camera.matrix_world = Matrix((camera_to_world @ optical_to_blender).tolist())
        scene.render.filepath = str(out / f"{index:03d}.png")
        bpy.ops.render.render(write_still=True)
    assert hashlib.sha256(model.read_bytes()).hexdigest() == before
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "model_sha256": before,
                "indices": indices,
                "source": "common GT cameras after model freezing",
                "width": 640,
                "height": 480,
                "cycles_samples": args.samples,
                "cycles_device": args.device,
                "enabled_devices": enabled_devices,
                "saved_model_modified": False,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
