import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,numpy as np,hashlib,datetime
from pathlib import Path
R=Path(__file__).parent;P=json.loads((R.parent.parent/'inputs/M2/packet.json').read_text());L=json.loads((R/'layout.json').read_text());old=json.loads((R/'versions/v1/layout.json').read_text());X=np.array(L['model_from_input']);F=P['frames'];out={}
# Review existing full-input anomalies from actual stored arrays and native packet metadata.
n=np.load(R/'checks/input_v1/depth.npz');rows=[]
for i in [19,20,21,22,23,24,165,166,167,168,169,170,174,175,176]:
 with np.load(F[i]['geometry']) as d:
  T=X@np.array(F[i]['camera_to_world']);prev=X@np.array(F[i-1]['camera_to_world']);pred=n['prediction_z_m'][i];ref=n['reference_z_m'][i];domain=np.isfinite(ref)&(ref>=.1)&(ref<=30);valid=domain&np.isfinite(pred)&(pred>=.1)&(pred<=30)
  rows.append({'frame':i,'selected_window':F[i]['selected_window'],'translation_step_m':float(np.linalg.norm(T[:3,3]-prev[:3,3])),'rotation_step_deg':float(np.degrees(np.arccos(np.clip((np.trace(T[:3,:3].T@prev[:3,:3])-1)/2,-1,1)))),'DA3_quantiles_m':np.nanpercentile(d['depth_z_m'],[10,50,90]).tolist(),'saved_v1_model_quantiles_m':np.nanpercentile(pred,[10,50,90]).tolist(),'signed_residual_median_m':float(np.median((pred-ref)[valid])),'original_domain_pixels':int(domain.sum())})
out['outlier_records']=rows;out['outlier_interpretation']='The selected DA3 window changes produce discontinuous predicted depth (median8.09 to19.67m at20->21,7.94 to18.74m at166->167) despite sub-centimeter translation and <0.07deg rotation steps and similar source RGB.175 has implausibly short0.37m median. This supports prediction-window inconsistency as a major contributor, not proof that all native poses/geometry are correct. No depth rescale, pose edit or mask trim.'
# Regional signed error before/after on original unchanged check domains.
regions=[]
for f,v in json.loads((R/'analysis/object_depth_regions.json').read_text()).items():regions.append({'name':f,'frame':v['sample_index'],'rgb_box':v['rgb_box']})
for f,v in json.loads((R/'analysis/plane_observations.json').read_text()).items():
 uv=np.array(v['rgb_polygon']);regions.append({'name':f,'frame':v['sample_index'],'rgb_box':[*uv.min(0).tolist(),*uv.max(0).tolist()]})
regions += [{'name':'desk_intrusion','frame':100,'rgb_box':[920,580,1080,780]},{'name':'open_passage','frame':74,'rgb_box':[1160,315,1280,540]},{'name':'open_passage','frame':82,'rgb_box':[918,458,985,565]},{'name':'near_seats','frame':155,'rgb_box':[780,730,1080,950]},{'name':'mirror_cluster','frame':61,'rgb_box':[568,270,1120,560]},{'name':'mirror_cluster','frame':74,'rgb_box':[703,253,1120,515]}]
for region in regions:
 for ver in [1,2,3,4,5]:
  f=R/f"checks/v{ver}/{region['frame']:04d}_depth.npz"
  if not f.exists():continue
  d=np.load(f);x0,y0,x1,y1=np.array(region['rgb_box'])//2;s=np.s_[y0:y1,x0:x1];pred=d['model_z_m'][s];ref=d['input_da3_z_m'][s];domain=d['input_valid_domain'][s];valid=domain&np.isfinite(pred)&(pred>=.1)&(pred<=30);e=(pred-ref)[valid];region[f'v{ver}']={'domain_pixels':int(domain.sum()),'valid_pixels':int(valid.sum()),'signed_median_m':float(np.median(e)) if e.size else None,'abs_median_m':float(np.median(np.abs(e))) if e.size else None,'miss_pixels':int((domain&~valid).sum())}
out['regions']=regions;out['meaning']='Signed = model optical Z minus own DA3 prediction; never ground truth. Rectangular diagnostics do not alter check validity masks.'
# Exact parameter changes retained; builder-form adjustments listed separately.
diffs=[]
def diff(a,b,path):
 if isinstance(a,dict) and isinstance(b,dict):
  for k in a.keys()|b.keys():diff(a.get(k),b.get(k),path+'/'+str(k))
 elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
  for i,(aa,bb) in enumerate(zip(a,b)):diff(aa,bb,path+'/'+str(i))
 elif a!=b:diffs.append({'parameter':path,'before':a,'after':b})
diff(old,L,'layout');out['exact_layout_changes']=diffs
out['builder_adjustments']=[
 {'issue':'M2-I02','parameter':'all rod rotation construction','before':'quaternion assigned before mode switch; discarded','after':'QUATERNION mode first; assigned endpoint quaternion; all world endpoints audited','frames':[33,74,82,100,108,118,129,155],'regions':['ceiling light boxes in revision_measurements','planters','near/far tables'],'provenance':'technical correction; requested endpoints unchanged except explicitly measured lamp centers'},
 {'issue':'M2-I03','parameter':'custom closed mesh face winding and chair bevel','before':'inward chair/desk volume; chair bevel0.04m','after':'bmesh recalc outward normals, bevel removed from backs; continuous prism boundary','frames':[33,61,74,129,155],'regions':['seat_far_left_33','seat_far_left_129','seat_near_mid_61','reception_33','reception_129'],'provenance':'topology correction; depth signs are contextual, winding itself not fitted to depth'},
 {'issue':'M2-I04','parameter':'wall seams and service passage','before':'22mm vertical/25mm horizontal unbacked gaps; rounded panel omissions; flat0.85m leaf at y=-0.3','after':'0.10m structural backing at wall center+0.10m, split exactly at apertures; service_door_1 open1.05m aperture2.24m high with1.5m bounded returns; split proxies','frames':[61,74,82],'regions':['open_passage','mirror_wall_61','wall_recess_82'],'provenance':'visible open silhouette observed; thickness and return depth inferred'},
 {'issue':'M2-I05','parameter':'seat footprints and feet','before':'independent round bases radii0.40/0.43m overlap up to0.210m; foot XY offsets0.22m','after':'centers/radii/heights/yaws retained; circular footprint clipped by every adjacent center bisector with0.003m inset per seat; back clipped identically; foot offsets0.15m','frames':[33,61,129,155],'regions':['seat_far_left_33','seat_far_left_129','seat_near_mid_61','near_seats'],'provenance':'RGB shows joined modular arrangement; exact shared hidden boundaries inferred'},
 {'issue':'M2-I08','parameter':'cylinder cap shading','before':'smooth caps','after':'flat caps; smooth quad sides','frames':[61,74,129],'regions':['mirror_cluster','table_far_129'],'provenance':'observed planar mirror/table faces; no position change'},
 {'issue':'M2-I08','parameter':'door frame dimensions','before':'jamb0.09x0.065x2.7m and rail0.09x0.9x0.12m','after':'jamb0.09x0.15x2.7m and rail0.09x0.9x0.20m','frames':[100,108,118],'regions':['entrance door outlines RGB100x820:1020y275:550;108x700:875y318:565;118x640:825y275:580'],'provenance':'RGB thickness approximation; closed glazing state retained'},
 {'issue':'M2-I08','parameter':'procedural vegetation','before':'35gold/46green stems,9/5 leaf stations','after':'65stems,12/7 stations; same deterministic seed, origins/radii/heights unchanged','frames':[33,82,91,108,129],'regions':['planter_far_left_33','planter_far_left_129','planter_near_left_91'],'provenance':'fullness appearance inferred; stochastic changed tips not individually measured'},
 {'issue':'M2-I08','parameter':'material and illumination','before':'uniform noisy floor, pale walls,850W daylight and180W fills','after':'object-coordinate14/m brass dash pattern; floor bump removed; stone/wood/ceiling bump distance0.002m; darker reflectance;420W daylight90W fills','frames':[33,61,74,91,100,108,129,155],'regions':['all corresponding RGB; floor_33/floor_61/floor_100'],'provenance':'RGB appearance inference; shader is not a depth adjustment'}]
(R/'analysis/revision_evidence.json').write_text(json.dumps(out,indent=2)+'\n');print('saved',len(regions),'regions',len(diffs),'parameter changes',len(rows),'outlier arrays inspected')
