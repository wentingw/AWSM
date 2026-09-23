"""Depth metrics with explicit invalid-prediction accounting."""
from __future__ import annotations
import numpy as np

def depth_metrics(pred, gt, valid=None, missing_penalty_m=None):
    p=np.asarray(pred,float); g=np.asarray(gt,float)
    if p.shape != g.shape: raise ValueError(f"shape mismatch {p.shape} vs {g.shape}")
    domain=np.isfinite(g)&(g>0)
    if valid is not None: domain &= np.asarray(valid,bool)
    finite=np.isfinite(p)&(p>0); good=domain&finite; invalid=domain&~finite
    if not np.any(domain): raise ValueError("no valid GT depth")
    d=np.abs(p[good]-g[good]); absrel=d/np.maximum(g[good],1e-8)
    ratio=np.maximum(p[good]/g[good],g[good]/p[good])
    penalty=float(missing_penalty_m if missing_penalty_m is not None else np.nanmax(g[domain]))
    allerr=np.full(np.count_nonzero(domain),penalty); allerr[finite[domain]]=np.abs(p[domain][finite[domain]]-g[domain][finite[domain]])
    return {"pixels_domain":int(domain.sum()),"pixels_valid":int(good.sum()),"valid_coverage":float(good.sum()/domain.sum()),"invalid_rate":float(invalid.sum()/domain.sum()),"absrel":float(np.mean(absrel)) if good.any() else None,"rmse_m":float(np.sqrt(np.mean(d*d))) if good.any() else None,"delta1":float(np.mean(ratio<1.25)) if good.any() else 0.0,"missing_penalty_mae_m":float(np.mean(allerr))}
