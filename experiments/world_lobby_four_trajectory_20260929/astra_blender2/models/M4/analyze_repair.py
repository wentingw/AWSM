import json,numpy as np,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;keys=[33,61,74,82,91,100,108,118,129,155]
old=json.load(open(R/'analysis/spatial_residuals_v1.json'))['regions'];rows=[]
for r in old:
 i=r['sample_index'];x0,y0,x1,y1=r['pixel_region_640x480'];n=np.load(R/f'checks/v2/{i:04d}_errors.npz');a=n['signed_z_residual_m'][y0:y1,x0:x1]
 rows.append(dict(sample_index=i,region=r['region'],pixel_region_640x480=r['pixel_region_640x480'],before=dict(median_signed_m=r['median_signed_model_minus_DA3_m'],mae_m=r['mae_m']),after=dict(median_signed_m=float(np.nanmedian(a)),mae_m=float(np.nanmean(abs(a)))),interpretation='Same mixed-surface diagnostic rectangle, not a score mask'))
json.dump(dict(role='author spatial evidence',convention='model optical Z minus own DA3 prediction; no truth',regions=rows),open(R/'analysis/spatial_residuals_v2.json','w'),indent=2)
for r in rows:
 if r['region'] in ['missing_pendant','missing_west_lights','west_wall','troughs','shrub','planters','seats_A','seats_B','far_wall']:print(r['sample_index'],r['region'],'signed',round(r['before']['median_signed_m'],3),'->',round(r['after']['median_signed_m'],3),'MAE',round(r['before']['mae_m'],3),'->',round(r['after']['mae_m'],3))
for version in [1,2]:
 r=json.load(open(R/f'checks/v{version}/paired_report.json'));print('paired',version,r['aggregate_input_consistency'])
 r=json.load(open(R/f'checks/input_v{version}/report.json'));print('input',version,r['aggregate'])
# Dense component bounds ledger, exact before/after for every changed/generated scene component.
before={x['name']:x for x in json.load(open(R/'independent_review/scene_inspection.json'))['meshes']};after={x['name']:x for x in json.load(open(R/'checks/artifact_inspection.json'))['meshes']};changes=[]
for n in sorted(set(before)|set(after)):
 a=before.get(n);b=after.get(n)
 if a is None or b is None or not np.allclose(a['bounds'],b['bounds'],atol=1e-6,rtol=0) or a['triangles']!=b['triangles']:
  changes.append(dict(component_name=n,semantic_object_id=n.split('__')[0],before=None if a is None else dict(bounds=a['bounds'],triangles=a['triangles']),after=None if b is None else dict(bounds=b['bounds'],triangles=b['triangles'])))
json.dump(dict(scope='Exact inspected mesh-bound/topology changes; companion rationale and pixel residuals in repair_changes_v2.json',changes=changes),open(R/'analysis/component_changes_v2.json','w'),indent=2)
# Whole180 prediction conflict diagnostics: preserve all samples/domain, report extremes.
rows=[]
for name in ['input_v1','input_v2']:
 n=np.load(R/'checks'/name/'depth.npz');report=json.load(open(R/'checks'/name/'report.json'))
 rows.append(dict(pass_directory=name,model_sha256=report['model_sha256'],frames=180,aggregate=report['aggregate'],conflicting_frames=[dict(sample_index=i,reference_median=float(np.nanmedian(n['reference_z_m'][i])),model_median=float(np.nanmedian(n['prediction_z_m'][i])),stats=report['per_frame'][i]) for i in [15,16,21,22,33,129,155,173,174,177,178,179]]))
json.dump(dict(reference='Own predicted DA3 only; all prescribed domains retained',passes=rows),open(R/'analysis/full_input_diagnostics_v2.json','w'),indent=2)
