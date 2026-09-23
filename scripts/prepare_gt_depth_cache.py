#!/usr/bin/env python3
"""Copy the existing evaluation-only 180-view z-depth cache into this workspace."""
import argparse, hashlib, json, shutil
from pathlib import Path
import numpy as np

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workspace',default='/home/hchen/Documents/astraBlenderTest/world_model_blog'); ap.add_argument('--source',default='/home/hchen/Documents/astraBlenderTest/vio-reconstruction/delivery/vipe-recon/evaluation/vipe_depth_samples.npz'); a=ap.parse_args()
    src=Path(a.source); out=Path(a.workspace)/'results/ground_truth/gt_depth_mapping_180.npz'; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,out)
    z=np.load(out); assert set(['truth_z_m','pixel_uv','timestamps_ns']).issubset(z.files); assert z['truth_z_m'].shape==(180,19200)
    meta={'path':str(out),'source_path':str(src),'source_sha256':digest(src),'copied_sha256':digest(out),'arrays':{k:list(z[k].shape) for k in z.files},'depth_field':'truth_z_m','depth_axis':'camera optical z-depth in metres','pixel_uv_convention':'(u,v), source image resolution 1280x960','evaluation_only':True,'modeler_access':'forbidden'}
    (out.with_suffix('.json')).write_text(json.dumps(meta,indent=2)+'\n'); print(json.dumps(meta,indent=2))
if __name__=='__main__': main()
