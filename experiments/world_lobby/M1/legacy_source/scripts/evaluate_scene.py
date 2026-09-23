"""Blender evaluation of the frozen v5 scene; never saves/changes the model.

Coordinates come only from camera SE(3), with the modeller's gravity rotation
undone. All geometric distances use point-to-triangle BVHs, not cloud NN.
"""
import hashlib
import json
import time
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

ROOT = Path('/home/hchen/Documents/astraBlenderTest')
RUN = ROOT/'vio-reconstruction/runs/stable_orbit_20260921T044401'
OUT = ROOT/'visual-recon/evaluation'
MODEL = ROOT/'visual-recon/scene.blend'
USD = ROOT/'drone-web/scenes/world_lobby/lobby.usda'
GT_POSE = ROOT/'vio-reconstruction/sessions/stable_orbit_20260921T044401/ground_truth/camera_tum.txt'
N = 250000
SEED = 20260922


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def join_world(objs, name, transform=None):
    # Detach parents while preserving world transforms, before changing frames.
    worlds = [(o, o.matrix_world.copy()) for o in objs]
    for o, world in worlds:
        o.parent = None
        o.matrix_world = world if transform is None else transform @ world
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.hide_set(False)
        o.hide_viewport = False
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def geometry(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    verts = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    mesh.vertices.foreach_get('co', verts.ravel())
    T = np.asarray(evaluated.matrix_world, dtype=np.float64)
    verts = (verts @ T[:3, :3].T + T[:3, 3]).astype(np.float32)
    tris = np.empty((len(mesh.loop_triangles), 3), dtype=np.int32)
    mesh.loop_triangles.foreach_get('vertices', tris.ravel())
    evaluated.to_mesh_clear()
    return verts, tris


def sample(verts, tris, n, seed):
    rng = np.random.default_rng(seed)
    area = np.empty(len(tris), dtype=np.float64)
    for start in range(0, len(tris), 250000):
        t = verts[tris[start:start+250000]].astype(np.float64)
        area[start:start+len(t)] = .5*np.linalg.norm(np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]), axis=1)
    ix = np.searchsorted(np.cumsum(area), rng.random(n)*area.sum())
    t = verts[tris[ix]].astype(np.float64)
    u, v = np.sqrt(rng.random(n)), rng.random(n)
    points = t[:, 0] + (u*(1-v))[:, None]*(t[:, 1]-t[:, 0]) + (u*v)[:, None]*(t[:, 2]-t[:, 0])
    return points, dict(area_m2=float(area.sum()), triangles=len(tris),
                       nonzero_area_triangles=int((area>1e-12).sum()),
                       bounds_min_m=verts.min(axis=0).tolist(), bounds_max_m=verts.max(axis=0).tolist())


def nearest(bvh, points):
    return np.asarray([bvh.find_nearest(Vector(p))[3] for p in points])


def stats(d):
    return dict(count=len(d), mean_m=float(d.mean()), median_m=float(np.median(d)),
                rmse_m=float(np.sqrt(np.mean(d*d))), p90_m=float(np.percentile(d, 90)),
                p95_m=float(np.percentile(d, 95)), max_m=float(d.max()),
                coverage={str(t): float(np.mean(d<=t)) for t in (.05, .1, .2, .5)})


def pair(a, b):
    aa, bb = stats(a), stats(b)
    return dict(model_to_gt=aa, gt_to_model=bb,
                symmetric_mean_m=(aa['mean_m']+bb['mean_m'])/2,
                f1={t: 2*aa['coverage'][t]*bb['coverage'][t]/max(1e-20, aa['coverage'][t]+bb['coverage'][t]) for t in aa['coverage']})


def main():
    start = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    model_hash = digest(MODEL)
    assert model_hash == json.loads((ROOT/'visual-recon/freeze_manifest.json').read_text())['files']['scene.blend']
    alignment = json.loads((OUT/'pose_metrics.json').read_text())
    T = np.asarray(alignment['T_truth_model'])
    assert np.allclose(T[:3, :3].T@T[:3, :3], np.eye(3), atol=1e-7)
    assert abs(np.linalg.det(T[:3, :3])-1)<1e-7
    bpy.ops.wm.open_mainfile(filepath=str(MODEL))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.get('render_only')]
    model_count = len(objects)
    assert model_count > 1000
    model = join_world(objects, 'EVAL_FROZEN_MODEL', Matrix(T.tolist()))
    vm, tm = geometry(model)
    print('Frozen model loaded', len(tm), 'triangles', flush=True)
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.usd_import(filepath=str(USD), import_materials=False, import_cameras=False, import_lights=False)
    objects = [o for o in bpy.context.scene.objects if o not in before and o.type == 'MESH']
    gt_count = len(objects)
    gt = join_world(objects, 'EVAL_TRUTH')
    vg, tg = geometry(gt)
    print('Ground truth loaded', len(tg), 'triangles', flush=True)
    assert len(tg) == json.loads((USD.parent/'scene.json').read_text())['source_triangles']
    sm, mm = sample(vm, tm, N, SEED)
    sg, gm = sample(vg, tg, N, SEED+1)
    bm = BVHTree.FromPolygons(vm, tm, all_triangles=True)
    bg = BVHTree.FromPolygons(vg, tg, all_triangles=True)
    del vm, tm, vg, tg
    dm, dg = nearest(bg, sm), nearest(bm, sg)
    np.savez_compressed(OUT/'scene_full_samples.npz', model_points=sm, gt_points=sg,
                        model_to_gt=dm, gt_to_model=dg)
    print('Full surface comparison', pair(dm, dg), flush=True)
    # 180 source camera timestamps; interpolate simulator camera ground truth.
    gtposes = np.loadtxt(GT_POSE, comments='#')
    cameras = json.loads((OUT/'evaluation_camera_timestamps.json').read_text())
    print('Camera views', len(cameras), flush=True)
    rays = np.asarray([[(x-640)/762.8, (y-480)/762.8, 1.] for y in np.linspace(0, 959, 48) for x in np.linspace(0, 1279, 64)])
    norm = np.linalg.norm(rays, axis=1)
    rays /= norm[:, None]
    visible_m, visible_g, depths, frames = [], [], [], []
    total = mg_hits = gt_hits = both = 0
    for c in cameras:
        ts = c['timestamp_s']
        hi = int(np.searchsorted(gtposes[:, 0], ts)); hi = min(max(hi, 1), len(gtposes)-1); lo=hi-1
        u = float((ts-gtposes[lo, 0])/(gtposes[hi, 0]-gtposes[lo, 0]))
        assert -.00001 <= u <= 1.00001
        u = min(max(u, 0), 1)
        pos = gtposes[lo, 1:4]*(1-u)+gtposes[hi, 1:4]*u
        q = lambda row: Quaternion(tuple(row[[7, 4, 5, 6]]))
        R = np.asarray(q(gtposes[lo]).slerp(q(gtposes[hi]), u).to_matrix())
        dirs = rays @ R.T
        visible_a, visible_b, dz = [], [], []
        for k, direction in enumerate(dirs):
            hm = bm.ray_cast(Vector(pos), Vector(direction), 100.)
            hg = bg.ray_cast(Vector(pos), Vector(direction), 100.)
            if hm[0] is not None: visible_a.append(tuple(hm[0]))
            if hg[0] is not None: visible_b.append(tuple(hg[0]))
            if hm[0] is not None and hg[0] is not None: dz.append(abs(hm[3]-hg[3])/norm[k])
        ma, ga = np.asarray(visible_a), np.asarray(visible_b)
        am, ag = nearest(bg, ma), nearest(bm, ga)
        visible_m.extend(am); visible_g.extend(ag); depths.extend(dz)
        frames.append(dict(index=c['index'], timestamp_s=ts, elapsed_s=ts-cameras[0]['timestamp_s'],
                           gt_hit_rays=len(ga), model_hit_rays=len(ma), both_hit_rays=len(dz),
                           surface=pair(am, ag), matched_ray_depth=stats(np.asarray(dz))))
        if c['index']%20 == 0: print('Visible evaluation frame',c['index'],flush=True)
        total += len(dirs); mg_hits += len(ma); gt_hits += len(ga); both += len(dz)
    av, bv = np.asarray(visible_m), np.asarray(visible_g)
    np.savez_compressed(OUT/'scene_visible_distances.npz', model_to_gt=av, gt_to_model=bv,
                        same_ray_abs_z_error_m=np.asarray(depths))
    result = dict(evaluation_only=True, evaluated_model_sha256=model_hash,
                  model_path=str(MODEL), ground_truth_usd=str(USD), ground_truth_usd_sha256=digest(USD),
                  model_mesh_parts=model_count, gt_mesh_objects=gt_count,
                  T_truth_model=T.tolist(), scale_applied=1,
                  alignment='SE(3) from four frozen manually composed camera positions and approximate RGB frame associations. No ICP, no geometry fitting, no rescaling. Not a recovered trajectory.',
                  sampling=dict(points_per_surface=N, seed=SEED, rule='uniform surface area; exact nearest triangle BVH'),
                  model_geometry=mm, gt_geometry=gm,
                  full_scene=pair(dm, dg),
                  observed_camera_views=dict(scope='180 original simulator camera poses, 64x48 first-hit rays per view, 100 m far range',
                      views=len(cameras), rays=total, gt_hit_rays=gt_hits, model_hit_rays=mg_hits,
                      both_hit_rays=both, gt_hit_fraction=gt_hits/total, model_hit_fraction=mg_hits/total,
                      **pair(av, bv), same_ray_depth_abs_error_m=stats(np.asarray(depths))),
                  sampling_convergence={str(n): pair(dm[:n], dg[:n]) for n in (50000, 100000, N)},
                  per_view=frames,
                  limitations=['Full USD includes unobserved, exterior and hidden geometry.',
                    'Visible-surface metric is view/pixel weighted; full-scene metric is surface-area weighted.',
                    'Glass is treated as first-hit geometry; transparency/refraction is not simulated.',
                    'Nearest triangle may belong to the wrong semantic object; appearance/materials are not graded.',
                    'This is registered visual reconstruction discrepancy, including four-view registration and arbitrary visual scale; not isolated modelling error.',
                    'Four camera compositions are approximate source-view associations; these scores are not directly comparable to a full estimated trajectory.',
                    'Authored units are interpreted as metres with scale=1; no metric scale was recovered from RGB.'],
                  runtime_s=time.monotonic()-start)
    assert digest(MODEL) == model_hash
    (OUT/'scene_metrics.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'per_view'}, indent=2), flush=True)


main()
