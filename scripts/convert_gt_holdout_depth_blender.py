#!/usr/bin/env python3
"""Convert Blender compositor Depth.V ray distance to optical z-depth."""
import argparse,json,glob,shutil
from pathlib import Path
import numpy as np
import OpenImageIO as oiio

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--fx',type=float,default=381.4); ap.add_argument('--fy',type=float,default=381.4); ap.add_argument('--cx',type=float,default=320); ap.add_argument('--cy',type=float,default=240); a=ap.parse_args(); root=Path(a.root); files=sorted(root.glob('_rgb.png/**/holdout_*_z.exr'))
    if len(files)!=20: raise RuntimeError(f'expected 20 compositor EXR files, found {len(files)}')
    yy,xx=np.mgrid[0:480,0:640]; rz=np.ones_like(xx,dtype=np.float32); norm=np.sqrt(((xx-a.cx)/a.fx)**2+((yy-a.cy)/a.fy)**2+1); factor=rz/norm
    rec=[]
    for src in files:
        f=oiio.ImageInput.open(str(src)); spec=f.spec();
        if tuple(spec.channelnames)!=('Depth.V',): raise RuntimeError(f'{src}: expected Depth.V, got {spec.channelnames}')
        ray=f.read_image(format=oiio.FLOAT)[:,:,0]; z=ray*factor; stem=src.name.replace('_z.exr',''); np.save(root/(stem+'_zdepth.npy'),z.astype(np.float32)); shutil.copy2(src,root/src.name); rec.append({'ray_exr':str(src),'ray_channel':'Depth.V','zdepth_npy':str(root/(stem+'_zdepth.npy')),'ray_min_m':float(np.nanmin(ray)),'ray_max_m':float(np.nanmax(ray)),'z_min_m':float(np.nanmin(z)),'z_max_m':float(np.nanmax(z))})
    m=json.loads((root/'manifest.json').read_text()); m['depth_axis']='optical_z_depth_m'; m['depth_source']='Blender compositor Depth.V ray distance converted by normalized pinhole ray z component'; m['depth_intrinsics']=[a.fx,a.fy,a.cx,a.cy]; m['depth_files']=rec; (root/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__': main()
