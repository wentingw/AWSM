import json,ast,shutil,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from session_log import record
R=Path(__file__).resolve().parents[2];L=json.loads((R/'layout.json').read_text());F=json.loads((R/'analysis/repair/fits.json').read_text());old=json.loads(json.dumps(L));s=(R/'build_scene.py').read_text()
# Preserve all additional v1 metadata before replacing current files.
for f in ['colliders.json','input_access_log.json','iteration_log.json']:
 target=R/'versions/v1'/('pre_repair_'+f);shutil.copyfile(R/f,target)
changes=[]
regions=json.loads((R/'analysis/paired_region_residuals_v1.json').read_text())
def evidence(labels):return [r for r in regions if r['label'] in labels]
def change(name,before,after,why,labels,provenance='inferred refinement constrained by RGB and physical clearance'):
 changes.append(dict(parameter=name,before=before,after=after,rationale=why,provenance=provenance,evidence=evidence(labels)))
L['version']=2
for group in L['seating']:
 q=F['seats'][group['id']]['centres'];n=len(group['chairs'])
 for j,a in enumerate(group['chairs']):
  before=a.copy();a[:2]=q[j];change(group['id']+'_chair'+str(j)+'.position_angle',before,a.copy(),'RGB ray-plane anchor and minimum displacement separation; retain orientation. .95m seat centres and >=1.07m table-centre distance.', ['chairs','chair'])
 for j,a in enumerate(group['ottomans']):
  before=a.copy();a[:]=q[n+j];change(group['id']+'_ottoman'+str(j)+'.position',before,a.copy(),'As above. No DA3 score minimisation.', ['chairs','chair'])
L['column']['location'][:2]=F['column']['after'][:2];L['column']['radius']=F['column']['after'][2]
change('column',old['column'],L['column'],'Joint fit to ten silhouette tangent planes from RGB33/100/108/118/129; RMS .042m; see fits.json.', ['column','glazing','glass'],'measured silhouette fit; upright axis inferred')
L['desk'].update(top_z=.89,bottom_z=.15,plinth_bottom_z=.018,plinth_top_z=.20)
L['desk']['dimensions']=[1.15,3.2,.872]
change('desk.top_z_and_support',{'top':1.15,'shell_bottom':.15,'support':None},{'top':.89,'shell_bottom':.15,'plinth':[.018,.20]},'Top accepted triangulation .861/.907m (33/129/155); concealed plinth and back closure inferred.', ['desk'],'measured top; inferred hidden support')
pend=ast.literal_eval(s.split('pendants=')[1].split('\nfor j,')[0]);L['pendants']=[list(p) for p in pend]
P=json.loads((R.parents[1]/'inputs/M3/packet.json').read_text());K=np.array(P['intrinsics'],float);K[:2]*=.5;X=np.array(L['model_from_input'])
for idx,label,frame,target_width in [(7,'pendant_wall',61,112),(6,'pendant_centre',129,183)]:
 point=F[label]['point'];z=point[2]-.015
 T=X@np.array(P['frames'][frame]['camera_to_world']);W=np.linalg.inv(T)
 def width(r):
  a=np.linspace(0,2*np.pi,128);q=np.c_[point[0]+r[0]*np.cos(a),point[1]+r[0]*np.sin(a),np.full(128,z+.23),np.ones(128)]@W.T;uv=q[:,:3]@K.T;u=uv[:,0]/uv[:,2];return u.max()-u.min()
 rr=float(least_squares(lambda r:[width(r)-target_width],[.7],bounds=(.25,1.3)).x[0])
 before=L['pendants'][idx].copy();L['pendants'][idx]=[point[0],point[1],z,rr]
 change(f'pendant_{idx}.xy_bottom_z_radius',before,L['pendants'][idx],f'Individual diffuser identity {label}; triangulated RGB observations in fits.json; source frame{frame} rim width {target_width}px. Radius uses horizontal rim profile +.23m, inferred shape.', ['pendants','lights','ceiling'],'multi-view triangulated position; one-view rim size constrained by identity')
L['provenance']='Revision2: technical repairs and selected measured refinements; native cameras and rigid transform unchanged. See author_repair_notes.json and analysis/repair/fits.json.'
# Miscellaneous changes, all recorded even if dimension parameters reside in the builder.
change('entry_door.upright_width_rail_height',[.065,.14],[.14,.22],'Source100/108/118 brass door members visibly broad; centres/extents retained. Inferred widths.', ['glazing','glass'])
change('divider.foliage_distribution',{'root_cluster':'single centre','height':.95},{'root_clusters':4,'along_y_fraction':[-.35,-.1167,.1167,.35],'height':.83},'Keep uncertain trough dimensions/corners; distribute inferred branches along visible trough length in RGB33/82/91/108/129.', ['shrubs','plants','divider'])
change('chair.back_topology','mixed winding and degenerate bevel','closed outward winding, bounded bevel, flat cap normals','M3-I01; preserve dimensions. Technical change does not purport to infer new geometry from DA3.', ['chairs','chair'],'topological repair')
change('cylinder.cap_normals','smooth','flat','M3-I09 flat mirrors and table surfaces visible in61/74/129; no size change.', ['mirror wall','chairs'],'normal repair')
change('crest.shield_normal_material',{'normal':'+X','material':'limestone'},{'normal':'-X','material':'white_linen'},'RGB33/129/155 shield is white facing room; preserve vertices.', ['far wall','back wall'])
change('appearance',{'floor_bump_strength':.15,'floor_bump_distance':.025,'oak':[.48,.445,.36],'concrete':[.30,.31,.29]}, {'floor_bump_strength':0,'oak':[.30,.28,.235],'concrete':[.16,.17,.16]},'Source61/74/100/129 surfaces flatter/darker; appearance inference.', ['floor','mirror wall','glass'])
(R/'layout.json').write_text(json.dumps(L,indent=2)+'\n')
M=json.loads((R/'modelling_manifest.json').read_text());M.update(revisions=2,phase='revision_author_repairs',status='ready_for_independent_review',quality_status='LIMITED; repaired candidate checks pending',scope='M3 revision author; independent final review pending');(R/'modelling_manifest.json').write_text(json.dumps(M,indent=2)+'\n')
notes={'method_id':'M3','author_role':'revision author, not independent reviewer','version':2,'changes':changes,'measurement_fits':'analysis/repair/fits.json','residual_convention':'model minus own predicted DA3, metres; rectangles may mix surfaces; not GT','uncertainties':['Single upright column fit leaves .042m tangent RMS due native pose/manual silhouette conflict.','Some pendant identities remain inferred; two selected identities measured.','Seat ray-plane elevation .565m inferred; separation correction does not establish exact furniture placement.','Trough corners inconsistent across views; keep dimensions and position unchanged.','Room and late DA3 conflicts retained; no scale/camera/mask changes.'],'provenance_reconciliation':{'issue':'M3-I05','source':'checks/input_v1/coordinator_invocation.json','status':'originating coordinator attribution supplied locally after review; author can verify record/hashes but did not witness creating command','original_author_uncertainty_preserved':True},'review_status':'author repair evidence only; requires independent review'}
(R/'author_repair_notes.json').write_text(json.dumps(notes,indent=2)+'\n')
record('prepare_v2',[R/'layout.json',R/'build_scene.py',R/'analysis/repair/fits.json',R/'analysis/paired_region_residuals_v1.json',R/'checks/input_v1/coordinator_invocation.json'],'Ran prepare_v2.py; preserved pre-repair metadata; incremented version2; recorded every parameter change. fit_repairs.py had two rejected pendant82 identity guesses before final accepted61/74 wall identity; intermediate calculation error ModuleNotFoundError fixed by explicit module path, no scene built.')
