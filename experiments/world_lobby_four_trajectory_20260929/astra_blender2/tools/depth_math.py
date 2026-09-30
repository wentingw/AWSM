"""Generic optical-Z sampling and metrics. No scene-specific data."""
import numpy as np

def pixel_grid():
    u,v=np.meshgrid(np.arange(4,1280,8),np.arange(4,960,8))
    return np.column_stack((u.ravel(),v.ravel()))

def sample_depth(depth,valid,K_depth,uv,K_rgb):
    rays=np.column_stack(((uv[:,0]-K_rgb[0,2])/K_rgb[0,0],(uv[:,1]-K_rgb[1,2])/K_rgb[1,1],np.ones(len(uv))))
    q=rays@K_depth.T; x=q[:,0]/q[:,2]; y=q[:,1]/q[:,2]
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int); x1=x0+1; y1=y0+1
    support=(x0>=0)&(y0>=0)&(x1<depth.shape[1])&(y1<depth.shape[0])
    z=np.full(len(uv),np.nan)
    inds=np.flatnonzero(support)
    inds=inds[valid[y0[inds],x0[inds]]&valid[y0[inds],x1[inds]]&valid[y1[inds],x0[inds]]&valid[y1[inds],x1[inds]]]
    a=x[inds]-x0[inds]; b=y[inds]-y0[inds]
    z[inds]=depth[y0[inds],x0[inds]]*(1-a)*(1-b)+depth[y0[inds],x1[inds]]*a*(1-b)+depth[y1[inds],x0[inds]]*(1-a)*b+depth[y1[inds],x1[inds]]*a*b
    return z

def metrics(pred,truth,domain=None):
    domain0=np.isfinite(truth)&(truth>=.1)&(truth<=30)
    if domain is not None: domain0 &= domain
    valid=domain0&np.isfinite(pred)&(pred>=.1)&(pred<=30)
    n=int(domain0.sum()); nv=int(valid.sum())
    if not n: return {'pixels_domain':0,'pixels_valid':0,**{k:None for k in ['valid_coverage','invalid_rate','mae_m','rmse_m','absrel','delta1','delta2','delta3','missing_penalty_mae_m']}}
    e=np.abs(pred[valid]-truth[valid]); ratio=np.maximum(pred[valid]/truth[valid],truth[valid]/pred[valid])
    return {'pixels_domain':n,'pixels_valid':nv,'valid_coverage':nv/n,'invalid_rate':1-nv/n,'mae_m':float(e.mean()) if nv else None,'rmse_m':float(np.sqrt(np.mean(e**2))) if nv else None,'absrel':float(np.mean(e/truth[valid])) if nv else None,'delta1':float(np.mean(ratio<1.25)) if nv else 0.,'delta2':float(np.mean(ratio<1.25**2)) if nv else 0.,'delta3':float(np.mean(ratio<1.25**3)) if nv else 0.,'missing_penalty_mae_m':float((e.sum()+30*(n-nv))/n)}
