"""CPU point-cloud geometry metrics; mesh sampling can be done upstream."""
from __future__ import annotations
import numpy as np
try:
    from scipy.spatial import cKDTree
except Exception:
    cKDTree=None

def pointcloud_metrics(pred, gt, thresholds=(.05,.1,.2)):
    p=np.asarray(pred,float); g=np.asarray(gt,float)
    if p.ndim!=2 or g.ndim!=2 or p.shape[1]!=3 or g.shape[1]!=3: raise ValueError("points must be Nx3")
    if cKDTree is None: raise RuntimeError("scipy is required for CPU nearest-neighbour geometry evaluation")
    dp=cKDTree(g).query(p,k=1)[0]; dg=cKDTree(p).query(g,k=1)[0]
    out={"pred_to_gt_mean_m":float(dp.mean()),"gt_to_pred_mean_m":float(dg.mean()),"chamfer_mean_m":float((dp.mean()+dg.mean())/2),"pred_to_gt_rmse_m":float(np.sqrt(np.mean(dp*dp)),),"gt_to_pred_rmse_m":float(np.sqrt(np.mean(dg*dg)),)}
    for t in thresholds: out[f"accuracy_{t:g}m"] = float(np.mean(dp<=t)); out[f"completeness_{t:g}m"] = float(np.mean(dg<=t))
    return out
