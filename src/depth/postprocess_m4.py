#!/usr/bin/env python3
"""Deduplicate M4 joint windows and fuse depth using input world-gauge poses."""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image

def main():
    p=argparse.ArgumentParser(); p.add_argument('root',type=Path); p.add_argument('--pixel-step',type=int,default=4); p.add_argument('--voxel',type=float,default=.04); a=p.parse_args()
    root=a.root; chosen={}; windows=[]
    for d in sorted(root.glob('window_[0-9][0-9][0-9]')):
        mp=d/'manifest.json'
        if not mp.exists(): continue
        m=json.loads(mp.read_text()); windows.append(d.name)
        for f in m.get('frames',[]):
            # Earliest-window rule: first occurrence wins; overlap never gets
            # aligned or averaged, and no GT is used for selection.
            chosen.setdefault(int(f['timestamp_ns']), {'window':d.name,'frame':f})
    if len(chosen)!=180: raise SystemExit(f'expected 180 unique timestamps, found {len(chosen)}')
    records=[]; points=[]; colors=[]
    for i,(ts,item) in enumerate(sorted(chosen.items())):
        d=item['window']; f=item['frame']; npz=root/d/f['data']; img=root/d/f['processed_image']
        with np.load(npz) as z:
            depth=z['depth_z']; K=z['intrinsics']; T=z['input_camera_pose']; mask=z['mask'].astype(bool)
            yy,xx=np.mgrid[0:depth.shape[0]:a.pixel_step,0:depth.shape[1]:a.pixel_step]; zz=depth[yy,xx]
            valid=mask[yy,xx]&np.isfinite(zz)&(zz>.1)&(zz<40)
            xyz=np.stack([(xx-K[0,2])*zz/K[0,0],(yy-K[1,2])*zz/K[1,1],zz],axis=-1)[valid]
            world=xyz@T[:3,:3].T+T[:3,3]; rgb=np.array(Image.open(img).convert('RGB'))[yy,xx][valid]
            points.append(world); colors.append(rgb)
            records.append({'index':i,'timestamp_ns':ts,'source_window':d,'source_data':str(npz.relative_to(root)),'processed_image':str(img.relative_to(root)),'input_camera_pose':T.astype(float).tolist(),'depth_shape':list(depth.shape),'valid_sample_fraction':float(valid.mean()),'depth_units':'metres','pose_convention':'OpenCV RDF cam2world','world_gauge':'M4 GT camera world; used only as declared input'})
    xyz=np.concatenate(points); rgb=np.concatenate(colors); vox=np.floor(xyz/a.voxel).astype(np.int32); _,ix=np.unique(vox,axis=0,return_index=True); xyz=xyz[ix].astype('<f4'); rgb=rgb[ix].astype('u1')
    cloud=root/'observed_scene_metric.ply'; arr=np.empty(len(xyz),dtype=[('x','<f4'),('y','<f4'),('z','<f4'),('red','u1'),('green','u1'),('blue','u1')]);
    for i,k in enumerate(('x','y','z')): arr[k]=xyz[:,i]
    for i,k in enumerate(('red','green','blue')): arr[k]=rgb[:,i]
    with cloud.open('wb') as f:
        f.write(f'ply\nformat binary_little_endian 1.0\nelement vertex {len(arr)}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n'.encode()); f.write(arr.tobytes())
    out={'status':'complete','method':'M4 GT camera pose + RGB -> MapAnything; joint window=4 overlap=2','windows':windows,'window_size':4,'overlap':2,'unique_frames':len(records),'deduplication':'earliest-window wins by timestamp_ns','ground_truth_used':True,'ground_truth_role':'camera pose input only; no GT depth/mesh','pose_source':'/home/hchen/Documents/astraBlenderTest/vio-reconstruction/sessions/stable_orbit_20260921T044401/ground_truth/camera_tum.txt','pose_for_fusion':'input_camera_pose only; output_camera_pose ignored','depth_units':'metres','coordinate_frame':'input GT camera world gauge','cloud':{'path':cloud.name,'points_after_voxel':len(xyz),'voxel_m':a.voxel,'raw_points':int(sum(len(x) for x in points))},'frames':records}
    (root/'modeling_input_manifest.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({k:v for k,v in out.items() if k!='frames'},indent=2))
if __name__=='__main__': main()
