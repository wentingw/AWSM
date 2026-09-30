import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json,sys,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];v=int(sys.argv[1]);base=json.loads((R/'analysis/paired_region_residuals_v1.json').read_text());regions=[(r['sample_index'],r['label'],r['pixel_region_640x480']) for r in base]
regions += [(118,'column core',[30,80,65,340]),(33,'column core',[125,60,145,250]),(108,'column core',[146,90,166,235]),(129,'column core',[182,80,204,300]),(61,'wall pendant',[238,24,340,68]),(74,'wall pendant',[390,5,485,38]),(129,'centre pendant',[255,8,425,68]),(82,'divider box',[282,353,370,425]),(91,'divider box',[175,218,265,264])]
rows=[]
for i,label,bb in regions:
 x0,y0,x1,y1=bb;row=dict(sample_index=i,label=label,pixel_region_640x480=bb,sign='model minus own DA3',region_type='fixed rectangular observation, not object mask')
 for ver in [1,v]:
  n=np.load(R/f'checks/v{ver}/{i:04d}_depth.npz');z=n['model_z_m'][y0:y1,x0:x1];r=n['input_da3_z_m'][y0:y1,x0:x1];valid=n['input_valid_domain'][y0:y1,x0:x1]&np.isfinite(z)&(z>=.1)&(z<=30);diff=(z-r)[valid]
  row[f'v{ver}']=dict(valid_pixels=int(valid.sum()),median_signed_m=float(np.median(diff)),mae_m=float(np.mean(abs(diff))),p10_p90=np.quantile(diff,[.1,.9]).tolist())
 rows.append(row)
(R/f'analysis/repair/region_comparison_v{v}.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps([r for r in rows if r['label'] in ['column core','wall pendant','centre pendant','divider box','desk']],indent=2))
