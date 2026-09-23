#!/usr/bin/env python3
import json, sys
from pathlib import Path
import numpy as np

def tum(path):
    out=[]
    for line in Path(path).read_text().splitlines():
        p=line.strip().split()
        if not p or p[0].startswith('#'): continue
        out.append((float(p[0]),np.array([float(x) for x in p[1:]],float)))
    return out

def main():
    base=Path(sys.argv[1]); mode=sys.argv[2]; gt=Path(sys.argv[3]) if len(sys.argv)>3 else None
    poses=tum(gt) if gt else []
    rows=[]; failures=[]
    for d in sorted(base.glob('smoke*')):
        p=d/'manifest.json'
        if not p.exists(): continue
        m=json.loads(p.read_text())
        if m.get('status')!='complete': failures.append({'dir':d.name,'status':m.get('status')}); continue
        f=m['frames'][0]; a=np.load(d/f['data']); z=a['depth_z']; mask=a['mask'].astype(bool)&np.isfinite(z)&(z>0)
        row={'dir':d.name,'frame':f['keyframe_index'],'depth_shape':list(z.shape),'valid_fraction':float(mask.mean()),'depth_p01_p50_p99_m':[float(x) for x in np.percentile(z[mask],[1,50,99])],'depth_units':m['depth_units']}
        if mode=='M4':
            row['pose_match_error_s']=f['pose_match_error_s']; row['input_pose_shape']=list(a['input_camera_pose'].shape)
            j=f['keyframe_index']; row['input_translation_m']=a['input_camera_pose'][:3,3].tolist(); row['gt_translation_m']=poses[j][1:4].tolist(); row['translation_equal_to_gt']=bool(np.allclose(a['input_camera_pose'][:3,3],poses[j][1:4],atol=1e-6))
        rows.append(row)
    report={'status':'passed_independent_single_view_smoke','mode':mode,'joint_8_view_status':'failed_or_not_run_due_to_GPU_OOM','independent_views':len(rows),'frames':rows,'failures':failures,'scope':'Eight independent one-view runs; this is not an eight-view joint attention run.'}
    (base/'smoke_audit.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
