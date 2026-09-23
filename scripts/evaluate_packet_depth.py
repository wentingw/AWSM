#!/usr/bin/env python3
"""Native optical-Z depth evaluation on fixed GT-only image rays.

MapAnything preprocessing changes intrinsics by a known resize/crop, so original
pixels are mapped using input calibration and processed input intrinsics.
Never uses the historical cache's joint ViPE validity mask.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.depth import depth_metrics

def main():
 p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 packet=json.loads(a.packet.read_text());gtpath=ROOT/'results/ground_truth/gt_depth_mapping_180.npz';gt=np.load(gtpath);uv=gt['pixel_uv'];truth=gt['truth_z_m'];domain=np.isfinite(truth)&(truth>=.1)&(truth<=30)
 c=json.loads((ROOT/'data/world_lobby/calibration/camera_imu.json').read_text());fx,fy,cx,cy=c['intrinsics'];rays=np.array([(uv[:,0]-cx)/fx,(uv[:,1]-cy)/fy,np.ones(len(uv))]);pred=np.full(truth.shape,np.nan);rows=[]
 for f in packet['frames']:
  k=f['keyframe_index'];assert abs(f['timestamp_ns']-int(gt['timestamps_ns'][k]))<=1
  if 'geometry' not in f:continue
  z=np.load(f['geometry']);K=z['intrinsics'];coords=K@rays;x,y=coords[:2];d=z['depth_z_m'];
  if packet['method_id']=='M2':
   assert d.shape==(960,1280);x,y=uv.T # ViPE depth pixels retain original RGB coordinates
  v=z['valid_mask'].astype(bool)&np.isfinite(d)&(d>0)
  # The processed image domain is part of prediction coverage, never GT mask.
  sample=map_coordinates(d,[y,x],order=1,mode='constant',cval=np.nan,prefilter=False)
  valid=map_coordinates(v.astype(float),[y,x],order=1,mode='constant',cval=0,prefilter=False)>.999
  sample[~valid]=np.nan;pred[k]=sample;rows.append({'keyframe_index':k,**depth_metrics(sample,truth[k],domain[k],missing_penalty_m=30)})
 full=depth_metrics(pred,truth,domain,missing_penalty_m=30);common=depth_metrics(pred[5:],truth[5:],domain[5:],missing_penalty_m=30)
 out=a.out;out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/'paired_depth.npz',prediction_z_m=pred,ground_truth_z_m=truth,gt_valid_domain=domain,pixel_uv=uv)
 report={'method_id':packet['method_id'],'kind':'native_frontend_depth_not_rendered_model','packet_sha256':hashlib.sha256(a.packet.read_bytes()).hexdigest(),'gt_cache_sha256':hashlib.sha256(gtpath.read_bytes()).hexdigest(),'scale_fit':False,'GT_mask':'finite truth optical-Z in [0.1,30] metres; no prediction-dependent masking','sampling':'19200 original-pixel rays/frame; bilinear input-depth lookup after exact preprocessing transform; invalid bilinear support rejected','all180':full,'common175':common,'per_frame':rows,'missing_prediction_penalty_m':30}
 (out/'depth_metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('per_frame',)}))
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 ids=[0,36,72,108,144];fig,axes=plt.subplots(2,5,figsize=(15,5))
 shape=tuple(gt['sampled_grid_shape']);errors=np.abs(pred-truth)
 for j,k in enumerate(ids):
  axes[0,j].imshow(pred[k].reshape(shape),vmin=0,vmax=15,cmap='viridis');axes[0,j].set_title(f'frame {k}: predicted Z')
  im=axes[1,j].imshow(errors[k].reshape(shape),vmin=0,vmax=2,cmap='magma');axes[1,j].set_title('absolute depth error (m)')
  for ax in axes[:,j]:ax.axis('off')
 fig.colorbar(im,ax=axes[1,:].tolist(),shrink=.65,label='m');fig.savefig(out/'depth_error_five_views.png',dpi=160,bbox_inches='tight');plt.close(fig)
if __name__=='__main__':main()
