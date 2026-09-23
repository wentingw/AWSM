"""Verify release provenance, score invariants, and required experiment artifacts."""
import json,hashlib,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=load('results/final_evaluation.json')['rows'];assert {r['system'] for r in rows}=={'M1','M2','M3','M4','B1','B2'}
by={r['system']:r for r in rows};assert by['B1']['pose']['translation_rmse_m']==by['M2']['pose']['translation_rmse_m'];assert not by['M1']['pose'].get('translation_rmse_m');assert not by['M4']['pose'].get('translation_rmse_m')
for m in ['M2','M3','M4']:
 r=load(f'results/{m}/render_manifest.json');assert digest(r['model_path'])==r['model_sha256'];assert (ROOT/f'results/{m}/evaluation_complete.json').exists()
r=load('results/M1/render_manifest.json');assert digest(r['model_path'])==r['model_sha256']=='fd2ff0bc5cbc1efd47457410cd6474c9718422cccd0b60a8fb7c36e2f01c641b'
vp=load('experiments/world_lobby/M2/vipe_full_20260923/complete.json');assert vp['frames']==8999;assert len(list((ROOT/'experiments/world_lobby/M2/vipe_full_20260923/depth').glob('*.npz')))==8999
nov=load('results/evaluation/novel_depth/report.json');assert nov['gttriangles']==9984967;assert len(nov['rows'])==7
for r in nov['rows']:
 assert r['pixels_domain']==100000
 expect=(r['sum_absolute_error_m']+30*(r['pixels_domain']-r['pixels_valid']))/r['pixels_domain'];assert abs(expect-r['missing_penalty_mae_m'])<1e-10;assert abs(r['rmse_m']**2-r['sum_squared_error_m2']/r['pixels_valid'])<1e-9
 assert digest(nov['model_specs'][r['method']]['path'])==nov['model_specs'][r['method']]['sha256']
for lang in ['zh','en']:
 s=(ROOT/f'blog/article.{lang}.md').read_text();assert '{{' not in s and 'RESULTS_' not in s
q=load('results/evaluation/tasks/drone_photographic_20/report.json');assert q['counts']['episodes']==20 and q['counts']['strict_rephotography_successes']==0;assert q['counts']['collisions']==5
for name in ['five_view_comparison.jpg','current_trajectories.png','model_depth_error_pixel_heatmap.png','drone_three_queries.jpg']:assert (ROOT/'figures'/name).exists()
for p in [ROOT/'scripts/build_blog.py',ROOT/'scripts/package_blog.py',ROOT/'scripts/evaluate_novel_depth_blender.py',ROOT/'scripts/qa_blog_browser.py']:ast.parse(p.read_text())
report={'status':'pass','checks':['six methods and shared frontend identity','original/frozen model hashes unchanged','8999 ViPE outputs and completion marker','novel GT triangle count and pooled penalty/RMSE identities','seven novel-view model hashes','no article placeholders','drone complete batch and separate true goal success','required figures present','release script syntax'],'external_publication':False};(ROOT/'results/release_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
