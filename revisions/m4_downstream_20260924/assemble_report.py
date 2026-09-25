"""Assemble measured M4 task results and bilingual editorial text."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];REV=Path(__file__).resolve().parent
OUT=ROOT/'results/evaluation/tasks/m4_downstream_20260924';OUT.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads((ROOT/p).read_text())
drone=load('results/evaluation/tasks/drone_M4_20260924/report.json')
g1=load('revisions/m4_downstream_20260924/independent_g1_check.json')
visibility=load('results/evaluation/tasks/g1_M4_20260924/visibility.json')
assert g1['status']=='pass' and visibility['status']=='complete' and len(visibility['episodes'])==20
assert visibility['evaluator_script_sha256']==hashlib.sha256((ROOT/'scripts/m4_g1_visibility_blender.py').read_bytes()).hexdigest()
vmap={v['episode_id']:v for v in visibility['episodes']}
for e in g1['episodes']:
 v=vmap[e['episode_id']];assert e['selected_target']==v['target_id']
 e['target_visible']=v['visible'];e['target_visible_fraction']=v['target_pixel_fraction']
 e['verified_target_success']=e['correct_identity'] and e['navigation_verified'] and e['target_visible']
g1['counts']['target_visible']=sum(e['target_visible'] for e in g1['episodes'])
g1['counts']['verified_target_successes']=sum(e['verified_target_success'] for e in g1['episodes'])
vn=g1['counts']['target_visible'];sn=g1['counts']['verified_target_successes'];fractions=[100*e['target_visible_fraction'] for e in g1['episodes']]
article={'zh':{
'DRONE_STEPS':'''1. **从图像检索候选位置。** 将 20 张参考照片与 30 个 M4 渲染视点编码为 DINOv2-small 特征，按 CLS 余弦相似度排序。候选视点按建图采样每六帧选取，检索只看图像。
2. **规划并飞行。** 在前五个候选中检查可达性，选择候选相机位置；MuJoCo 用四个有界推力执行器模拟 1 kg、六自由度四旋翼。机器人通过自身状态反馈跟随路径。
3. **拍摄并独立评分。** 在实际飞行终点渲染照片，与原参考图比较；随后才读取目标真值位姿，计算平移、旋转误差和复拍成功率。''',
'DRONE_RESULTS':'''**17/20 次无碰撞到达检索候选视点，3/20 次发生接触；严格与宽松复拍均为 0/20。** 严格条件为位置误差 ≤0.10 m、旋转误差 ≤5° 且无碰撞，宽松条件为 ≤0.25 m、≤10° 且无碰撞。20 次的平均误差为 **0.883 m / 8.26°**，终点 RGB 的平均 PSNR / SSIM 为 **10.65 dB / 0.300**。Query 9 的终点位姿很接近目标，但飞行中有接触，因此仍判为失败。''',
'DRONE_LIMITATIONS':'''视频展示 Query 13，图中沿用展示查询 0、3、13；完整统计包含所有 20 次。检索只提供离散的粗候选，本版没有连续图像反馈精调，并假设理想稳定云台。因此，到达检索结果并不等于找到精确拍摄位姿；这些结果也没有测量新场景泛化能力。''',
'G1_PROTOCOL':'''例如发布指令：**“找到浅灰色陶瓷盆中长着低矮绿植的花盆，走过去面对它。”** 另四条指令分别指定北侧／南侧金黄色花枝长方形花盆，以及北侧／南侧天堂鸟花盆；北侧明确定义为地图 +Y。共五个目标，每个从四个固定起点执行，合计 **20 次导航**，不是 20 个独立目标。''',
'G1_STEPS':'''1. **解析语言并选择实例。** 受限中文解析器提取类别、植物属性、盆体属性和方位，在 M4 生成的对象表中选择唯一匹配目标；有歧义时拒绝执行。控制器不读取评测器保存的目标答案。
2. **计算接近点与路径。** 根据目标包围盒生成候选接近位置，以 0.47 m 规划膨胀半径进行 A* 搜索。起点来自四个相隔至少 2 m、处于重建地板支撑区域的建图位置。
3. **行走、转向并停留。** 宇树官方 G1 12 自由度 CPU 行走策略控制 MuJoCo 关节动力学。接近点误差 <0.30 m、面向目标误差 <15° 并持续至少 1.5 s，且全程无障碍物接触、无跌倒，才计为导航成功。
4. **独立核验“找到”。** 将所选实例与独立目标标注比较，再从机器人末段实际记录状态上的固定虚拟相机投射射线。只有正确花盆作为第一命中表面、占画面至少 0.1%，才通过可见性检查。''',
'G1_RESULTS':f'''**20/20 次选择正确实例并完成无碰撞导航；{vn}/20 次通过目标可见性检查，合并成功率为 {sn}/20。** 记录轨迹的平均长度为 **7.31 m**，平均执行时间 **22.18 s**；末段接近点误差平均 **0.215 m**，目标朝向误差平均 **3.60°**。目标的采样可见面积占比为 {min(fractions):.2f}%–{max(fractions):.2f}%。下图展示五条指令各自第一个起点的结果，完整评测覆盖四个起点。''',
'G1_LIMITATIONS':'''这里实现的是**生成语义地图上的语言目标选择与导航**：对象属性来自 M4，语言解析器支持的是上述受限表达。它没有在线视觉物体识别；评测图中的目标轮廓来自几何射线标签。可见性计入场景遮挡，未建模机器人机身的自遮挡。虚拟相机固定安装在机体坐标 [0.08, 0, 0.35] m、下俯 20°，不根据目标答案转向。可见面积用 160×120 射线网格估计对应 640×480 画面；相机取最后一条完整记录状态，距停止时刻不超过 50 ms。视频回放已记录的关节状态，采用简化着色。''',
'M4_TASK_EVIDENCE':'''**适用范围。** 两个任务只验证这一重建场景内的能力。障碍物碰撞体采用保守包围盒，质量和摩擦等参数是仿真假设；没有在原始 GT 世界中重跑动力学，也没有部署真实机器人。旧 M3 实验仍保留在复现包中，不与本次不同协议的结果作受控优劣比较。

[合并逐次结果](../results/evaluation/tasks/m4_downstream_20260924/report.json) · [无人机指标](../results/evaluation/tasks/drone_M4_20260924/report.json) · [G1 遮挡与可见性](../results/evaluation/tasks/g1_M4_20260924/visibility.json) · [执行与复现步骤](../docs/M4_DOWNSTREAM_20260924.md) · [代码、指令和完整轨迹](../downloads/reproduction_sources.zip)'''
},'en':{
'DRONE_STEPS':'''1. **Retrieve candidate locations from images.** Encode the 20 reference photographs and 30 M4 renders using DINOv2-small, then rank CLS cosine similarity. Candidates come from every sixth mapping sample; retrieval uses images only.
2. **Plan and fly.** Check the top five candidates for reachability and select a map-camera position. MuJoCo simulates a 1 kg, six-degree-of-freedom quadrotor with four bounded thrust actuators, following the planned path using self-state feedback.
3. **Photograph and score independently.** Render the achieved flight endpoint and compare it with the reference. Only the post-execution evaluator reads the target camera pose to calculate position, orientation and rephotography outcomes.''',
'DRONE_RESULTS':'''**17/20 flights reach a retrieved candidate without collision; 3/20 have contacts. Strict and relaxed rephotography both score 0/20.** Strict success requires position error ≤0.10 m, rotation error ≤5° and no collision; relaxed thresholds are ≤0.25 m and ≤10°, also collision-free. Across all 20 queries, mean error is **0.883 m / 8.26°**, with endpoint RGB **PSNR 10.65 dB / SSIM 0.300**. Query 9 ends close to the reference pose but has contacts during flight, so it remains a failure.''',
'DRONE_LIMITATIONS':'''The video shows Query 13; the panel retains display queries 0, 3 and 13; aggregate results include all 20. Retrieval supplies discrete coarse candidates, with no continuous image-based pose refinement and an ideal stabilized gimbal. Reaching a retrieved view therefore does not imply recovering the precise photographic pose. This experiment does not measure generalization to unseen scenes.''',
'G1_PROTOCOL':'''An example instruction is **“Find the planter with low green foliage in a pale-grey ceramic pot, walk over, and face it.”** Four further Chinese instructions specify the north/south rectangular golden-flower planters and north/south bird-of-paradise planters. North explicitly means map +Y. Each of five target instances is executed from four fixed starts: **20 navigation executions**, not 20 independent targets.''',
'G1_STEPS':'''1. **Parse language and select an instance.** A constrained Chinese parser extracts category, plant/pot attributes and direction, and finds a unique match in M4's generated object inventory. Ambiguous requests are rejected. The controller never reads evaluator-only intended IDs.
2. **Plan an approach.** Generate approach candidates from the target bounds and run A* with a 0.47 m obstacle-inflation radius. The four starts are deterministic mapping locations at least 2 m apart on supported reconstructed floor.
3. **Walk, face and dwell.** Unitree's official G1 12DOF CPU locomotion policy drives articulated MuJoCo dynamics. Navigation requires approach error <0.30 m, target bearing <15° for at least 1.5 s, and no obstacle contacts or falls throughout execution.
4. **Verify finding the target independently.** Compare the selected instance with an independent intended label, then cast rays from a fixed virtual camera attached to the last recorded physical robot state. The correct planter must be the first visible surface in at least 0.1% of the image.''',
'G1_RESULTS':f'''**20/20 executions select the correct instance and complete collision-free navigation; {vn}/20 pass target visibility, for {sn}/20 combined successes.** Mean recorded path length is **7.31 m**, with **22.18 s** mean execution time. At the last recorded state, mean approach error is **0.215 m** and target-bearing error **3.60°**. Sampled target coverage ranges from {min(fractions):.2f}% to {max(fractions):.2f}%. The panel shows each instruction from its first start; the full evaluation includes all four starts.''',
'G1_LIMITATIONS':'''This is **language-goal selection and navigation over a generated semantic map**. Attributes come from M4, and the parser supports the stated constrained expressions. There is no online visual object recognition; evaluation outlines come from geometry-derived ray labels. Visibility includes scene occlusion but omits robot self-occlusion. The virtual camera has fixed body-relative translation [0.08, 0, 0.35] m and 20° downward pitch; it is never aimed using the target answer. Coverage is estimated with a 160×120 ray grid for a 640×480 image. The camera uses the last complete recorded state, no more than 50 ms before stopping. The video replays recorded joint states with simplified shading.''',
'M4_TASK_EVIDENCE':'''**Scope.** These tasks test only this reconstructed scene. Conservative bounding boxes represent obstacle collisions, and mass/friction are simulator assumptions. Neither original-GT-world dynamics transfer nor real-robot deployment is tested. Earlier M3 experiments remain in the reproduction archive; their different protocol prevents a controlled performance comparison with this revision.

[Combined episode results](../results/evaluation/tasks/m4_downstream_20260924/report.json) · [Drone metrics](../results/evaluation/tasks/drone_M4_20260924/report.json) · [G1 occlusion and visibility](../results/evaluation/tasks/g1_M4_20260924/visibility.json) · [Execution and reproduction](../docs/M4_DOWNSTREAM_20260924.md) · [Code, instructions and complete trajectories](../downloads/reproduction_sources.zip)'''
}}
report={'status':'complete','scene_method':'M4','scene_sha256':drone['source_hashes']['scene_blend'],'drone':drone,'g1':g1,'article':article,'verification_sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['revisions/m4_downstream_20260924/independent_drone_check.json','revisions/m4_downstream_20260924/independent_g1_check.json','results/evaluation/tasks/g1_M4_20260924/visibility.json']}}
report['endpoint_assets'] = [{'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for task in ['drone','g1'] for sub in (['endpoint_rgb'] if task=='drone' else ['endpoint_rgb','visibility_masks']) for p in sorted((ROOT/f'results/evaluation/tasks/{task}_M4_20260924'/sub).glob('*.png'))]
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'drone':drone['counts'],'g1':g1['counts']},indent=2))
