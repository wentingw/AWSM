#!/usr/bin/env python3
"""Exact point-to-triangle surface evaluation using Blender BVH trees."""
import argparse,json
from pathlib import Path
import bpy,numpy as np,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def collect(objs,T=None):
 vs=[];ts=[];off=0;deps=bpy.context.evaluated_depsgraph_get()
 for o in objs:
  e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());W=np.asarray(e.matrix_world,float);v=v@W[:3,:3].T+W[:3,3]
  if T is not None:v=v@T[:3,:3].T+T[:3,3]
  t=np.empty((len(m.loop_triangles),3),np.int32);m.loop_triangles.foreach_get('vertices',t.ravel());vs.append(v);ts.append(t+off);off+=len(v);e.to_mesh_clear()
 if not vs:raise RuntimeError('no mesh objects')
 return np.vstack(vs),np.vstack(ts)
def sample(v,t,n,seed):
 rng=np.random.default_rng(seed);tri=v[t];area=.5*np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1);c=np.cumsum(area);ix=np.searchsorted(c,rng.random(n)*c[-1]);q=tri[ix];u=np.sqrt(rng.random(n));w=rng.random(n);return q[:,0]+u[:,None]*(1-w)[:,None]*(q[:,1]-q[:,0])+u[:,None]*w[:,None]*(q[:,2]-q[:,0])
def stats(d):return {'count':int(len(d)),'mean_m':float(np.mean(d)),'rmse_m':float(np.sqrt(np.mean(d*d))),'median_m':float(np.median(d)),'p90_m':float(np.percentile(d,90)),'threshold_coverage':{str(x):float(np.mean(d<=x)) for x in (.05,.1,.2)}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model',required=True);ap.add_argument('--gt-usd',default='/home/hchen/Documents/astraBlenderTest/drone-web/scenes/world_lobby/lobby.usda');ap.add_argument('--out',required=True);ap.add_argument('--transform-json');ap.add_argument('--samples',type=int,default=100000);argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None; a=ap.parse_args(argv);out=Path(a.out);out.mkdir(parents=True,exist_ok=True);T=np.eye(4) if not a.transform_json else np.asarray((lambda d:d.get('transform',d.get('T_gt_model')))(json.load(open(a.transform_json))),float)
 if T.shape!=(4,4) or not np.isfinite(T).all():raise ValueError('transform must be finite 4x4')
 bpy.ops.wm.open_mainfile(filepath=a.model);model_objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];mv,mt=collect(model_objs,T);model_bounds=[mv.min(axis=0).tolist(),mv.max(axis=0).tolist()];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.wm.usd_import(filepath=a.gt_usd,import_materials=False,import_cameras=False,import_lights=False);gt_objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];gv,gt=collect(gt_objs);gt_bounds=[gv.min(axis=0).tolist(),gv.max(axis=0).tolist()];expected_gt_triangles=9984967
 if len(gt)!=expected_gt_triangles:raise RuntimeError(f'GT triangle count {len(gt)} != expected {expected_gt_triangles}; wrong USD wrapper/units')
 bm=BVHTree.FromPolygons(mv,mt,all_triangles=True);bg=BVHTree.FromPolygons(gv,gt,all_triangles=True);mp=sample(mv,mt,a.samples,20260923);gp=sample(gv,gt,a.samples,20260924);dm=np.array([bg.find_nearest(Vector(x))[3] for x in mp]);dg=np.array([bm.find_nearest(Vector(x))[3] for x in gp]);np.savez_compressed(out/'surface_distances.npz',model_to_gt=dm,gt_to_model=dg);visible_info={}
 cache=Path(__file__).resolve().parents[1]/'results/ground_truth/gt_depth_mapping_180.npz';posesfile=cache.parent/'mapping_gt_tum.txt'
 if cache.exists() and posesfile.exists():
  from mathutils import Quaternion
  z=np.load(cache);depth=z['truth_z_m'];uv=z['pixel_uv'];valid=np.isfinite(depth)&(depth>=.1)&(depth<=30);idx=np.flatnonzero(valid);rng=np.random.default_rng(20260925);idx=rng.choice(idx,min(a.samples,len(idx)),replace=False);fi,pi=np.unravel_index(idx,depth.shape);rows=np.loadtxt(posesfile);rays=np.column_stack([(uv[pi,0]-640)/762.8,(uv[pi,1]-480)/762.8,np.ones(len(pi))]);vp=np.empty_like(rays)
  for k in np.unique(fi):
   mask=fi==k;R=np.array(Quaternion(tuple(rows[k,[7,4,5,6]])).to_matrix());vp[mask]=(rays[mask]*depth[k,pi[mask],None])@R.T+rows[k,1:4]
  vd=np.array([bm.find_nearest(Vector(x))[3] for x in vp]);np.savez_compressed(out/'observed_gt_surface_distances.npz',points=vp,distances_m=vd);visible_info={'observed_gt_to_model':stats(vd),'observed_sampling':'uniform over fixed valid GT image-ray hits across180frames; observation-weighted, not surface-area weighted'}
 res={'model':a.model,'gt_usd':a.gt_usd,'model_vertices':len(mv),'model_triangles':len(mt),'gt_vertices':len(gv),'gt_triangles':len(gt),'model_bounds_m':model_bounds,'gt_bounds_m':gt_bounds,'samples_each':a.samples,'alignment':'single supplied global transform; no ICP','model_to_gt':stats(dm),'gt_to_model':stats(dg),'symmetric_chamfer_mean_m':float((dm.mean()+dg.mean())/2)};res.update(visible_info);(out/'surface_metrics.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
if __name__=='__main__':main()
