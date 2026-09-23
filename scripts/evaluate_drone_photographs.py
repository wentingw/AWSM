"""Post-execution evaluator only. GT cameras never reach the planner."""
import sys,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageOps,ImageDraw,ImageFont
from skimage.metrics import structural_similarity
ROOT=Path(__file__).resolve().parents[1];batch=ROOT/'experiments/tasks/drone_M3/photographic_20';out=ROOT/'results/evaluation/tasks/drone_photographic_20';out.mkdir(parents=True,exist_ok=True)
truth={x['query_id']:x for x in json.loads((ROOT/'results/evaluation/tasks/photographic_reference_truth_private.json').read_text())};T=np.asarray(json.loads((ROOT/'results/M3/model_registration.json').read_text())['transform']);rows=[]
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for ep in sorted(batch.glob('episode_*')):
 d=json.loads((ep/'summary.json').read_text());q=d['request']['query_id'];r={'query_id':q,'flight_status':d['status'],'strict_rephotography_success':False,'relaxed_rephotography_success':False}
 if 'final_camera_to_model' in d:
  C=T@np.asarray(d['final_camera_to_model']);t=np.asarray(truth[q]['camera_tum']);R=Rotation.from_quat(t[4:8]).as_matrix();te=float(np.linalg.norm(C[:3,3]-t[1:4]));re=float(np.degrees(Rotation.from_matrix(C[:3,:3].T@R).magnitude()));r.update(translation_error_m=te,rotation_error_deg=re,selected_view_id=d['selected_view_id'],candidate_arrival_error_m=d['dynamics']['goal_error_m'],simulated_seconds=d['dynamics']['simulated_seconds'],contact_steps=d['dynamics']['collision_steps'],strict_rephotography_success=d['status']=='success' and te<=.1 and re<=5,relaxed_rephotography_success=d['status']=='success' and te<=.25 and re<=10)
  target=np.asarray(Image.open(d['request']['reference_rgb']).convert('RGB').resize((640,480),Image.Resampling.LANCZOS));p=ep/'final_rgb.png'
  if p.exists():
   pred=np.asarray(Image.open(p).convert('RGB'));mse=float(np.mean(((pred.astype(float)-target)/255)**2));r['psnr_db']=float(-10*np.log10(max(mse,1e-12)));r['ssim']=float(structural_similarity(target,pred,data_range=255,channel_axis=2))
 rows.append(r)
counts={'episodes':len(rows),'collision_free_candidate_arrivals':sum(r['flight_status']=='success' for r in rows),'collisions':sum(r['flight_status']=='collision' for r in rows),'planning_failed':sum(r['flight_status']=='planning_failed' for r in rows),'strict_rephotography_successes':sum(r['strict_rephotography_success'] for r in rows),'relaxed_rephotography_successes':sum(r['relaxed_rephotography_success'] for r in rows)}
result={'condition':'20 original mapping photographs; target poses withheld during execution; no held-out-image generalization','registration':'fixed global M3 SE3; no per-task fitting','success_definition':{'strict':'collision-free execution, position <=0.10m AND rotation <=5deg','relaxed':'collision-free execution, position <=0.25m AND rotation <=10deg'},'counts':counts,'means':{k:float(np.mean([r[k] for r in rows if k in r])) for k in ['translation_error_m','rotation_error_deg','psnr_db','ssim'] if any(k in r for r in rows)},'episodes':rows,'limitations':['coarse29candidate DINO retrieval, top5 collision planning','no image-based local refinement','simulator state oracle','ideal stabilized gimbal','model-world collision proxies; not GT dynamics transfer']};(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
if all((batch/f"episode_{r['query_id']:02d}/final_rgb.png").exists() for r in rows):
 sheet=Image.new('RGB',(1060,90+len(rows)*258),'#f5f4ef');draw=ImageDraw.Draw(sheet);draw.text((10,12),'REFERENCE PHOTO',font=font,fill='#172524');draw.text((340,12),'ACTUAL FINAL CAMERA IN M3',font=font,fill='#172524');draw.text((680,12),'POST-EXECUTION GT EVALUATION',font=font,fill='#172524')
 for i,r in enumerate(rows):
  ep=batch/f"episode_{r['query_id']:02d}";d=json.loads((ep/'summary.json').read_text());y=55+i*258
  for x,p in [(10,Path(d['request']['reference_rgb'])),(340,ep/'final_rgb.png')]:sheet.paste(Image.open(p).convert('RGB').resize((320,240),Image.Resampling.LANCZOS),(x,y))
  draw.multiline_text((680,y+20),f"Query {r['query_id']:02d} | {r['flight_status']}\nPosition: {r['translation_error_m']:.2f} m\nRotation: {r['rotation_error_deg']:.1f} deg\nSSIM: {r['ssim']:.3f}\nStrict photo goal: {'PASS' if r['strict_rephotography_success'] else 'FAIL'}",font=font,fill='#172524',spacing=8)
 sheet.save(ROOT/'figures/drone_all_queries.jpg',quality=92)
 # Predeclared display IDs: first query plus q3/q13; avoid selecting on success.
 small=Image.new('RGB',(1060,55+3*258),'#f5f4ef');small.paste(sheet.crop((0,0,1060,55)),(0,0))
 for j,i in enumerate([0,3,13]):small.paste(sheet.crop((0,55+i*258,1060,55+(i+1)*258)),(0,55+j*258))
 small.save(ROOT/'figures/drone_three_queries.jpg',quality=94)
print(json.dumps({'counts':counts,'means':result['means']},indent=2))
