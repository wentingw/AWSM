"""Build bilingual static article from frozen metrics and editorial templates."""
from pathlib import Path
import json,sys,re,html,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'runtime/site_python'));import markdown
B=ROOT/'blog'
PUBLICATION=ROOT/'publish/huggingface_publication.json'
def load(p):return json.loads((ROOT/p).read_text())
eval=load('results/final_evaluation.json');rows=eval['rows'];rgb={x['system']:x for x in load('results/rgb_metrics_five_views_mean.json')['rows']}
def num(v,d=3):return '—' if v is None else f'{v:.{d}f}'
def percent(v):return '—' if v is None else f'{100*v:.2f}%'
def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
labels={'M1':'M1 · RGB / Sim(3)†','M2':'M2 · ViPE + Astra','M3':'M3 · VIO + MapAnything + Astra','M4':'M4 · GT pose + MapAnything + Astra','B1':'B1 · ViPE + TSDF','B2':'B2 · MapAnything + TSDF'}
for lang in ['zh','en']:
 zh=lang=='zh';text=(B/f'templates/article.{lang}.md').read_text()
 main=[];coverage=[];geom=[]
 for r in rows:
  m=r['system'];p=r['pose'];n=r['native_depth'];d=r['model_depth'];g=r['geometry']
  pose='GT 输入' if zh else 'GT input'
  main.append([labels[m],pose if m=='M4' else num(p.get('translation_rmse_m')),pose if m=='M4' else num(p.get('rotation_rmse_deg')),percent(n.get('absrel')),percent(d.get('absrel'))])
  coverage.append([m,percent(p.get('frame_coverage')) if m not in ['M1','M4'] else '—',percent(n.get('valid_coverage')),percent(d.get('valid_coverage'))])
  geom.append([m,num(g['model_to_gt_mean_m']),num(g['observed_gt_to_model_mean_m']),num(rgb[m]['psnr_db_mean'],2),num(rgb[m]['ssim_mean'])])
 text=text.replace('{{MAIN_TABLE}}',table(['方法' if zh else 'System','ATE (m) ↓','Rotation (°) ↓','Native depth AbsRel ↓','Model depth AbsRel ↓'],main))
 text=text.replace('{{COVERAGE_TABLE}}',table(['方法' if zh else 'System','Sampled pose coverage','Native depth coverage','Model depth coverage'],coverage))
 text=text.replace('{{GEOMETRY_RGB_TABLE}}',table(['方法' if zh else 'System','Model → GT (m) ↓','Observed GT → model (m) ↓','PSNR (dB) ↑','SSIM ↑'],geom))
 novel_path=ROOT/'results/evaluation/novel_depth/report.json'
 if novel_path.exists():
  n=json.loads(novel_path.read_text());intro=n.get('article_zh' if zh else 'article_en','')
  if 'rows' in n:
   intro+='\n\n'+table(['System','Novel depth AbsRel ↓','RMSE (m) ↓','Coverage','Penalized MAE (m) ↓'],[[r['method'],percent(r['absrel']),num(r['rmse_m']),percent(r['valid_coverage']),num(r['missing_penalty_mae_m'])] for r in n['rows']])
   intro+='\n\n[Independent BVH report](../results/evaluation/novel_depth/report.json)'
 else:
  intro=('补充新视角使用同一仿真场景中的位姿扰动，不是独立采集或跨场景测试。旧 Workbench 图像只有灰色材质，已排除外观评分；Cycles 与原始 Isaac RTX 的材质及光照转换也不能保证一致。因此主文不报告新视角 RGB 分数。' if zh else 'Supplementary viewpoints are pose perturbations within the same simulated scene, not an independent capture or cross-scene test. Earlier Workbench RGB is gray-clay and excluded from appearance scoring. Cycles material and lighting conversion does not guarantee agreement with the original Isaac RTX capture, so we do not report novel-view RGB scores.')
 text=text.replace('{{NOVEL_DEPTH}}',intro)
 clearance=('**GT 静态审计揭示了迁移风险。** 将实际轨迹按固定全局配准变换到原始 GT 网格后，20/20 条无人机轨迹都有中心点距 GT 表面小于 0.30 m 的样本；G1 脚底代理低于参考 GT 地面约 0.33–0.71 m。它们是表面距离和高度诊断，没有 inside/outside 判定，也没有 GT 动力学重放。因此既不能当作确定的碰撞次数，也不能把模型世界成功写成原场景成功。' if zh else '**A static GT audit exposes the transfer gap.** After applying the fixed global registration, all 20 drone trajectories contain a center sample within 0.30 m of the original GT surface. G1 foot proxies lie roughly 0.33–0.71 m below the reference GT floor. These are surface-distance and height diagnostics without inside/outside classification or GT dynamics replay. They are neither confirmed collision counts nor evidence of successful transfer.')
 text=text.replace('{{GT_CLEARANCE}}',clearance)
 refs=[('GPT-6 Astra','https://developers.openai.com/api/docs/models/gpt-6-astra'),('ViPE','https://arxiv.org/abs/2508.10934'),('MapAnything','https://github.com/facebookresearch/map-anything'),('OpenVINS','https://docs.openvins.com/'),('3D Gaussian Splatting','https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/'),('VGGT','https://github.com/facebookresearch/vggt'),('Hydra','https://github.com/MIT-SPARK/Hydra'),('ConceptFusion','https://concept-fusion.github.io/'),('VLMaps','https://github.com/vlmaps/vlmaps'),('SceneScript','https://arxiv.org/abs/2403.13064'),('Real2Code','https://arxiv.org/abs/2406.08474'),('Holodeck','https://github.com/allenai/Holodeck'),('Lab Kitchen Twin','https://frank-zy-dou.github.io/kitchen-twin/'),('LiteReality-Agent','https://github.com/LiteReality/LiteReality-Agent')]
 text=text.replace('{{REFERENCES}}',' · '.join(f'[{name}]({url})' for name,url in refs));assert '{{' not in text;(B/f'article.{lang}.md').write_text(text)
 md=markdown.Markdown(extensions=['tables','fenced_code','toc']);body=md.convert(text);body=re.sub(r'<h1.*?</h1>','',body,count=1,flags=re.S);body=re.sub(r'<h2.*?</h2>','',body,count=1,flags=re.S)
 body=re.sub(r'<table>(.*?)</table>',r'<div class="table-scroll"><table>\1</table></div>',body,flags=re.S)
 body=re.sub(r'<p><img alt="([^"]*)" src="([^"]*)" /></p>',r'<figure><a href="\2"><img loading="lazy" src="\2" alt="\1"></a><figcaption>\1</figcaption></figure>',body)
 compare='''<div class="interactive" id="compare"><div class="controlrow"><label>METHOD <select id="compare-method"><option>M1</option><option selected>M2</option><option>M3</option><option>M4</option><option>B1</option><option>B2</option></select></label><label>KEYFRAME <select id="compare-frame"><option>0</option><option selected>36</option><option>72</option><option>108</option><option>144</option></select></label></div><div class="compare-pair"><figure><img id="compare-pred" alt="Selected reconstruction"><figcaption id="compare-label">M2</figcaption></figure><figure><img id="compare-gt" alt="Original simulator RGB"><figcaption>INPUT / SIMULATOR RGB</figcaption></figure></div></div>'''
 needle='<h2 id="'+('' if False else 'unused')
 first_grid=body.find('<figure><a href="../figures/five_view_comparison.jpg">');body=body[:first_grid]+compare+body[first_grid:] if first_grid>=0 else body
 modeltitle='旋转、放大，检查场景结构' if zh else 'Rotate the scene. Inspect its structure.'
 modelnote='展示副本移除了墙、窗、门和顶棚，方便检查内部；评测和物理始终使用完整冻结场景。模型中的对象名称与物性仍是声明的假设。' if zh else 'Display copies remove walls, windows, doors, and ceilings for inspection. Evaluation and physics use complete frozen scenes. Object labels and physical properties remain declared assumptions.'
 model=f'''<aside class="model-panel"><div class="controlrow"><h3>{modeltitle}</h3><label>MODEL <select id="model-select"><option>M2</option><option selected>M3</option><option>M4</option></select></label></div><model-viewer id="scene-viewer" src="assets/M3_cutaway.glb" alt="Frozen M3 scene, presentation cutaway" camera-controls touch-action="pan-y" shadow-intensity="0.3" exposure="1" environment-image="neutral" camera-orbit="-30deg 48deg 85%" interaction-prompt="none" loading="lazy"></model-viewer><p class="caption">{modelnote} <a href="assets/cutaway_provenance.json">Provenance</a></p></aside>'''
 marker='<h2 id="'+('五个固定视角' if zh else 'five-fixed-views')+'">';pos=body.find(marker)
 if pos<0:pos=body.find('<div class="interactive"')
 if pos>=0:body=body[:pos]+model+body[pos:]
 # Asset downloads are pinned to the exact published HF commit.
 if PUBLICATION.exists():
  pub=json.loads(PUBLICATION.read_text());base=pub['url'];revision=pub['commit']
  heading='完整模型与实验资产' if zh else 'Full models and experiment assets'
  detail='下载完整冻结模型；这里的原模型保留墙体与顶棚。页面交互模型是用于检查内部结构的展示剖视副本。' if zh else 'Download the complete frozen models, including walls and ceilings. The interactive models above are display cutaways for inspection.'
  links=[]
  for m in ['M1','M2','M3','M4']:
   links.append('<tr><th>'+m+'</th><td><a href="'+base+'/resolve/'+revision+'/models/'+m+'/scene.blend?download=true">Blender .blend</a></td><td><a href="'+base+'/resolve/'+revision+'/models/'+m+'/scene.glb?download=true">GLB .glb</a></td></tr>')
  downloads='<section class="downloads"><h2 id="assets">'+heading+'</h2><p>'+detail+'</p><div class="table-scroll"><table><thead><tr><th>METHOD</th><th>EDITABLE SCENE</th><th>PORTABLE MODEL</th></tr></thead><tbody>'+''.join(links)+'</tbody></table></div><p><a href="'+base+'/tree/'+revision+'">Hugging Face · models, baselines, evaluations &amp; tasks</a><br><a href="'+base+'/resolve/'+revision+'/SHA256SUMS">SHA256SUMS</a> · <a href="'+base+'/resolve/'+revision+'/payload_manifest.json">Asset manifest</a></p><p class="caption">Frozen asset revision: <code>'+revision+'</code></p></section>'
  body+=downloads
 # Videos are physically executed runs; display replay is explicitly labelled.
 gvideo=B/'assets/g1_episode.mp4';dvideo=B/'assets/drone_episode.mp4'
 if gvideo.exists():
  title='G1 · 真实策略轨迹 / MuJoCo 简化着色' if zh else 'G1 · actual policy trajectory / simplified MuJoCo shading'
  video=f'<figure class="video"><video controls playsinline preload="metadata" poster="assets/g1_poster.jpg"><source src="assets/g1_episode.mp4" type="video/mp4"></video><figcaption>{title}</figcaption></figure>'
  phrase='<h3 id="'+('g1按照语言寻找对象' if zh else 'unitree-g1-find-the-described-object')+'">'
  pos=body.find('G1：按照语言寻找对象</h3>') if zh else body.find('Unitree G1: find the described object</h3>')
  if pos>=0:pos=body.index('</h3>',pos)+5;body=body[:pos]+video+body[pos:]
 if dvideo.exists():
  title='无人机 · 实际轨迹展示回放；精确复拍失败保留' if zh else 'Drone · replay of actual dynamics trajectory; rephotography failure retained'
  video=f'<figure class="video"><video controls playsinline preload="metadata" poster="assets/drone_poster.jpg"><source src="assets/drone_episode.mp4" type="video/mp4"></video><figcaption>{title}</figcaption></figure>'
  pos=body.find('<figure><a href="../figures/drone_three_queries.jpg">');body=body[:pos]+video+body[pos:] if pos>=0 else body
 title='当地图成为程序' if zh else 'When the map becomes a program'
 subtitle='GPT‑6 Astra × Blender × 可执行三维世界' if zh else 'GPT‑6 Astra × Blender × executable 3D worlds'
 description='四条建模路线、六个主系统、两类机器人任务。让几何测量与实际执行检验生成式场景建模。' if zh else 'Four reconstruction routes, six main systems, two robot tasks. Testing generated scene programs with geometry and execution.'
 toc='<ul>'+''.join(f'<li><a href="#{id}">{label}</a></li>' for id,label in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',body))+'</ul>'
 page=f'''<!doctype html><html lang="{'zh-CN' if zh else 'en'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — Astra World Models</title><meta name="description" content="{description}"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:image" content="assets/hero.jpg"><link rel="stylesheet" href="style.css"><script type="module" src="vendor/model-viewer.min.js"></script></head><body><div class="reading-progress" id="progress"></div><nav><a class="brand" href="{'index.html' if zh else 'en.html'}">ASTRA <span>/ WORLD MODELS</span></a><div><a href="index.html" {'aria-current="page"' if zh else ''}>中文</a><a href="en.html" {'' if zh else 'aria-current="page"'}>EN</a><a href="../results/final_evaluation.json">DATA ↗</a></div></nav><header><p class="eyebrow">RESEARCH NOTE · 23 SEPTEMBER 2026</p><h1>{title}</h1><p class="subtitle">{subtitle}</p><p class="lead">{description}</p><div class="meta"><span>360 s / synthetic capture</span><span>180 modelling views</span><span>Measured successes & failures</span></div></header><figure class="hero"><img src="assets/hero.jpg" alt="Original simulator image beside the Astra M4 reconstruction"><figcaption>{'同一输入视角：原始仿真 RGB 与 M4 重建。M4 获得 GT 相机位姿，不获得 GT 网格。' if zh else 'Same input view: simulator RGB and M4 reconstruction. M4 receives GT camera poses, not the GT mesh.'}</figcaption></figure><div class="layout"><aside class="toc"><p>ON THIS PAGE</p>{toc}</aside><main><article>{body}</article></main></div><footer><p>WORLD LOBBY · ASTRA / BLENDER</p><p>{'一次可复算的工程实验。原始结果、失败与适用边界均保留。' if zh else 'A reproducible engineering experiment, with failures and limits retained.'}</p><a href="article.{lang}.md">Markdown</a> · <a href="../docs/REPRODUCIBILITY.md">Reproduction</a> · <a href="../results/final_evaluation.csv">CSV</a> · <a href="../downloads/reproduction_sources.zip">Code &amp; episode records</a></footer><script src="site.js"></script></body></html>'''
 (B/('index.html' if zh else 'en.html')).write_text(page)
# Only the five published inputs are copied, never a whole private session.
views=[0,36,72,108,144];display=B/'assets/views';display.mkdir(exist_ok=True)
from PIL import Image
for k in views:
 p=next((ROOT/'data/world_lobby/rgb_180').glob(f'{k:06d}_*.png'));Image.open(p).convert('RGB').resize((640,480),Image.Resampling.LANCZOS).save(display/f'GT_{k:03d}.jpg',quality=94)
 for m in ['M1','M2','M3','M4','B1','B2']:shutil.copy2(ROOT/f'results/{m}/renders/{k:03d}.png',display/f'{m}_{k:03d}.png')
print('BUILT bilingual article and interactive pages')
