"""All-four freeze gate, then plan depth evaluation and Tables 9–11; no authors."""
import concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
BLENDER='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender'
PY_APPEARANCE='/home/hchen/anaconda3/envs/mapanything/bin/python'
GT=RUN/'evaluation/gt_reference'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(cmd,log):
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
    print('COMPLETE',str(log.relative_to(RUN)),flush=True)
def check_frozen():
    records={}
    for method in ['M1','M2','M3','M4']:
        d=RUN/'models'/method;freeze=json.loads((d/'freeze_manifest.json').read_text());assert freeze['status']=='frozen_for_independent_GT_evaluation'
        for n,h in freeze['files'].items():assert sha(d/n)==h,(method,n)
        records[method]=freeze
    return records
def render(method):
    out=RUN/'evaluation/blog_tables_456/renders'/method
    command([BLENDER,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(RUN/'tools/render_frozen_views.py'),'--','--model',str(RUN/f'models/{method}/scene.blend'),'--cameras',str(RUN/'evaluation/depth/gt_cameras_modeling_180.json'),'--registration',str(RUN/f'evaluation/depth/{method}/registration.json'),'--out',str(out),'--indices','0,36,72,108,144','--samples','16'],out/'render.log')
def main():
    frozen=check_frozen()
    command([sys.executable,str(RUN/'tools/evaluate_models.py'),'--gt-root',str(GT),'--out',str(RUN/'evaluation/depth')],RUN/'evaluation/depth_run.log')
    regs=json.loads((RUN/'evaluation/depth/registrations.json').read_text());methods=[m for m,r in regs.items() if r['status']=='COMPLETE']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(render,methods):pass
    command([PY_APPEARANCE,str(RUN/'tools/evaluate_blog_table5.py')],RUN/'evaluation/blog_tables_456/appearance.log')
    command([BLENDER,'-b','--factory-startup','--threads','4','--python-exit-code','1','--python',str(RUN/'tools/evaluate_blog_tables_46_blender.py'),'--','--run',str(RUN),'--gt-usd',str(RUN.parents[1]/'drone-web/scenes/world_lobby/lobby.usda'),'--gt-depth',str(GT/'modeling_180/gt_depth_modeling_180.npz'),'--out',str(RUN/'evaluation/blog_tables_456')],RUN/'evaluation/blog_tables_456/geometry_novel.log')
    assert check_frozen()==frozen
    (RUN/'evaluation/COMPLETE.json').write_text(json.dumps(dict(status='COMPLETE',frozen_unchanged=True,methods=methods,model_hashes={m:f['files']['scene.blend'] for m,f in frozen.items()},GT_source=str(GT),author_feedback=False),indent=2)+'\n')
if __name__=='__main__':main()
