#!/usr/bin/env python3
"""Independent MapAnything depth runner for blog M4/B2 experiments.

M4 consumes RGB, one fixed calibration, and evaluation-only camera poses.
B2 consumes RGB and the same fixed calibration, with no pose or truth path
opened.  The script writes per-view depth_z, masks, confidence, poses (when
provided), and an auditable manifest.  It deliberately does not import the
legacy vio-reconstruction/mapanything package.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, sys
from pathlib import Path
import numpy as np

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def quat(q):
    x,y,z,w=np.asarray(q,float); n=x*x+y*y+z*z+w*w
    if n < 1e-16: raise ValueError('zero quaternion')
    s=2/n
    return np.array([[1-s*(y*y+z*z),s*(x*y-z*w),s*(x*z+y*w)],
                     [s*(x*y+z*w),1-s*(x*x+z*z),s*(y*z-x*w)],
                     [s*(x*z-y*w),s*(y*z+x*w),1-s*(x*x+y*y)]])

def tum(path):
    out=[]
    for line in Path(path).read_text().splitlines():
        p=line.strip().replace(',',' ').split()
        if not p or p[0].startswith('#'): continue
        if len(p)!=8: raise ValueError(f'bad TUM row: {line}')
        t=float(p[0]); v=np.array([float(x) for x in p[1:]])
        T=np.eye(4); T[:3,:3]=quat(v[3:]); T[:3,3]=v[:3]; out.append((t,T))
    if not out: raise ValueError(f'empty pose file {path}')
    return out

def frame_rows(frames_csv, root):
    rows=[]
    with open(frames_csv,newline='') as f:
        for r in csv.DictReader(f):
            p=Path(r['original_rgb_absolute_path']) if r.get('original_rgb_absolute_path') else root/'inputs/cam0/data'/Path(r['image']).name
            rows.append({'keyframe_index':int(r.get('keyframe_index',len(rows))), 'source_frame_index':int(r.get('source_frame_index_zero_based',len(rows))), 'timestamp_ns':int(r['timestamp_ns']), 'image':p})
    return rows

def calibration(path):
    d=json.loads(Path(path).read_text()); fx,fy,cx,cy=d['intrinsics']
    K=np.array([[fx,0,cx],[0,fy,cy],[0,0,1]],np.float32)
    return K,d

def match_pose(rows, pose_path):
    ps=tum(pose_path); ts=np.array([x[0] for x in ps])
    for r in rows:
        t=r['timestamp_ns']/1e9; j=int(np.argmin(abs(ts-t))); err=abs(float(ts[j]-t))
        if err>2e-4: raise ValueError(f'pose mismatch {r["image"]} {err}s')
        r['input_pose']=ps[j][1]; r['pose_match_error_s']=err
    return rows

def infer(args, rows, K, mode, model=None):
    import torch
    from PIL import Image
    repo=Path(args.repo).resolve(); sys.path.insert(0,str(repo))
    from mapanything.models.mapanything.model import MapAnything
    from mapanything.utils.image import preprocess_inputs
    device=args.device or ('cuda' if torch.cuda.is_available() else 'cpu')
    if model is None: model=MapAnything.from_pretrained(args.checkpoint).to(device).eval()
    raw=[]
    for i,r in enumerate(rows):
        with Image.open(r['image']) as im: im=im.convert('RGB').copy()
        x={'img':im,'intrinsics':K.copy(),'idx':[i],'instance':[r['image'].name]}
        if mode in ('M3','M4'):
            x['camera_poses']=r['input_pose'].astype(np.float32); x['is_metric_scale']=True
        raw.append(x)
    views=preprocess_inputs(raw,resolution_set=args.resolution,norm_type='dinov2')
    pred=model.infer(views,memory_efficient_inference=True,minibatch_size=args.minibatch,use_amp=not args.no_amp,amp_dtype=args.amp_dtype,apply_mask=True,mask_edges=False,ignore_pose_inputs=False,ignore_pose_scale_inputs=False)
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True); (out/'images').mkdir(exist_ok=True)
    rec=[]
    for i,(r,p) in enumerate(zip(rows,pred)):
        def a(k): return p[k][0].detach().cpu().numpy()
        rgb=np.clip(a('img_no_norm')*255,0,255).astype('uint8'); Image.fromarray(rgb).save(out/'images'/f'{i:06d}.png')
        arr={'depth_z':a('depth_z').squeeze(-1).astype('float32'),'intrinsics':views[i]['intrinsics'][0].detach().cpu().numpy().astype('float32'),'predicted_intrinsics':a('intrinsics').astype('float32'),'confidence':a('conf').astype('float32'),'mask':a('mask').squeeze(-1).astype('uint8')}
        if mode in ('M3','M4'): arr['input_camera_pose']=r['input_pose'].astype('float32')
        if 'camera_poses' in p: arr['output_camera_pose']=a('camera_poses').astype('float32')
        if 'metric_scaling_factor' in p: arr['metric_scaling_factor']=a('metric_scaling_factor').astype('float32')
        np.savez_compressed(out/f'{i:06d}.npz',**arr)
        rec.append({'index':i,'keyframe_index':r['keyframe_index'],'source_frame_index':r['source_frame_index'],'timestamp_ns':r['timestamp_ns'],'image':str(r['image']),'data':f'{i:06d}.npz','processed_image':f'images/{i:06d}.png','pose_match_error_s':r.get('pose_match_error_s'),'depth_units':'metres' if mode in ('M3','M4') else 'native_model_output_scale','depth_shape':list(arr['depth_z'].shape)})
    manifest={'status':'complete','method':('GT camera pose + RGB + fixed intrinsics -> MapAnything' if mode=='M4' else 'OpenVINS metric pose + RGB + fixed intrinsics -> MapAnything' if mode=='M3' else 'RGB + fixed intrinsics -> MapAnything image-only'),'mode':mode,'ground_truth_used':mode=='M4','ground_truth_role':'camera pose input only' if mode=='M4' else ('OpenVINS pose input; no GT' if mode=='M3' else 'not opened'),'pose_convention':'OpenCV RDF cam2world','metric_scale_flag':mode in ('M3','M4'),'native_scale':mode=='B2','depth_units':'metres' if mode in ('M3','M4') else 'native_model_output_scale','resolution':args.resolution,'checkpoint':args.checkpoint,'frames':rec}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['M3','M4','B2'],required=True);p.add_argument('--frames-csv',type=Path,required=True);p.add_argument('--calibration',type=Path,required=True);p.add_argument('--poses',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--repo',default='/home/hchen/Documents/map-anything');p.add_argument('--checkpoint',default='facebook/map-anything');p.add_argument('--device');p.add_argument('--minibatch',type=int,default=1);p.add_argument('--resolution',type=int,choices=[518,512],default=518);p.add_argument('--amp-dtype',choices=['bf16','fp16','fp32'],default='bf16');p.add_argument('--no-amp',action='store_true');p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int)
    a=p.parse_args(); root=a.frames_csv.parent; rows=frame_rows(a.frames_csv,root); rows=rows[a.start:a.start+a.count if a.count else None]; K,cal=calibration(a.calibration)
    if a.mode in ('M3','M4'):
        if not a.poses: p.error('--poses required for M4')
        if a.mode=='M4' and 'ground_truth' not in a.poses.parts: raise SystemExit('M4 requires explicitly named ground_truth pose source')
        rows=match_pose(rows,a.poses)
    else:
        if a.poses: raise SystemExit('B2 forbids pose input')
    if not rows: raise SystemExit('no rows')
    m=infer(a,rows,K,a.mode); m['calibration']=cal; m['calibration_sha256']=sha(a.calibration); (a.output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n'); print(json.dumps({'status':m['status'],'mode':a.mode,'frames':len(rows),'output':str(a.output)}))
if __name__=='__main__': main()
