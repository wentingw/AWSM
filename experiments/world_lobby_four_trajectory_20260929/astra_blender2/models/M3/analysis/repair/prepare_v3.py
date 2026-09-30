import json,shutil,hashlib,datetime
from pathlib import Path
from session_log import record
R=Path(__file__).resolve().parents[2];B=R.parents[1];M=json.loads((R/'modelling_manifest.json').read_text());M['input_bvh_pass_count']=2;M['checking_render_count']=20;(R/'modelling_manifest.json').write_text(json.dumps(M,indent=2)+'\n')
for f in ['colliders.json','input_access_log.json','author_repair_notes.json','iteration_log.json']:
 shutil.copyfile(R/f,R/'versions/v2'/f)
shutil.copyfile(R/'modelling_manifest.json',R/'versions/v2/modelling_manifest_after_checks.json')
shutil.copytree(R/'analysis',R/'versions/v2/analysis',dirs_exist_ok=True)
L=json.loads((R/'layout.json').read_text());L['version']=3
s=(R/'build_scene.py').read_text().replace('model v2 repaired candidate.','model v3 repaired candidate.')
s=s.replace(";b=o.modifiers.new('soft_back_edges','BEVEL');b.width=.04;b.segments=3",'')
# Disable smoothing on horizontal/end faces while keeping the cylindrical surfaces smooth.
s=s.replace("for p in o.data.polygons:p.use_smooth=True\n\ndef table", "for p in o.data.polygons:p.use_smooth=(abs(p.normal.z)<.5 and len(p.vertices)==4)\n\ndef table")
(R/'build_scene.py').write_text(s);(R/'layout.json').write_text(json.dumps(L,indent=2)+'\n');M['revisions']=3;M['phase']='final_candidate_checking';(R/'modelling_manifest.json').write_text(json.dumps(M,indent=2)+'\n')
N=json.loads((R/'author_repair_notes.json').read_text());N['version']=3;N['changes'].append(dict(version=3,parameter='chair.curved_back.edge_treatment',before={'bevel_width':.04,'bevel_segments':3,'evaluated_zero_area_faces_per_back':2},after={'bevel':None,'cap_normals':'flat'},rationale='V2 evaluated audit still found two degenerate faces per back, exported GLB eight degenerate triangles per back. Remove bevel; preserve closed outward-wound raw annular sector. No position/dimension change.',provenance='technical topology repair; rounding remains approximate',evidence=[r for r in json.loads((R/'analysis/repair/region_comparison_v2.json').read_text()) if r['label'] in ['chairs','chair']]))
N['v2_actual_comparison_inspection']={str(i):msg for i,msg in [
(33,'Column now aligns better; two corrected lamps occupy source silhouettes; seating arrangement and pot species remain approximate; pale materials; missing floor reflection pattern.'),
(61,'Mirrors flat; wall pendant now present at source pixels. Seats separated but back direction/height and table proportions remain mismatched.'),
(74,'Wall pendant silhouette largely aligns; selected chair shifted too far upward/right; mirrors flat. Surface color and doors remain approximate.'),
(82,'Foliage fills trough lengths but too dense/coarse. Prominent foreground lamps absent after identity repair; unresolved pendant layout.'),
(91,'Column changed without fitting this frame: source/model offset persists. Trough boxes unchanged; foliage too dense and floor pattern absent.'),
(100,'Entry brass members thicker, glass now independent closed leaves. Column and remaining pendants imperfect; reflections too smooth/simple.'),
(108,'Column signed patch close to own DA3; foliage fills planter; furniture and lamp placement still differs.'),
(118,'Left column restored; planter foliage now too bulky; lowered desk and support physically valid but predicted-depth conflict remains.'),
(129,'Large top-centre pendant restored and close to own DA3. Column improved. Crest now visible. Furniture silhouettes and plant architecture remain LIMITED.'),
(155,'Crest visible and mirrors flat. Chairs separated; their RGB positions and floor appearance still differ; far-wall DA3 conflict retained.') ]}
N['v2_input_pass']='checks/input_v2/report.json';N['final_input_pass_plan']='checks/input_final; third and last full180 pass, after v3 paired inspection.'
(R/'author_repair_notes.json').write_text(json.dumps(N,indent=2)+'\n')
cmd=['/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender','-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(B/'tools/raycast_scene.py'),'--','--model',str(R/'scene.blend'),'--input-packet',str(B/'inputs/M3/packet.json'),'--model-manifest',str(R/'modelling_manifest.json'),'--out',str(R/'checks/input_v2')]
rep=json.loads((R/'checks/input_v2/report.json').read_text());inv=dict(actor='M3 revision author',command=cmd,environment={'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'},tool_session_id=77492,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completion_mtime_utc=datetime.datetime.fromtimestamp((R/'checks/input_v2/report.json').stat().st_mtime,datetime.timezone.utc).isoformat(),model_sha256=rep['model_sha256'],report_sha256=hashlib.sha256((R/'checks/input_v2/report.json').read_bytes()).hexdigest(),log='logs/input_v2.log',read_scope=[str(B/'inputs/M3'),str(R),str(B/'tools/raycast_scene.py'),str(B/'tools/depth_math.py')],write_scope=[str(R/'checks/input_v2'),str(R/'logs/input_v2.log')],purpose='second full180 after main repairs')
(R/'checks/input_v2/author_invocation.json').write_text(json.dumps(inv,indent=2)+'\n')
record('completed_v2_and_prepare_v3',[R/f'checks/v2/{i:04d}_comparison.jpg' for i in [33,61,74,82,91,100,108,118,129,155]]+[R/'checks/input_v2/report.json',R/'checks/input_v2/depth.npz'],{'visual_inspection':'All ten v2 actual full comparison sheets viewed (RGB, model/input optical-Z, residuals, masks, edges). Fixed-region array analysis in analyse_checks.py.', 'commands':['python3 TOOLS/visualize_checks.py --method-dir OUTPUT --packet INPUT/packet.json --version 2 > logs/visualize_v2.log','python3 analysis/repair/analyse_checks.py 2 > logs/region_comparison_v2.log','VENV_PYTHON analysis/repair/audit_glb.py 2 > logs/glb_audit_v2.log',cmd,'python3 analysis/repair/prepare_v3.py'],'input_v2_actor':'self; observed complete session77492','scope':'M3 only; no GT and no input mask changes','v3_reason':'degenerate bevel faces; remove modifier while keeping dimensions/positions'})
