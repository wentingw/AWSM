"""Build bilingual static article from frozen metrics and editorial templates."""
from pathlib import Path
import json,sys,re,html,shutil
from blog_presentation import scene_comparison, image_comparison, number_figures
from blog_tasks_m4 import m4_task_section, m4_task_table
from blog_tables import NAMES, method_label, best_values, legend
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'runtime/site_python'));import markdown
B=ROOT/'blog'
PUBLICATION=ROOT/'publish/huggingface_publication.json'
def load(p):return json.loads((ROOT/p).read_text())
eval=load('results/final_evaluation.json');rows=eval['rows'];appearance=load('results/evaluation/appearance_five_views_20260925/report.json');assert appearance['status']=='complete';rgb={x['system']:x for x in appearance['rows']}
def num(v,d=3):return '—' if v is None else f'{v:.{d}f}'
def percent(v):return '—' if v is None else f'{100*v:.2f}%'
def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
TABLE_TITLES={
 'methods':('四种建模路线与输入信息','Four reconstruction routes and their inputs'),
 'pose_depth':('四种建模方法与三种融合基线的相机位姿和深度误差','Camera-pose and depth errors for four reconstruction methods and three fusion baselines'),
 'coverage':('采样相机位姿与深度的覆盖率','Coverage of sampled camera poses and depth'),
 'geometry':('四种建模方法与三种融合基线的几何误差','Geometry errors for four reconstruction methods and three fusion baselines'),
 'appearance':('四种建模方法在五个输入视角上的外观指标','Appearance metrics for four reconstruction methods at five input views'),
 'novel_depth':('同一场景新视角的深度误差','Depth errors at novel viewpoints in the same scene'),
 'm4_tasks':('M4 · GT 位姿 + MapAnything + Astra：下游任务结果与成功判据','M4 · GT pose + MapAnything + Astra: downstream task outcomes and success criteria'),
 'downloads':('完整冻结模型与下载格式','Complete frozen models and download formats'),
}
def caption_tables(body):
 pattern=r'<p class="table-heading" id="table-(\d+)-title">(.*?)</p>\s*<table>(.*?)</table>'
 def replace(match):
  number,title,content=match.groups()
  return f'<figure class="table-figure" id="table-{number}"><figcaption id="table-{number}-title">{title}</figcaption><div class="table-scroll"><table aria-labelledby="table-{number}-title">{content}</table></div></figure>'
 body=re.sub(pattern,replace,body,flags=re.S)
 if len(re.findall(r'<table\b',body))!=len(re.findall(r'<figure class="table-figure"',body)):
  raise ValueError('Every article table must have a numbered title')
 return body
for lang in ['zh','en']:
 zh=lang=='zh';labels={m:method_label(m,zh) for m in NAMES};text=(B/f'templates/article.{lang}.md').read_text()
 text=text.replace('{{M4_TASK_SECTION}}',m4_task_section(zh))
 for method,label in labels.items():text=text.replace('{{METHOD_'+method+'}}',label)
 text=text.replace('{{METRIC_LEGEND}}',legend(zh))
 table_number=0
 def table_heading(key):
  global table_number
  table_number+=1
  title=html.escape(TABLE_TITLES[key][0 if zh else 1])
  return f'<p class="table-heading" id="table-{table_number}-title"><span class="table-number">Table {table_number}.</span> {title}</p>'
 text=text.replace('{{METHOD_TABLE_TITLE}}',table_heading('methods'))
 main=[];coverage=[];geom=[]
 for r in rows:
  m=r['system'];p=r['pose'];n=r['native_depth'];d=r['model_depth'];g=r['geometry']
  pose='GT 输入' if zh else 'GT input'
  main.append([labels[m]+(' / Sim(3)†' if m=='M1' else ''),pose if m=='M4' else num(p.get('translation_rmse_m')),pose if m=='M4' else num(p.get('rotation_rmse_deg')),percent(n.get('absrel')),percent(d.get('absrel'))])
  coverage.append([labels[m],percent(p.get('frame_coverage')) if m not in ['M1','M4'] else '—',percent(n.get('valid_coverage')),percent(d.get('valid_coverage'))])
  geom.append([labels[m],num(g['model_to_gt_mean_m']),num(g['observed_gt_to_model_mean_m'])])
 # B2p shares M3's frontend; use its independently evaluated TSDF model depth.
 b2p=eval['supplementary_rows']['B2p'];p=b2p['pose'];n=b2p['native_depth'];d=b2p['model_depth']
 main.append([labels['B2p'],num(p['translation_rmse_m']),num(p['rotation_rmse_deg']),percent(n['absrel']),percent(d['absrel'])])
 coverage.append([labels['B2p'],percent(p['frame_coverage']),percent(n['valid_coverage']),percent(d['valid_coverage'])])
 text=text.replace('{{MAIN_TABLE}}',table_heading('pose_depth')+'\n\n'+table(['方法' if zh else 'System','ATE (m) ↓','Rotation (°) ↓','Native depth AbsRel ↓','Model depth AbsRel ↓'],best_values(main,{1:'min',2:'min',3:'min',4:'min'})))
 text=text.replace('{{COVERAGE_TABLE}}',table_heading('coverage')+'\n\n'+table(['方法' if zh else 'System','Sampled pose coverage ↑','Native depth coverage ↑','Model depth coverage ↑'],best_values(coverage,{1:'max',2:'max',3:'max'})))
 g=b2p['geometry'];geom.append([labels['B2p'],num(g['model_to_gt_mean_m']),num(g['observed_gt_to_model_mean_m'])])
 text=text.replace('{{GEOMETRY_TABLE}}',table_heading('geometry')+'\n\n'+table(['方法' if zh else 'System','Model → GT (m) ↓','Observed GT → model (m) ↓'],best_values(geom,{1:'min',2:'min'})))
 appearance_rows=[[labels[m],num(rgb[m]['psnr_db_mean'],2),num(rgb[m]['ssim_mean']),num(rgb[m]['lpips_alex_v01_mean'])] for m in ['M1','M2','M3','M4']]
 text=text.replace('{{APPEARANCE_TABLE}}',table_heading('appearance')+'\n\n'+table(['方法' if zh else 'System','PSNR (dB) ↑','SSIM ↑','LPIPS ↓'],best_values(appearance_rows,{1:'max',2:'max',3:'min'})))
 novel_path=ROOT/'results/evaluation/novel_depth/report.json'
 if novel_path.exists():
  n=json.loads(novel_path.read_text());intro=n.get('article_zh' if zh else 'article_en','')
  if 'rows' in n:
   intro+='\n\n'+table_heading('novel_depth')+'\n\n'+table(['方法' if zh else 'System','Novel depth AbsRel ↓','RMSE (m) ↓','Coverage ↑','Penalized MAE (m) ↓'],best_values([[labels[r['method']],percent(r['absrel']),num(r['rmse_m']),percent(r['valid_coverage']),num(r['missing_penalty_mae_m'])] for r in n['rows']],{1:'min',2:'min',3:'max',4:'min'}))
   intro+='\n\n[Independent BVH report](../results/evaluation/novel_depth/report.json)'
 else:
  intro=('补充新视角使用同一仿真场景中的位姿扰动，不是独立采集或跨场景测试。旧 Workbench 图像只有灰色材质，已排除外观评分；Cycles 与原始 Isaac RTX 的材质及光照转换也不能保证一致。因此主文不报告新视角 RGB 分数。' if zh else 'Supplementary viewpoints are pose perturbations within the same simulated scene, not an independent capture or cross-scene test. Earlier Workbench RGB is gray-clay and excluded from appearance scoring. Cycles material and lighting conversion does not guarantee agreement with the original Isaac RTX capture, so we do not report novel-view RGB scores.')
 text=text.replace('{{NOVEL_DEPTH}}',intro)
 text=text.replace('{{M4_TASK_TABLE}}',m4_task_table(zh,table,table_heading))
 refs=[('GPT-6 Astra','https://developers.openai.com/api/docs/models/gpt-6-astra'),('ViPE','https://arxiv.org/abs/2508.10934'),('MapAnything','https://github.com/facebookresearch/map-anything'),('OpenVINS','https://docs.openvins.com/'),('3D Gaussian Splatting','https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/'),('VGGT','https://github.com/facebookresearch/vggt'),('Hydra','https://github.com/MIT-SPARK/Hydra'),('ConceptFusion','https://concept-fusion.github.io/'),('VLMaps','https://github.com/vlmaps/vlmaps'),('SceneScript','https://arxiv.org/abs/2403.13064'),('Real2Code','https://arxiv.org/abs/2406.08474'),('Holodeck','https://github.com/allenai/Holodeck'),('Lab Kitchen Twin','https://frank-zy-dou.github.io/kitchen-twin/'),('LiteReality-Agent','https://github.com/LiteReality/LiteReality-Agent')]
 text=text.replace('{{REFERENCES}}',' · '.join(f'[{name}]({url})' for name,url in refs));assert '{{' not in text;(B/f'article.{lang}.md').write_text(text)
 md=markdown.Markdown(extensions=['tables','fenced_code','toc']);body=md.convert(text);body=re.sub(r'<h1.*?</h1>','',body,count=1,flags=re.S);body=re.sub(r'<h2.*?</h2>','',body,count=1,flags=re.S)
 body=re.sub(r'<p><img alt="([^"]*)" src="([^"]*)" /></p>',r'<figure><a href="\2"><img loading="lazy" src="\2" alt="\1"></a><figcaption>\1</figcaption></figure>',body)
 compare=image_comparison(zh)
 first_grid=body.find('<figure><a href="../figures/five_view_comparison.jpg">')
 body=body[:first_grid]+compare+body[first_grid:] if first_grid>=0 else body
 model=scene_comparison(zh)
 marker='<h2 id="'+('_4' if zh else 'five-fixed-views')+'">'
 pos=body.find(marker)
 if pos>=0:pos=body.index('</h2>',pos)+len('</h2>')
 else:pos=body.find('<figure class="interactive"')
 if pos>=0:body=body[:pos]+model+body[pos:]
 # Asset downloads are pinned to the exact published HF commit.
 if PUBLICATION.exists():
  pub=json.loads(PUBLICATION.read_text());base=pub['url'];revision=pub['commit']
  heading='完整模型与实验资产' if zh else 'Full models and experiment assets'
  detail='下载完整冻结模型；这里的原模型保留墙体与顶棚。页面交互模型是用于检查内部结构的展示剖视副本。' if zh else 'Download the complete frozen models, including walls and ceilings. The interactive models above are display cutaways for inspection.'
  links=[]
  for m in ['M1','M2','M3','M4']:
   links.append('<tr><th>'+html.escape(labels[m])+'</th><td><a href="'+base+'/resolve/'+revision+'/models/'+m+'/scene.blend?download=true">Blender .blend</a></td><td><a href="'+base+'/resolve/'+revision+'/models/'+m+'/scene.glb?download=true">GLB .glb</a></td></tr>')
  downloads='<section class="downloads"><h2 id="assets">'+heading+'</h2><p>'+detail+'</p>'+table_heading('downloads')+'<table><thead><tr><th>METHOD</th><th>EDITABLE SCENE</th><th>PORTABLE MODEL</th></tr></thead><tbody>'+''.join(links)+'</tbody></table><p><a href="'+base+'/tree/'+revision+'">Hugging Face · models, baselines, evaluations &amp; tasks</a><br><a href="'+base+'/resolve/'+revision+'/SHA256SUMS">SHA256SUMS</a> · <a href="'+base+'/resolve/'+revision+'/payload_manifest.json">Asset manifest</a></p><p class="caption">Frozen asset revision: <code>'+revision+'</code></p></section>'
  body+=downloads
 body=caption_tables(body)
 # Videos are physically executed runs; display replay is explicitly labelled.
 for task,heading in [('g1','G1：按照自然语言找到指定花盆</h3>' if zh else 'Unitree G1: find a specified planter from language</h3>'),('drone',None)]:
  video_path=f'assets/m4_tasks/{task}_episode.mp4'
  if not (B/video_path).exists():raise FileNotFoundError(video_path)
  if task=='g1':
   title='M4 / episode 00 · 已记录的 G1 关节状态回放；M4 展示剖视与简化着色，1×。' if zh else 'M4 / episode 00 · replay of recorded G1 joint states; M4 display cutaway and simplified shading, 1×.'
  else:
   title='M4 / query 13 · 实际动力学轨迹回放；M4 展示剖视，1×。到达候选视点，精确复拍失败。' if zh else 'M4 / query 13 · replay of the actual dynamics trajectory; M4 display cutaway, 1×. Candidate arrival succeeds, precise rephotography fails.'
  video=f'<figure class="video"><video controls playsinline preload="metadata" poster="assets/m4_tasks/{task}_poster.jpg"><source src="{video_path}" type="video/mp4"></video><figcaption>{title}</figcaption></figure>'
  pos=body.find(heading) if heading else body.find('<figure><a href="../figures/m4_tasks/drone_comparison.jpg">')
  if pos<0:raise ValueError('Missing task video insertion point: '+task)
  if heading:pos=body.index('</h3>',pos)+5
  body=body[:pos]+video+body[pos:]
 title='当地图成为程序' if zh else 'When the map becomes a program'
 subtitle='GPT‑6 Astra × Blender × 可执行三维世界' if zh else 'GPT‑6 Astra × Blender × executable 3D worlds'
 description='四条建模路线、六个主系统、两类机器人任务。让几何测量与实际执行检验生成式场景建模。' if zh else 'Four reconstruction routes, six main systems, two robot tasks. Testing generated scene programs with geometry and execution.'
 toc='<ul>'+''.join(f'<li><a href="#{id}">{label}</a></li>' for id,label in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',body))+'</ul>'
 page=f'''<!doctype html><html lang="{'zh-CN' if zh else 'en'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} — Astra World Models</title><meta name="description" content="{description}"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:image" content="assets/hero.jpg"><link rel="stylesheet" href="style.css"><script type="importmap">{{"imports":{{"three":"./vendor/three/three.module.js"}}}}</script><script type="module" src="scene-compare.js"></script></head><body><div class="reading-progress" id="progress"></div><nav><a class="brand" href="{'index.html' if zh else 'en.html'}">ASTRA <span>/ WORLD MODELS</span></a><div><a href="index.html" {'aria-current="page"' if zh else ''}>中文</a><a href="en.html" {'' if zh else 'aria-current="page"'}>EN</a><a href="../results/final_evaluation.json">DATA ↗</a></div></nav><header><p class="eyebrow">RESEARCH NOTE · UPDATED 24 SEPTEMBER 2026</p><h1>{title}</h1><p class="subtitle">{subtitle}</p><p class="lead">{description}</p><div class="meta"><span>360 s / synthetic capture</span><span>180 modelling views</span><span>Measured successes & failures</span></div></header><figure class="hero"><img src="assets/hero.jpg" alt="Original simulator image beside the Astra M4 reconstruction"><figcaption>{'同一输入视角：原始仿真 RGB 与 M4 重建。M4 获得 GT 相机位姿，不获得 GT 网格。' if zh else 'Same input view: simulator RGB and M4 reconstruction. M4 receives GT camera poses, not the GT mesh.'}</figcaption></figure><div class="layout"><aside class="toc"><p>ON THIS PAGE</p>{toc}</aside><main><article>{body}</article></main></div><footer><p>WORLD LOBBY · ASTRA / BLENDER</p><p>{'一次可复算的工程实验。原始结果、失败与适用边界均保留。' if zh else 'A reproducible engineering experiment, with failures and limits retained.'}</p><a href="article.{lang}.md">Markdown</a> · <a href="../docs/REPRODUCIBILITY.md">Reproduction</a> · <a href="../results/final_evaluation.csv">CSV</a> · <a href="../downloads/reproduction_sources.zip">Code &amp; episode records</a></footer><script src="site.js"></script></body></html>'''
 page=number_figures(page,zh)
 (B/('index.html' if zh else 'en.html')).write_text(page)
# Only the five published inputs are copied, never a whole private session.
views=[0,36,72,108,144];display=B/'assets/views';display.mkdir(exist_ok=True)
from PIL import Image
for k in views:
 p=next((ROOT/'data/world_lobby/rgb_180').glob(f'{k:06d}_*.png'));Image.open(p).convert('RGB').resize((640,480),Image.Resampling.LANCZOS).save(display/f'GT_{k:03d}.jpg',quality=94)
 for m in ['M1','M2','M3','M4','B1','B2']:shutil.copy2(ROOT/f'results/{m}/renders/{k:03d}.png',display/f'{m}_{k:03d}.png')
print('BUILT bilingual article and interactive pages')
