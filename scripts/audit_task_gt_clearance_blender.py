#!/usr/bin/env python3
"""Static G1 trajectory clearance audit against the metric GT surface.

This audit uses only the authorized GT USD wrapper and a supplied model->GT
transform. It measures nearest triangle-surface distances for torso/head and
foot proxies. It does not replay dynamics, test inside/outside, or claim GT
collision transfer.
"""
import argparse,csv,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def collect_gt():
    vs=[]; ts=[]; off=0
    deps=bpy.context.evaluated_depsgraph_get()
    for o in [x for x in bpy.context.scene.objects if x.type=='MESH']:
        e=o.evaluated_get(deps); m=e.to_mesh(); m.calc_loop_triangles()
        v=np.empty((len(m.vertices),3),np.float32); m.vertices.foreach_get('co',v.ravel())
        W=np.asarray(e.matrix_world,float); v=v@W[:3,:3].T+W[:3,3]
        t=np.empty((len(m.loop_triangles),3),np.int32); m.loop_triangles.foreach_get('vertices',t.ravel())
        vs.append(v); ts.append(t+off); off+=len(v); e.to_mesh_clear()
    if not vs: raise RuntimeError('GT USD imported no mesh objects')
    return np.vstack(vs),np.vstack(ts)

def quat_rot(q,v):
    w,x,y,z=q; qv=np.array([x,y,z]); return v+2*np.cross(qv,np.cross(qv,v)+w*v)
def read_traj(path):
    rows=[]
    with open(path) as f:
        for r in csv.DictReader(f): rows.append(r)
    return rows

def stat(a):
    a=np.asarray(a,float); return {'count':int(len(a)),'min_m':float(np.min(a)),'mean_m':float(np.mean(a)),'median_m':float(np.median(a)),'p90_m':float(np.percentile(a,90)),'max_m':float(np.max(a))}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--gt-usd',required=True); ap.add_argument('--transform-json',required=True); ap.add_argument('--trajectory',action='append',required=True); ap.add_argument('--out',required=True)
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None
    a=ap.parse_args(argv); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    T=np.asarray(json.load(open(a.transform_json)).get('transform'),float)
    if T.shape!=(4,4): raise ValueError('transform must be 4x4')
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.usd_import(filepath=a.gt_usd,import_materials=False,import_cameras=False,import_lights=False)
    gv,gt=collect_gt(); bvh=BVHTree.FromPolygons(gv,gt,all_triangles=True)
    if len(gt)!=9984967: raise RuntimeError(f'GT triangle count {len(gt)} != 9984967')
    floor_z=float(np.percentile(gv[:,2],.5)); all_results=[]; csvrows=[]
    for tp in a.trajectory:
        rows=read_traj(tp); torso=[]; head=[]; foot=[]; foot_dev=[]
        for r in rows:
            base=np.array([float(r['x']),float(r['y']),float(r['z'])]); q=np.array([float(r[k]) for k in ('qw','qx','qy','qz')])
            pts={'torso':base+quat_rot(q,np.array([0,0,.45])),'head':base+quat_rot(q,np.array([0,0,1.10])),'foot_left':base+quat_rot(q,np.array([-.12,0,-.78])),'foot_right':base+quat_rot(q,np.array([.12,0,-.78]))}
            for k,v in pts.items():
                hv=np.r_[v,1.]@T.T; hit=bvh.find_nearest(Vector(hv[:3])); d=float(hit[3]) if hit else float('nan')
                if k=='torso': torso.append(d)
                elif k=='head': head.append(d)
                else: foot.append(d); foot_dev.append(float(hv[2]-floor_z))
            csvrows.append([Path(tp).name,r['time_s'],*[(np.r_[pts[k],1.]@T.T)[:3].tolist() for k in ('torso','head','foot_left','foot_right')]])
        all_results.append({'trajectory':str(tp),'samples':len(rows),'torso_surface_distance_m':stat(torso),'head_surface_distance_m':stat(head),'foot_surface_distance_m':stat(foot),'foot_bottom_minus_gt_floor_m':stat(foot_dev),'potential_surface_overlap_lt_0p05m':bool(np.nanmin(torso+head+foot)<.05)})
    agg={k:stat(np.concatenate([np.array(r[k]['min_m'] if False else []) for r in []])) for k in []}
    report={'gt_usd':str(Path(a.gt_usd).resolve()),'gt_triangles':len(gt),'transform_json':str(Path(a.transform_json).resolve()),'floor_estimate_z_m':floor_z,'trajectory_count':len(all_results),'trajectories':all_results,'semantics':['nearest triangle-surface distances only','foot height is proxy based on base pose and fixed offsets','no inside/outside test','static geometry audit, no dynamics replay','planning failures without trajectory are omitted and not fabricated'],'threshold_note':'G1 has no collision-transfer threshold; reported distances are descriptive.'}
    (out/'g1_gt_clearance.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'g1_gt_clearance_points.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['trajectory','time_s','torso_xyz_gt','head_xyz_gt','foot_left_xyz_gt','foot_right_xyz_gt']); w.writerows(csvrows)
    print(json.dumps({'trajectory_count':len(all_results),'gt_triangles':len(gt),'floor_z_m':floor_z}))
if __name__=='__main__': main()
