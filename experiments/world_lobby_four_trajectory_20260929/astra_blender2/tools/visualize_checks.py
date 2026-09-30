"""Pair original RGB with actual renders and visualize own-input depth residuals."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
import matplotlib
matplotlib.use('Agg')
from matplotlib import colormaps

def color(a,maximum):
    mask=np.isfinite(a);v=colormaps['turbo'](np.clip(np.nan_to_num(a)/maximum,0,1))[:,:,:3];v[~mask]=0
    return Image.fromarray((v*255).astype(np.uint8))
def boundary(z):
    good=np.isfinite(z);base=np.nan_to_num(z)
    dx=np.zeros_like(good);dy=dx.copy()
    dx[:,1:]=good[:,1:]&good[:,:-1]&(np.abs(base[:,1:]-base[:,:-1])>np.maximum(.15,.05*base[:,1:]))
    dy[1:]=good[1:]&good[:-1]&(np.abs(base[1:]-base[:-1])>np.maximum(.15,.05*base[1:]))
    return dx|dy
def main():
    p=argparse.ArgumentParser();p.add_argument('--method-dir',type=Path,required=True);p.add_argument('--packet',type=Path,required=True);p.add_argument('--version',type=int,required=True);a=p.parse_args()
    out=a.method_dir/'checks'/f'v{a.version}';report=json.loads((out/'paired_report.json').read_text());frames=json.loads(a.packet.read_text())['frames'];stats=[]
    for r in report['frames']:
        i=r['sample_index'];n=np.load(out/f'{i:04d}_depth.npz');z=n['model_z_m']
        rgb=Image.open(frames[i]['rgb']).convert('RGB').resize((640,480),Image.Resampling.LANCZOS);pred=Image.open(out/f'{i:04d}_rgb.png').convert('RGB')
        panels=[('Input RGB',rgb),('Blender RGB',pred),('Model optical Z: 0-20 m',color(z,20))]
        item={'sample_index':i}
        if 'input_da3_z_m' in n:
            ref=n['input_da3_z_m'];domain=n['input_valid_domain'];valid=domain&np.isfinite(z)&(z>=.1)&(z<=30)
            absdiff=np.where(valid,np.abs(z-ref),np.nan);reldiff=absdiff/ref
            signed=np.where(valid,z-ref,np.nan)
            boundaries=np.zeros((480,640,3),np.uint8);br=boundary(ref);bm=boundary(z);boundaries[br]=[255,80,80];boundaries[bm]=[70,170,255];boundaries[br&bm]=[255,255,255]
            masks=np.zeros((480,640,3),np.uint8);masks[domain]=[255,80,80];masks[valid]=[70,210,90]
            panels.extend([('Input DA3 optical Z: 0-20 m',color(ref,20)),('Absolute error: 0-3 m',color(absdiff,3)),('Relative error: 0-100%',color(reldiff,1)),('GT-free input domain: green hit / red miss',Image.fromarray(masks)),('Depth edges: red input / blue model',Image.fromarray(boundaries))])
            close=binary_dilation(bm,iterations=2);item.update(input_edge_pixels=int(br.sum()),model_edge_pixels=int(bm.sum()),input_edge_matched_within_2px=float((br&close).sum()/max(1,br.sum())),median_signed_residual_m=float(np.nanmedian(signed)))
            np.savez_compressed(out/f'{i:04d}_errors.npz',signed_z_residual_m=signed,absolute_error_m=absdiff,relative_error=reldiff,input_domain=domain,model_valid=valid,input_edges=br,model_edges=bm)
        canvas=Image.new('RGB',(1280,510*((len(panels)+1)//2)),'white');draw=ImageDraw.Draw(canvas)
        for j,(label,img) in enumerate(panels):
            x=j%2*640;y=j//2*510;draw.text((x+8,y+6),f'sample {i} | {label}',fill='black');canvas.paste(img,(x,y+30))
        canvas.save(out/f'{i:04d}_comparison.jpg',quality=90);stats.append(item)
    (out/'boundary_checks.json').write_text(json.dumps(stats,indent=2)+'\n')
    print('Saved',len(stats),'paired comparison sheets')
if __name__=='__main__':main()
