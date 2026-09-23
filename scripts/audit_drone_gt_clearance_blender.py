#!/usr/bin/env python3
import argparse,csv,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def gt_mesh():
 vs=[];ts=[];off=0;deps=bpy.context.evaluated_depsgraph_get()
 for o in [x for x in bpy.context.scene.objects if x.type=='MESH']:
  e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());W=np.asarray(e.matrix_world,float);v=v@W[:3,:3].T+W[:3,3];t=np.empty((len(m.loop_triangles),3),np.int32);m.loop_triangles.foreach_get('vertices',t.ravel());vs.append(v);ts.append(t+off);off+=len(v);e.to_mesh_clear()
 return np.vstack(vs),np.vstack(ts)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--gt-usd',required=True);ap.add_argument('--transform-json',required=True);ap.add_argument('--trajectory',action='append',required=True);ap.add_argument('--out',required=True);argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None;a=ap.parse_args(argv);out=Path(a.out);out.mkdir(parents=True,exist_ok=True);T=np.asarray(json.load(open(a.transform_json))['transform'],float)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.wm.usd_import(filepath=a.gt_usd,import_materials=False,import_cameras=False,import_lights=False);v,t=gt_mesh();assert len(t)==9984967,(len(t),);bvh=BVHTree.FromPolygons(v,t,all_triangles=True);allr=[];rows=[]
 for tp in a.trajectory:
  ds=[]
  with open(tp) as f:
   for r in csv.DictReader(f):
    p=np.r_[float(r['x']),float(r['y']),float(r['z']),1.]@T.T;h=bvh.find_nearest(Vector(p[:3]));d=float(h[3]) if h else float('nan');ds.append(d);rows.append([Path(tp).name,r['time_s'],*p[:3],d])
  x=np.asarray(ds);allr.append({'trajectory':str(tp),'samples':len(x),'min_m':float(np.nanmin(x)),'mean_m':float(np.nanmean(x)),'median_m':float(np.nanmedian(x)),'p90_m':float(np.nanpercentile(x,90)),'potential_overlap_lt_0p30m':bool(np.nanmin(x)<.30)})
 report={'gt_usd':str(Path(a.gt_usd).resolve()),'gt_triangles':len(t),'transform_json':str(Path(a.transform_json).resolve()),'trajectory_count':len(allr),'trajectories':allr,'semantics':['center point to nearest GT triangle surface only','sphere-radius interpretation is approximate; no inside/outside test','static geometry audit, no MuJoCo dynamics replay','potential_overlap_lt_0p30m is descriptive, not collision truth']};(out/'drone_gt_clearance.json').write_text(json.dumps(report,indent=2)+'\n')
 with (out/'drone_gt_clearance_points.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['trajectory','time_s','x_gt','y_gt','z_gt','nearest_surface_distance_m']);w.writerows(rows)
 print(json.dumps({'trajectory_count':len(allr),'gt_triangles':len(t),'potential_overlap_count':sum(x['potential_overlap_lt_0p30m'] for x in allr)}))
if __name__=='__main__':main()
