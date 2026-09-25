"""LPIPS on frozen five-view renders; preserve and verify existing PSNR/SSIM."""
from pathlib import Path
import os,sys,json,csv,hashlib,importlib.metadata
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/lpips_python'))
os.environ.setdefault('TORCH_HOME',str(ROOT/'runtime/lpips_torch'))
import numpy as np
from PIL import Image
import PIL,torch,torchvision,lpips,skimage
from skimage.metrics import structural_similarity
OUT=ROOT/'results/evaluation/appearance_five_views_20260925'
METHODS=['M1','M2','M3','M4'];VIEWS=[0,36,72,108,144]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(p):
 p=Path(p)
 return p if p.is_absolute() else ROOT/p

def main():
 OUT.mkdir(parents=True,exist_ok=True);torch.set_num_threads(4);torch.manual_seed(0)
 frozen=ROOT/'results/rgb_metrics_five_views.json';old=json.loads(frozen.read_text());means=json.loads((ROOT/'results/rgb_metrics_five_views_mean.json').read_text())['rows'];bymean={r['system']:r for r in means}
 model=lpips.LPIPS(net='alex',version='0.1',lpips=True,pnet_rand=False,pnet_tune=False,eval_mode=True,verbose=False).cpu().eval()
 assert not model.training
 records=[];zero=None
 with torch.inference_mode():
  for method in METHODS:
   selected=[r for r in old['rows'] if r['system']==method];assert [r['keyframe_index'] for r in selected]==VIEWS
   for r in selected:
    pred_path=local(r['pred_path']);gt_path=local(r['gt_path'])
    pred=Image.open(pred_path).convert('RGB');gt=Image.open(gt_path).convert('RGB');assert pred.size==(640,480)
    a=np.asarray(pred,dtype=np.float32)/255.;b=np.asarray(gt.resize(pred.size,Image.Resampling.LANCZOS),dtype=np.float32)/255.
    psnr=float(-10*np.log10(float(np.mean((a-b)**2))));ssim=float(structural_similarity(a,b,channel_axis=2,data_range=1.0))
    assert abs(psnr-r['psnr_db'])<1e-6 and abs(ssim-r['ssim'])<1e-7,(method,r['keyframe_index'])
    ta=torch.from_numpy(a.transpose(2,0,1).copy())[None];tb=torch.from_numpy(b.transpose(2,0,1).copy())[None]
    value=float(model(ta,tb,normalize=True).item());assert np.isfinite(value) and value>=-1e-6
    if zero is None:
     zero=float(model(tb,tb,normalize=True).item());assert abs(zero)<1e-7
    records.append({'system':method,'keyframe_index':r['keyframe_index'],'psnr_db':r['psnr_db'],'ssim':r['ssim'],'lpips_alex_v01':value,'pred_path':str(pred_path.relative_to(ROOT)),'gt_path':str(gt_path.relative_to(ROOT)),'pred_sha256':sha(pred_path),'gt_sha256':sha(gt_path)})
    print(method,r['keyframe_index'],'LPIPS',f'{value:.8f}',flush=True)
 rows=[]
 for method in METHODS:
  subset=[r for r in records if r['system']==method];rows.append({'system':method,'views':5,'psnr_db_mean':bymean[method]['psnr_db_mean'],'ssim_mean':bymean[method]['ssim_mean'],'lpips_alex_v01_mean':float(np.mean([r['lpips_alex_v01'] for r in subset]))})
 alex=Path(torch.hub.get_dir())/'checkpoints/alexnet-owt-7be5be79.pth';linear=Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
 weights=[{'role':'ImageNet-pretrained AlexNet backbone','source':'https://download.pytorch.org/models/alexnet-owt-7be5be79.pth','sha256':sha(alex)},{'role':'learned LPIPS v0.1 calibration weights','source':'https://github.com/richzhang/PerceptualSimilarity/blob/master/lpips/weights/v0.1/alex.pth','sha256':sha(linear)}]
 report={'status':'complete','methods':METHODS,'keyframe_indices':VIEWS,'resolution_wh':[640,480],'domain':'same five input views as frozen PSNR/SSIM; no held-out RGB generalization','preprocessing':'PIL RGB; GT Lanczos 1280x960 to 640x480; predictions unchanged; float32 RGB [0,1]; LPIPS normalize=True converts to [-1,1]; no crop, mask, pose/color/exposure fitting; black images and holes retained','lpips':{'implementation':'lpips==0.1.4','network':'alex','version':'0.1','learned_calibration':True,'pretrained_backbone':True,'random_backbone':False,'spatial':False,'input_normalize':True,'eval_mode':True,'device':'cpu','dtype':'float32','lower_is_better':True,'weights':weights},'aggregation':'arithmetic mean of five per-view scores for each metric','versions':{'torch':torch.__version__,'torchvision':torchvision.__version__,'numpy':np.__version__,'Pillow':PIL.__version__,'scikit-image':skimage.__version__},'checks':{'frozen_psnr_ssim_recomputed':'pass','identical_image_lpips':zero},'source_rgb_metrics_sha256':sha(frozen),'evaluator_sha256':sha(Path(__file__)),'rows':rows,'per_view':records}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 with (OUT/'per_view.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 with (OUT/'means.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
