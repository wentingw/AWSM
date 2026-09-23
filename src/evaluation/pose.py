"""Pose I/O and auditable SE(3)/Sim(3) gauge evaluation."""
from __future__ import annotations
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def read_tum(path):
    a=np.loadtxt(path,comments="#",ndmin=2)
    if a.shape[1]!=8: raise ValueError(f"expected 8 TUM columns, got {a.shape}")
    if not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0): raise ValueError("TUM timestamps must be finite and strictly increasing")
    q=a[:,4:8]; n=np.linalg.norm(q,axis=1)
    if np.any(n<1e-12): raise ValueError("zero-norm quaternion")
    a=a.copy(); a[:,4:8]=q/n[:,None]; return a

def _canonical_quats(q):
 q=np.asarray(q,float).copy()
 for i in range(1,len(q)):
  if np.dot(q[i-1],q[i])<0:q[i]*=-1
 return q

def _interp(a,t):
    t=np.asarray(t,float)
    if np.any(t<a[0,0]-1e-7) or np.any(t>a[-1,0]+1e-7): raise ValueError("interpolation requested outside timestamp overlap")
    t=np.clip(t,a[0,0],a[-1,0]); xyz=np.column_stack([np.interp(t,a[:,0],a[:,i]) for i in (1,2,3)])
    return xyz,Slerp(a[:,0],Rotation.from_quat(_canonical_quats(a[:,4:8])))(t).as_matrix()

def _umeyama(x,y,scale=False):
    mx,my=x.mean(0),y.mean(0); X,Y=x-mx,y-my; U,S,Vt=np.linalg.svd((Y.T@X)/len(x)); D=np.eye(3); D[-1,-1]=np.sign(np.linalg.det(U@Vt)); R=U@D@Vt
    s=float(np.sum(S*np.diag(D))/max(np.sum(X*X)/len(x),1e-15)) if scale else 1.0; A=np.eye(4); A[:3,:3]=s*R; A[:3,3]=my-s*R@mx; return A

def align_poses(pred,gt,mode="se3"):
    lo=max(pred[0,0],gt[0,0]); hi=min(pred[-1,0],gt[-1,0])
    if hi-lo<1e-9: raise ValueError("pose trajectories have no timestamp overlap")
    keep=(pred[:,0]>=lo-1e-7)&(pred[:,0]<=hi+1e-7); p=pred[keep]; pp,_=_interp(p,p[:,0]); pg,_=_interp(gt,p[:,0]); T=_umeyama(pp,pg,scale=mode.lower()=="sim3")
    aligned=pred.copy(); aligned[:,1:4]=pred[:,1:4]@T[:3,:3].T+T[:3,3]; return aligned,T

def _stats(x):
    x=np.asarray(x,float); return {"count":int(x.size),"mean":float(np.mean(x)),"rmse":float(np.sqrt(np.mean(x*x))),"median":float(np.median(x)),"p90":float(np.percentile(x,90))}

def pose_metrics(pred,gt,align="se3",rpe_seconds=(1.0,10.0)):
    pred=np.asarray(pred,float); gt=np.asarray(gt,float); aligned,T=align_poses(pred,gt,align); lo=max(aligned[0,0],gt[0,0]); hi=min(aligned[-1,0],gt[-1,0]); t=aligned[(aligned[:,0]>=lo-1e-7)&(aligned[:,0]<=hi+1e-7),0]
    if len(t)==0: raise ValueError("pose trajectories have no evaluable overlap")
    pp,_=_interp(aligned,t); pg,Rg=_interp(gt,t); Rp0=_interp(aligned,t)[1]; s=max(abs(np.linalg.det(T[:3,:3]))**(1/3),1e-15); Rgauge=T[:3,:3]/s; Rp=np.einsum("ij,njk->nik",Rgauge,Rp0)
    trans=np.linalg.norm(pp-pg,axis=1); c=np.clip((np.trace(np.einsum("nij,njk->nik",Rg.transpose(0,2,1),Rp),axis1=1,axis2=2)-1)/2,-1,1); rot=np.degrees(np.arccos(c)); out={"align":align,"T_pred_to_gt":T.tolist(),"gauge_rotation":Rgauge.tolist(),"gauge_scale":float(s),"translation_m":_stats(trans),"rotation_deg":_stats(rot),"n":int(len(t)),"rpe":{}}
    for dt in rpe_seconds:
        ts=t[t+dt<=hi+1e-7]
        if len(ts)==0: out["rpe"][str(dt)]=None; continue
        p0,R0=_interp(pred,ts); p1,R1=_interp(pred,ts+dt); g0,G0=_interp(gt,ts); g1,G1=_interp(gt,ts+dt); ep=s*np.einsum("nij,nj->ni",R0.transpose(0,2,1),p1-p0); eg=np.einsum("nij,nj->ni",G0.transpose(0,2,1),g1-g0); Rpred_rel=np.einsum("nij,njk->nik",R0.transpose(0,2,1),R1); Rgt=np.einsum("nij,njk->nik",G0.transpose(0,2,1),G1); er=Rotation.from_matrix(np.einsum("nij,njk->nik",Rgt.transpose(0,2,1),Rpred_rel)).magnitude(); out["rpe"][str(dt)]={"translation_m":_stats(np.linalg.norm(ep-eg,axis=1)),"rotation_deg":_stats(np.degrees(er))}
    return out
