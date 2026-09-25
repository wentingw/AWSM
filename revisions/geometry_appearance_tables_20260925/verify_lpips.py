"""Independently check stored score means and one normalized LPIPS pair."""
from pathlib import Path
import sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[2];REV=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'runtime/lpips_python'));os.environ['TORCH_HOME']=str(ROOT/'runtime/lpips_torch')
import numpy as np,torch,lpips
from PIL import Image
report=json.loads((ROOT/'results/evaluation/appearance_five_views_20260925/report.json').read_text());old={r['system']:r for r in json.loads((ROOT/'results/rgb_metrics_five_views_mean.json').read_text())['rows']}
for row in report['rows']:
 views=[r for r in report['per_view'] if r['system']==row['system']];assert [v['keyframe_index'] for v in views]==[0,36,72,108,144]
 assert row['psnr_db_mean']==old[row['system']]['psnr_db_mean'] and row['ssim_mean']==old[row['system']]['ssim_mean']
 assert abs(row['lpips_alex_v01_mean']-sum(r['lpips_alex_v01'] for r in views)/5)<1e-12
 for view in views:
  for key in ['pred','gt']:assert hashlib.sha256((ROOT/view[key+'_path']).read_bytes()).hexdigest()==view[key+'_sha256']
# Use explicit [-1,1] tensors instead of the evaluator's normalize=True interface.
torch.set_num_threads(4);model=lpips.LPIPS(net='alex',version='0.1',eval_mode=True,verbose=False).cpu().eval()
r=next(r for r in report['per_view'] if r['system']=='M4' and r['keyframe_index']==0)
def tensor(path,resize=False):
 im=Image.open(ROOT/path).convert('RGB')
 if resize:im=im.resize((640,480),Image.Resampling.LANCZOS)
 return 2*torch.tensor(np.array(im),dtype=torch.float32).permute(2,0,1).unsqueeze(0)/255.-1
x=tensor(r['pred_path']);y=tensor(r['gt_path'],True)
with torch.inference_mode():
 value,layers=model(x,y,normalize=False,retPerLayer=True);reverse=model(y,x,normalize=False);identical=model(y,y,normalize=False)
assert abs(value.item()-r['lpips_alex_v01'])<1e-6
assert abs(reverse.item()-value.item())<1e-7 and abs(identical.item())<1e-7
assert abs(sum(float(l.item()) for l in layers)-value.item())<1e-7
out={'status':'pass','original_psnr_ssim_unchanged':True,'all_input_sha256':'pass','all_four_means':'pass','independent_explicit_normalization_check':{'method':'M4','view':0,'lpips':float(value.item()),'layer_sum':sum(float(l.item()) for l in layers),'identical_pair':float(identical.item()),'symmetry':'pass'}}
(REV/'lpips_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
