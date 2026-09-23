"""Create a self-contained static site and reviewable deployment scaffolds."""
from pathlib import Path
import shutil,json,hashlib,zipfile,re
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist';DIST.mkdir(exist_ok=True)
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def sanitize(text):return text.replace(str(ROOT)+'/', '').replace(str(ROOT.parent)+'/', 'source_project/').replace('/home/hchen/Documents/','external_sources/')
for name in ['index.html','en.html','article.zh.md','article.en.md','style.css','site.js']:
 p=ROOT/'blog'/name;s=p.read_text().replace('href="../','href="').replace('src="../','src="').replace('](../','](');(DIST/name).write_text(s)
for name in ['assets','vendor']:shutil.copytree(ROOT/'blog'/name,DIST/name,dirs_exist_ok=True)
# Figure assets are allowlisted by actual article references.
for name in sorted(set(re.findall(r'(?:src|href)="(figures/[^"#]+)',(DIST/'index.html').read_text()+(DIST/'en.html').read_text()))):copy(ROOT/name,DIST/name)
for p in (ROOT/'docs').glob('*.md'):q=DIST/'docs'/p.name;q.parent.mkdir(exist_ok=True);q.write_text(sanitize(p.read_text()))
copy(ROOT/'references/research_sources.json',DIST/'references/research_sources.json')
reports=[ROOT/'results/release_verification.json',ROOT/'results/site_qa/report.json',ROOT/'results/final_evaluation.json',ROOT/'results/final_evaluation.csv',*list((ROOT/'results').glob('rgb_metrics_five_views*'))]
reports+=list((ROOT/'results/evaluation/pose/current').glob('*.json'))
reports+=list((ROOT/'results/evaluation/depth').glob('*/*.json'))
reports+=list((ROOT/'results/evaluation/geometry').glob('*/surface_metrics.json'))
reports+=[ROOT/'results/evaluation/tasks/drone_photographic_20/report.json',ROOT/'results/evaluation/novel_depth/report.json']
reports+=list((ROOT/'results/evaluation/tasks/gt_clearance').glob('*/*.json'))
for p in reports:
 q=DIST/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(sanitize(p.read_text()))
# A compact source/evidence bundle, not raw input data or runtime environments.
archive=DIST/'downloads/reproduction_sources.zip';archive.parent.mkdir(exist_ok=True)
source_files=[]
for folder in ['src','scripts','tests','configs']:
 source_files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in ['.py','.sh','.json','.md','.yaml','.yml'] and '__pycache__' not in p.parts and p.name not in ['github_public_login.py','publish_github_pages.py','publish_hf_assets.py','update_hf_publication_metadata.py'])
for root in [ROOT/'experiments/tasks/drone_M3/photographic_20',ROOT/'experiments/tasks/g1_M3/final_margin047']:
 source_files.extend(p for p in root.rglob('*') if p.is_file() and p.suffix in ['.json','.csv','.xml'] and p.name not in ['trajectory_full.csv'])
for m in ['M2','M3','M4']:
 root=ROOT/f'experiments/world_lobby/{m}/astra_model';source_files.extend(p for p in root.glob('*') if p.is_file() and p.suffix in ['.py','.json','.md'])
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in source_files:z.writestr(str(p.relative_to(ROOT)),sanitize(p.read_text()))
copy(archive,ROOT/'downloads/reproduction_sources.zip')
(DIST/'.nojekyll').touch()
(DIST/'robots.txt').write_text('User-agent: *\nAllow: /\n')
(DIST/'README.md').write_text('# Astra World Model Blog\n\nStatic bilingual site. Serve this directory with any HTTP server. See docs/REPRODUCIBILITY.md and downloads/reproduction_sources.zip. Models in assets are presentation cutaways, not evaluation artifacts.\n')
PUB=ROOT/'publish';PUB.mkdir(exist_ok=True);gp=PUB/'github_pages';shutil.copytree(DIST,gp,dirs_exist_ok=True);workflow=gp/'.github/workflows/pages.yml';workflow.parent.mkdir(parents=True,exist_ok=True);workflow.write_text('''name: Publish research blog
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: .
      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
''')
hf=PUB/'huggingface_assets';hf.mkdir(exist_ok=True);(hf/'README.md').write_text('''---
pretty_name: Astra World Lobby Reconstruction Artifacts
tags:
- 3d-reconstruction
- robotics
- blender
- scene-understanding
---
# Astra World Lobby artifacts

Companion assets for *When the map becomes a program*. One synthetic scene; four reconstruction routes plus direct geometry baselines. M1 uses a GT-assisted similarity registration; M4 takes GT camera poses as input. Semantics and physical parameters are declared/inferred, not independently verified.

The primary article belongs on GitHub Pages. Upload the selected original frozen `.blend` / `.glb` artifacts under M1–M4, their checksums and the evaluation reports. Do not confuse display cutaways with complete evaluation or physics scenes. Include the source attribution in the accompanying research records. No asset license is invented by this scaffold.

Drone: 15/20 collision-free candidate arrivals, 0/20 accurate rephotography. G1: 18/30 constrained model-world approach successes, over five correlated target families. No real-robot or GT-dynamics transfer claim.
''')
models=[]
for m in ['M1','M2','M3','M4']:
 folder=ROOT.parent/'visual-recon' if m=='M1' else ROOT/f'experiments/world_lobby/{m}/astra_model'
 for ext in ['blend','glb']:
  p=folder/f'scene.{ext}'
  if p.exists():models.append({'method':m,'source':str(p),'destination':f'{m}/scene.{ext}','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(PUB/'model_asset_manifest.json').write_text(json.dumps(models,indent=2)+'\n')
manifest=[{'path':str(p.relative_to(DIST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DIST.rglob('*')) if p.is_file()];(PUB/'site_manifest.json').write_text(json.dumps({'files':manifest,'total_bytes':sum(p['bytes'] for p in manifest),'external_publication':False},indent=2)+'\n')
# Check actual local links in published HTML, without touching external services.
class Links(HTMLParser):
 def __init__(self):super().__init__();self.paths=[];self.ids=set();self.anchors=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.add(d['id'])
  for a in ['src','href','poster']:
   u=d.get(a,'')
   if u.startswith('#'):self.anchors.append(u[1:])
   elif u and not re.match(r'^(?:https?:|data:|mailto:)',u):self.paths.append(u.split('#')[0])
missing=[]
for name in ['index.html','en.html']:
 p=Links();p.feed((DIST/name).read_text());missing+=[f'{name}: {q}' for q in p.paths if not (DIST/q).exists()];missing+=[f'{name}: #{q}' for q in p.anchors if q not in p.ids]
assert not missing,missing
(ROOT/'results/site_qa/link_report.json').write_text(json.dumps({'status':'pass','html_pages':2,'missing_local_links':missing,'site_bytes':sum(p['bytes'] for p in manifest),'source_bundle_files':len(source_files)},indent=2)+'\n')
print('PACKAGED',len(manifest),'files',round(sum(p['bytes'] for p in manifest)/1024**2,1),'MiB; local links PASS')
