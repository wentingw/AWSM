import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evaluation.pose import pose_metrics

def trajectory():
 t=np.arange(6.,dtype=float); xyz=np.column_stack([t,.2*t*t,.1*np.sin(t)]); return np.column_stack([t,xyz,np.tile([0.,0.,0.,1.],(6,1))])
def test_sim3_and_rpe():
 p=trajectory(); R=Rotation.from_euler("zyx",[20,10,5],degrees=True).as_matrix(); q=Rotation.from_matrix(R).as_quat(); g=p.copy();g[:,1:4]=3*(p[:,1:4]@R.T)+[2,-1,4];g[:,4:]=q; r=pose_metrics(p,g,"sim3"); assert r["translation_m"]["rmse"]<1e-8; assert r["rpe"]["1.0"]["translation_m"]["rmse"]<1e-8; assert r["rpe"]["1.0"]["rotation_deg"]["rmse"]<1e-8
def test_quaternion_sign_flip():
 p=trajectory();g=p.copy();g[::2,4:]*=-1; assert pose_metrics(g,p,"se3")["rotation_deg"]["rmse"]<1e-8
def test_timestamp_rounding_endpoints():
 p=trajectory();g=p.copy();g[-1,0]-=2e-9
 assert pose_metrics(p,g,"se3")["n"]==len(p)

def test_no_overlap_rejected():
 p=trajectory();g=p.copy();g[:,0]+=100
 try: pose_metrics(p,g,"se3")
 except ValueError: return
 raise AssertionError("expected no-overlap rejection")
if __name__=="__main__":
 test_timestamp_rounding_endpoints();test_sim3_and_rpe();test_quaternion_sign_flip();test_no_overlap_rejected();print("PASS")
