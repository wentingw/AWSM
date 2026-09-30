import json,numpy as np,hashlib,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[2];N=json.loads((R/'author_repair_notes.json').read_text());C=json.loads((R/'cameras.json').read_text());objects={v:{o['id']:o for o in json.loads((R/f'versions/v{v}/objects.json').read_text())['objects']} for v in [1,2]};rows=[]
cache={(v,i):np.load(R/f'checks/v{v}/{i:04d}_depth.npz') for v in [1,2] for i in [33,61,74,82,91,100,108,118,129,155]}
for change in N['changes']:
 name=change['parameter'];oid=name.split('.')[0]
 if oid not in objects[2]:continue
 out=[]
 for i in [33,61,74,82,91,100,108,118,129,155]:
  f=C['frames'][i];K=np.array(f['intrinsics'],float);K[:2]*=.5;W=np.linalg.inv(np.array(f['camera_to_world']));uvs=[]
  for ver in [1,2]:
   lo,hi=objects[ver][oid]['bounds_model_m'];p=np.array([list(q)+[1] for q in itertools.product(*zip(lo,hi))])@W.T
   if np.any(p[:,2]<=.1):continue
   q=p[:,:3]@K.T;uvs.extend((q[:,:2]/q[:,2,None]).tolist())
  if not uvs:continue
  q=np.array(uvs);lo=np.maximum(np.floor(q.min(0)).astype(int),[0,0]);hi=np.minimum(np.ceil(q.max(0)).astype(int),[640,480]);x0,y0=lo;x1,y1=hi
  if x1-x0<5 or y1-y0<5:continue
  obs=dict(sample_index=i,pixel_region_640x480=[int(x0),int(y0),int(x1),int(y1)],region_provenance='Projected union of before/after semantic bounds, may include foreground occluders and background; NOT an input mask change')
  for ver in [1,2]:
   d=cache[ver,i];z=d['model_z_m'][y0:y1,x0:x1];r=d['input_da3_z_m'][y0:y1,x0:x1];valid=d['input_valid_domain'][y0:y1,x0:x1]&np.isfinite(z)&(z>=.1)&(z<=30);diff=(z-r)[valid]
   obs[f'v{ver}']=dict(valid_pixels=int(valid.sum()),median_signed_m=float(np.median(diff)),p10_p90=np.quantile(diff,[.1,.9]).tolist())
  out.append(obs)
 change['per_object_projected_region_evidence']=out
N['changes'].append({'version':2,'parameter':'botanical.procedural_realisation_after_divider_calls','before':'single trough bush; later plants generated from subsequent shared random state','after':'four trough bushes; later plant branch/leaf realization regenerated from advanced deterministic random state','rationale':'Incidental stochastic detail change, inferred. Fixed pot/profile/placement parameters for all non-divider plants retained. Semantic bounds may change with branch tips. No data-derived precision claimed.','evidence': [r for r in json.loads((R/'analysis/repair/region_comparison_v2.json').read_text()) if r['label'] in ['shrubs','plants','divider']],'provenance':'inferred hidden/botanical detail'})
N['changes'].append({'version':2,'parameter':'pendant_6_and_7.support_cable_light_transform','before':'cable from old bottom+.20 to ceiling5.23; local area light old bottom-.025','after':'same local offsets at new measured pendant centre and bottom','rationale':'Suspension and light follow moved pendant object. Relative support dimensions/power remain inferred.','evidence_reference':'pendant_6/7 xy_bottom_z_radius records'})
(R/'author_repair_notes.json').write_text(json.dumps(N,indent=2)+'\n')
# Both initial passes contain own DA3 only; examine spatial subsets plus temporal depth conflict.
checks=[]
for name in ['input_v1','input_v2']:
 d=np.load(R/f'checks/{name}/depth.npz');report=json.loads((R/f'checks/{name}/report.json').read_text());per=[]
 for i in [33,61,74,82,91,100,108,118,129,155,160,167,170,179]:
  pred=d['prediction_z_m'][i];ref=d['reference_z_m'][i];m=np.isfinite(pred)&np.isfinite(ref);per.append({'sample_index':i,'median_model_z':float(np.nanmedian(pred)),'median_input_da3_z':float(np.nanmedian(ref)),'median_signed_z':float(np.median((pred-ref)[m]))})
 checks.append({'pass':name,'frames':len(d['timestamps_ns']),'model_sha256':report['model_sha256'],'selected_temporal_observations':per})
(R/'analysis/repair/full_input_observations_v2.json').write_text(json.dumps(checks,indent=2)+'\n')
print('Updated object-local before/after residual evidence, botanical inference, and temporal input-pass observations.')
