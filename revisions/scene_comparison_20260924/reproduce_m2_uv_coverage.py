#!/usr/bin/env python3
"""Reproduce M2 ViPE UV-coverage branch from frozen artifacts.

This is an independent CPU/NumPy reproduction of SLAMMap.project_map's
non-infill occupancy logic. It does not run ViPE or alter experiment files.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "experiments/world_lobby/M2/vipe_full_20260923"
MAP_PATH = RUN / "slam_map.pt"
CAM_PATH = RUN / "camera.npz"
OUT = Path(__file__).with_name("m2_uv_coverage_reproduction.json")

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def main():
    payload=torch.load(MAP_PATH,map_location="cpu",weights_only=False)
    xyz=payload["dense_disp_xyz"].numpy()
    pack=payload["dense_disp_packinfo"].numpy().astype(np.int64)[:,0,:]
    keyframes=np.asarray(payload["dense_disp_frame_inds"],dtype=np.int64)
    cam=np.load(CAM_PATH)
    c2w=cam["camera_to_world"]
    fx,fy,cx,cy=cam["intrinsics"][:4].astype(float)
    H,W=960,1280
    scores=[]
    for t in range(0,len(c2w),10):
        # Exact project_map neighborhood: searchsorted + tstamp_nn=3.
        right=min(int(np.searchsorted(keyframes,t))+3,len(keyframes)-1)
        left=max(right-6,0)
        chunks=[xyz[int(pack[k,0]):int(pack[k,0]+pack[k,1])] for k in range(left,right+1)]
        points=np.concatenate(chunks,axis=0)
        w2c=np.linalg.inv(c2w[t])
        q=points@w2c[:3,:3].T+w2c[:3,3]
        z=q[:,2]
        valid=z>0
        u=fx*q[:,0]/z+cx; v=fy*q[:,1]/z+cy
        valid &= (u>0)&(u<W)&(v>0)&(v<H)
        occupied=np.zeros((10,10),dtype=bool)
        occupied[np.clip((v[valid]/H*10).astype(np.int64),0,9),
                 np.clip((u[valid]/W*10).astype(np.int64),0,9)] = True
        scores.append(float(occupied.mean()))
    result={
      "status":"complete",
      "method":"independent_cpu_numpy_reproduction_of_SLAMMap.project_map_non_infill_uv_score",
      "approximation_note":"Not direct map.project_map call: frozen slam_map.pt stores a dict and project_map requires CUDA. Logic is mirrored for neighborhood selection, world_to_camera transform, pinhole projection, valid-point tests and 10x10 occupancy.",
      "inputs":{"slam_map":str(MAP_PATH),"slam_map_sha256":sha256(MAP_PATH),"camera_npz":str(CAM_PATH),"camera_npz_sha256":sha256(CAM_PATH)},
      "map_points":int(len(xyz)),"map_keyframes":int(len(keyframes)),"trajectory_frames":int(len(c2w)),"sample_stride":10,
      "min_uv_score":float(min(scores)),"mean_uv_score":float(np.mean(scores)),"p10_uv_score":float(np.percentile(scores,10)),
      "threshold":0.3,"keyframe_branch":"PriorDA (score > threshold)",
      "rest_branch":"PriorDA because rest invocation skips index 0, so local min_uv_score remains initialized to 1.0; it does not inherit or recompute keyframe score.",
      "no_model_rerun":True,"frozen_artifacts_modified":False
    }
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
