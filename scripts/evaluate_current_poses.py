"""Unified current-run pose metrics and global mapping-frame registration."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from src.evaluation.pose import read_tum,pose_metrics,align_poses
GT=ROOT/'results/ground_truth/mapping_gt_tum.txt';gt=read_tum(GT);out=ROOT/'results/evaluation/pose/current';out.mkdir(parents=True,exist_ok=True)
run=ROOT/'experiments/world_lobby/M2/vipe_full_20260923';v=np.load(run/'camera.npz');allp=np.column_stack([v['timestamps_ns']/1e9,v['camera_to_world'][:,:3,3],Rotation.from_matrix(v['camera_to_world'][:,:3,:3]).as_quat()]);m2=allp[::50];assert len(m2)==180
m3=read_tum(ROOT/'experiments/world_lobby/M3/openvins_20260923/openvins_camera_pose_180.tum');b2=read_tum(ROOT/'data/packets/B2/camera.tum');arrays={'M2':m2,'M3':m3,'B2':b2};rows=[]
for name,pred in arrays.items():
 native=pose_metrics(pred,gt,'se3');sim=pose_metrics(pred,gt,'sim3');common=pose_metrics(pred[pred[:,0]>=gt[5,0]-1e-6],gt[5:],'se3');item={'method_id':name,'pose_count':len(pred),'frame_coverage':len(pred)/180,'native_se3':native,'common175_se3':common,'sim3_diagnostic':sim,'shared_by':{'M2':['B1'],'M3':['B2p'],'B2':[]}[name]};rows.append(item);np.savetxt(out/f'{name}_native.tum',pred,fmt='%.12f');(out/f'{name}_registration.json').write_text(json.dumps({'transform':native['T_pred_to_gt'],'scope':'all valid fixed mapping samples; global SE3; apply same transform to mesh/depth/holdout'},indent=2)+'\n')
(out/'report.json').write_text(json.dumps({'methods':rows,'M1':'NA: Astra has no native trajectory estimator','M4':'GT pose input, not estimated error','GT_file':str(GT),'baseline_notes':'B1 shares M2 trajectory; B2p shares M3. B2 calibrated RGB-only 4-view predictions with overlap-SE3 chaining.'},indent=2)+'\n')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(12.8,5.2));colors={'M2':'#267bbd','M3':'#c94d40','B2':'#9c6abc'}
for row in rows:
 name=row['method_id'];a,T=align_poses(arrays[name],gt,'se3');axes[0].plot(a[:,1],a[:,2],color=colors[name],lw=1.7,label={'M2':'M2 / B1: ViPE','M3':'M3 / B2p: OpenVINS','B2':'B2: MapAnything'}[name]);g=np.column_stack([np.interp(a[:,0],gt[:,0],gt[:,j]) for j in (1,2,3)]);axes[1].plot(a[:,0]-gt[0,0],np.linalg.norm(a[:,1:4]-g,axis=1),color=colors[name],lw=1.5,label=name)
axes[0].plot(gt[:,1],gt[:,2],color='#182a25',lw=2.2,label='GT / M4 input');axes[0].set(xlabel='x (m)',ylabel='y (m)',title='One global SE(3) per estimated trajectory');axes[0].set_aspect('equal');axes[0].legend(fontsize=8);axes[1].set(xlabel='elapsed time (s)',ylabel='translation error (m)',title='Position error through the capture');axes[1].legend();
for ax in axes:ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('M1 has no native camera trajectory. M4 receives GT poses.',fontsize=11,y=.99);fig.tight_layout();fig.savefig(ROOT/'figures/current_trajectories.png',dpi=190);fig.savefig(ROOT/'figures/current_trajectories.svg');print(json.dumps([{k:r[k] for k in ('method_id','pose_count','frame_coverage')}|{'ate_m':r['native_se3']['translation_m']['rmse'],'rotation_deg':r['native_se3']['rotation_deg']['rmse']} for r in rows],indent=2))
