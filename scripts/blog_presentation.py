"""Presentation markup for synchronized scene comparison and numbered figures."""
import html
import re

METHOD_NAMES = {
 'M1': ('纯视觉 + Astra', 'RGB-only + Astra'),
 'M2': ('ViPE + Astra', 'ViPE + Astra'),
 'M3': ('OpenVINS + MapAnything + Astra', 'OpenVINS + MapAnything + Astra'),
 'M4': ('GT 位姿 + MapAnything + Astra', 'GT pose + MapAnything + Astra'),
 'B1': ('ViPE + TSDF', 'ViPE + TSDF'),
 'B2': ('MapAnything + TSDF', 'MapAnything + TSDF'),
 'GT': ('原始仿真场景', 'Original simulator scene'),
}


def options(methods, selected, zh):
 return ''.join(f'<option value="{m}"'+(' selected' if m==selected else '')+f'>{m} · {html.escape(METHOD_NAMES[m][0 if zh else 1])}</option>' for m in methods)


def scene_comparison(zh):
 title='旋转、放大，检查场景结构' if zh else 'Rotate the scene. Inspect its structure.'
 method='重建方法 / GT' if zh else 'Reconstruction / GT'
 compare='中轴线对比 GT' if zh else 'Split comparison with GT'
 single='单独查看所选场景' if zh else 'View selected scene alone'
 reset='重置视角' if zh else 'Reset view'
 retry='重试' if zh else 'Retry'
 split='移动中轴线' if zh else 'Move divider'
 help=('拖动场景旋转，滚轮或双指缩放；拖动中轴线比较同一视角。选择 GT 可单独查看原始仿真场景。' if zh else 'Drag the scene to rotate, scroll or pinch to zoom, and drag the divider to compare the same view. Select GT to inspect the original simulator scene alone.')
 note=('两侧使用同一相机、米制坐标和既有评测配准，不对各模型单独居中或缩放。M1 沿用已披露的 GT 辅助 Sim(3)，其余方法沿用既有 SE(3) 配准，M4 为 GT 坐标。展示副本采用剖视与网格简化，材质为网页展示转换；它们不是完整评测模型，也不能用于衡量真实物性或外观精度。' if zh else 'Both sides share one camera, metric coordinates, and the existing evaluation registration; models are never centered or rescaled independently. M1 retains the disclosed GT-assisted Sim(3); other methods retain their SE(3) registration, with M4 already in GT coordinates. These cutaway, simplified display copies use converted web materials. They are not full evaluation models and do not establish physical or appearance accuracy.')
 return f'''<figure class="scene-comparison" id="scene-comparison" data-state="idle"><h3>{title}</h3><div class="scene-toolbar"><label class="method-control">{method}<select id="model-select">{options(['M1','M2','M3','M4','GT'],'M3',zh)}</select></label><label>{'显示方式' if zh else 'Display'}<select id="scene-mode"><option value="compare">{compare}</option><option value="single">{single}</option></select></label><button id="scene-reset" type="button">{reset}</button></div><div class="scene-stage"><span class="scene-label scene-label-left">M3 · OpenVINS + MapAnything + Astra</span><span class="scene-label scene-label-right">GT · {'原始仿真场景' if zh else 'Original simulator scene'}</span><button class="scene-divider" type="button" role="slider" aria-label="{split}" aria-valuemin="2" aria-valuemax="98" aria-valuenow="50" aria-orientation="horizontal"><span aria-hidden="true">↔</span></button><div class="scene-status" role="status" aria-live="polite">{'滚动到此处加载三维场景' if zh else 'Scroll here to load the 3D scenes'}</div></div><label class="scene-split-control" for="scene-split">{split}<input id="scene-split" type="range" min="2" max="98" value="50"></label><button id="scene-retry" class="scene-retry" type="button">{retry}</button><p class="scene-help">{help}</p><figcaption>{note} <a href="assets/comparison/comparison_provenance.json">{'展示资产来源与变换' if zh else 'Display provenance and transforms'}</a></figcaption></figure>'''


def image_comparison(zh):
 caption='固定输入视角的重建渲染与原始 RGB；可选择方法与关键帧。' if zh else 'Reconstruction render and original RGB at a fixed input view; select the method and keyframe.'
 return f'''<figure class="interactive" id="compare"><div class="controlrow"><label>{'方法' if zh else 'METHOD'} <select id="compare-method">{options(['M1','M2','M3','M4','B1','B2'],'M2',zh)}</select></label><label>{'关键帧' if zh else 'KEYFRAME'} <select id="compare-frame"><option>0</option><option selected>36</option><option>72</option><option>108</option><option>144</option></select></label></div><div class="compare-pair"><div><img id="compare-pred" alt="Selected reconstruction"><p class="compare-subcaption" id="compare-label">M2 · ViPE + Astra</p></div><div><img id="compare-gt" alt="Original simulator RGB"><p class="compare-subcaption">INPUT / SIMULATOR RGB</p></div></div><figcaption>{caption}</figcaption></figure>'''


FIGURE_TITLES={
 'hero':('原始场景与 GT 位姿约束重建','Original scene and GT-pose-conditioned reconstruction'),
 'methods_plan.svg':('四条建模路线与独立评测流程','Four reconstruction routes and independent evaluation'),
 'scene-comparison':('重建场景与 GT 的同视角交互比较','Interactive reconstruction–GT comparison with a shared camera'),
 'compare':('固定视角的渲染与输入图像对比','Fixed-view render and input-image comparison'),
 'five_view_comparison.jpg':('四种重建方法与输入 GT 的五视角比较','Five-view comparison of four reconstruction methods and input GT'),
 'direct_baseline_comparison.jpg':('直接几何融合基线与输入 GT','Direct geometry-fusion baselines and input GT'),
 'model_depth_error_pixel_heatmap.png':('固定 GT 相机下的模型深度误差','Model-depth errors at fixed GT cameras'),
 'current_trajectories.png':('配准后的相机轨迹与平移误差','Registered camera trajectories and translation errors'),
 'drone_episode.mp4':('无人机实际轨迹回放','Replay of the executed drone trajectory'),
 'm4_tasks/task_flow.':('冻结 M4 场景中的两条任务流程','Two task pipelines in the frozen M4 scene'),
 'drone_comparison.jpg':('M4 无人机参考图与实际终点图','M4 drone reference images and achieved endpoint images'),
 'g1_comparison.jpg':('M4 中的花盆指令与终点可见性','Planter instructions and endpoint visibility in M4'),
 'g1_episode.mp4':('宇树 G1 策略执行轨迹','Unitree G1 policy execution trajectory'),
}


def number_figures(page, zh):
 counter=0
 def replace(match):
  nonlocal counter
  attrs,content=match.groups()
  if 'table-figure' in attrs:return match.group(0)
  keys=[key for key in FIGURE_TITLES if (key in content if '.' in key else (f'id="{key}"' in attrs or (key=='hero' and 'class="hero"' in attrs)))]
  if len(keys)!=1:raise ValueError(f'Figure needs one unambiguous title: {keys}, {attrs}')
  counter+=1
  caption=re.search(r'<figcaption>(.*?)</figcaption>',content,flags=re.S)
  if not caption:raise ValueError(f'Figure {keys[0]} lacks a caption')
  title=html.escape(FIGURE_TITLES[keys[0]][0 if zh else 1])
  labelled=f'<figcaption id="figure-{counter}-title"><span class="figure-number">Figure {counter}.</span> <span class="figure-title">{title}.</span> {caption.group(1)}</figcaption>'
  content=content[:caption.start()]+labelled+content[caption.end():]
  if 'id=' not in attrs:attrs+=f' id="figure-{counter}"'
  else:content=f'<span id="figure-{counter}" class="figure-anchor"></span>'+content
  attrs+=f' data-figure-number="{counter}" aria-labelledby="figure-{counter}-title"'
  return '<figure'+attrs+'>'+content+'</figure>'
 page=re.sub(r'<figure\b([^>]*)>(.*?)</figure>',replace,page,flags=re.S)
 if counter!=len(FIGURE_TITLES):raise ValueError(f'Expected {len(FIGURE_TITLES)} numbered figures; got {counter}')
 return page
