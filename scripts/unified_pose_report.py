#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evaluation.pose import read_tum,pose_metrics,align_poses
ROOT=Path("/home/hchen/Documents/astraBlenderTest");RUN=ROOT/"vio-reconstruction/runs/stable_orbit_20260921T044401";GT=ROOT/"vio-reconstruction/sessions/stable_orbit_20260921T044401/ground_truth/camera_tum.txt"
def npz_to_tum(p):
 z=np.load(p);P=z["camera_to_world"];q=Rotation.from_matrix(P[:,:3,:3]).as_quat();return np.column_stack([z["timestamps_ns"]/1e9,P[:,:3,3],q])
def interp_rows(a,t):
 t=np.asarray(t);p=np.column_stack([np.interp(t,a[:,0],a[:,i]) for i in (1,2,3)]);q=Slerp(a[:,0],Rotation.from_quat(a[:,4:8]))(t).as_quat();return np.column_stack([t,p,q])
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--out",default=str(ROOT/"world_model_blog/results/evaluation/pose"));a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True);gt=read_tum(GT)
 sources={"GT":(GT,"main_reference"),"M3_OpenVINS_full_valid":(ROOT/"world_model_blog/experiments/world_lobby/M3/openvins_20260923/openvins_camera_pose_images.tum","main_method_full_valid"),"M3b_SfM_IMU":(RUN/"accepted_estimate/metric_camera.tum","supplementary_historical"),"M3c_batchVIO":(RUN/"batch_vio_20260922/estimate/metric_camera.tum","supplementary_historical"),"ViPE_180":(RUN/"vipe_rgb_180_20260922/camera.npz","diagnostic_sparse"),"M1_RGB_COLMAP":(ROOT/"visual-recon/camera_rgb180/solve_v1/camera_rgb180_native.tum","diagnostic_posthoc_not_Astra")}
 rows=[]
 for name,(path,role) in sources.items():
  pred=npz_to_tum(path) if str(path).endswith(".npz") else read_tum(path);item={"method_id":name,"role":role,"source_path":str(path),"source_count":len(pred),"source_time_range_s":[float(pred[0,0]),float(pred[-1,0])],"native_se3":pose_metrics(pred,gt,"se3"),"sim3_supplement":pose_metrics(pred,gt,"sim3")}
  if name=="M3_OpenVINS_full_valid":
   common_path=ROOT/"world_model_blog/experiments/world_lobby/M3/openvins_20260923/openvins_camera_pose_180.tum";pred_common=read_tum(common_path);common_gt=gt[np.searchsorted(gt[:,0],pred_common[:,0])];item["common175"]={"source_path":str(common_path),"keyframe_indices":[5,179],"count":len(pred_common),"gt_timestamp_tolerance_max_s":float(np.max(np.abs(common_gt[:,0]-pred_common[:,0]))),"native_se3":pose_metrics(pred_common,common_gt,"se3"),"sim3_supplement":pose_metrics(pred_common,common_gt,"sim3")};np.savetxt(out/"M3_OpenVINS_common175.tum",pred_common,fmt="%.12g")
  rows.append(item)
 (out/"unified_pose_report.json").write_text(json.dumps({"gt_path":str(GT),"coordinate_note":"global gauge metrics; M1 COLMAP is post-hoc diagnostic, not Astra pose","methods":rows},indent=2)+"\n");plot(out,rows,gt)
def plot(out,rows,gt):
 import matplotlib;matplotlib.use("Agg");import matplotlib.pyplot as plt
 fig,ax=plt.subplots(1,2,figsize=(13,5));colors=plt.cm.tab10(np.linspace(0,1,len(rows)))
 for c,r in zip(colors,rows):
  if r["method_id"]=="GT":continue
  p=read_tum(r["source_path"]) if not r["source_path"].endswith(".npz") else npz_to_tum(r["source_path"]);al,_=align_poses(p,gt,"se3");ax[0].plot(al[:,1],al[:,2],label=r["method_id"],color=c,lw=1)
 ax[0].plot(gt[:,1],gt[:,2],"k",label="GT",lw=2);ax[0].set_title("Global SE(3)-aligned XY trajectory");ax[0].set_aspect("equal");ax[0].legend(fontsize=7);ax[0].set_xlabel("x (m)");ax[0].set_ylabel("y (m)")
 for c,r in zip(colors,rows):
  if r["method_id"]=="GT":continue
  p=read_tum(r["source_path"]) if not r["source_path"].endswith(".npz") else npz_to_tum(r["source_path"]);q=np.interp(gt[:,0],p[:,0],np.linalg.norm(p[:,1:4],axis=1),left=np.nan,right=np.nan);ax[1].plot(gt[:,0]-gt[0,0],q,label=r["method_id"],color=c,lw=1)
 ax[1].set_title("Trajectory position norm");ax[1].set_xlabel("time (s)");ax[1].set_ylabel("norm (m)");fig.tight_layout();fig.savefig(out/"unified_trajectory_xy.png",dpi=180);plt.close(fig)
if __name__=="__main__":main()
