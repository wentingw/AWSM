"""Replace plan execution records with this run's measured outcomes."""
import json,re,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parent/'plan_astra_blender2.md'
def read(p):return json.loads(p.read_text())
def main():
    complete=read(R/'evaluation/COMPLETE.json');assert complete['status']=='COMPLETE'
    geo=read(R/'evaluation/blog_tables_456/tables_4_6.json');appearance=read(R/'evaluation/blog_tables_456/table5_appearance.json');regs=read(R/'evaluation/depth/registrations.json')
    original=(R/'provenance/plan_before_execution.md').read_text();plan=re.split(r'\n## 9\.',original,maxsplit=1)[0]
    plan=plan.replace('日期：2026-09-30。状态：待执行。','日期：2026-09-30。状态：本轮建模、独立审查、冻结和评测完成；仅发布 Table 9/10/11 指标。')
    rows=[];quality=[];account={}
    for m in ['M1','M2','M3','M4']:
        d=R/'models'/m;a=read(d/'modelling_manifest.json');rv=read(d/'independent_review/final_review.json')
        rows.append(f"| {m} | {a['revisions']} | {a['checking_render_count']} | {len(list(d.glob('checks/input*/report.json')))} | {rv['status']} |")
        quality.append(f"- {m}：最终质量与独立审查 `{rv['status']}`；场景 SHA256 `{complete['model_hashes'][m]}`。")
        logs=list((R/'provenance').glob(m.lower()+'*_events.jsonl'));usage=[];sessions=[];commands=0;errors=0
        for f in logs:
            events=[]
            for l in f.read_text().splitlines():
                try:events.append(json.loads(l))
                except json.JSONDecodeError:pass
            usage.extend([{'session_log':f.name,'usage':e.get('usage')} for e in events if e.get('type')=='turn.completed'])
            commands+=sum(e.get('type')=='item.started' and e.get('item',{}).get('type')=='command_execution' for e in events)
            errors+=sum(e.get('type') in ['error','turn.failed'] for e in events)
            launch=f.with_name(f.name.replace('_events.jsonl','_launch.json'));final=f.with_name(f.name.replace('_events.jsonl','_final.txt'))
            if launch.exists() and final.exists():
                started=read(launch).get('started_utc')
                if started:sessions.append({'session_log':f.name,'started_utc':started,'final_record_mtime_utc':datetime.fromtimestamp(final.stat().st_mtime,timezone.utc).isoformat(),'wall_seconds_to_final_record':final.stat().st_mtime-datetime.fromisoformat(started.replace('Z','+00:00')).timestamp(),'timing_source':'recorded launch UTC and final output file modification time'})
        account[m]={'observed_cli_usage':usage,'scope':'CLI records only; collaboration author usage unavailable' if m in ['M1','M2'] else 'Saved CLI sessions; retries/tool calls in JSONL','tool_command_events':commands,'error_events':errors,'session_timing':sessions}
    (R/'provenance/usage_accounting.json').write_text(json.dumps(account,indent=2)+'\n')
    metrics=[];g9={x['method']:x for x in geo['table4']['rows']};g11={x['method']:x for x in geo['table6']['rows']};g10={x['system']:x for x in appearance['rows']}
    for m in ['M1','M2','M3','M4']:
        if regs[m]['status']!='COMPLETE':metrics.append(f'| {m} | N/A | N/A | N/A | N/A | N/A | N/A | N/A |');continue
        metrics.append(f"| {m} | {g9[m]['model_to_gt']['mean_m']:.4f} | {g9[m]['observed_gt_to_model']['mean_m']:.4f} | {g10[m]['psnr_db_mean']:.4f} | {g10[m]['ssim_mean']:.4f} | {g10[m]['lpips_alex_v01_mean']:.4f} | {g11[m]['absrel']*100:.2f}% | {g11[m]['rmse_m']:.4f} |")
    record='''\n\n## 9. 本轮实际执行记录（覆盖旧执行记录）

本轮输出根目录为 `astra_blender2/`，保留上一轮 `astra_blender/`。
四组均使用新的 GPT-6 Astra 方法专属作者上下文，从本方法净化输入重新测量、语义建模；
独立初审与最终候选复审使用新的方法专属上下文。没有向作者提供 GT 评分。
输入实体复制，工具访问按方法限制并留记录；没有强制 OS 文件读取沙箱。

### 预算和审查

| 方法 | 完整版本 | 十视角配对检查累计 | 180帧输入BVH次数 | 最终独立复审 |
|---|---:|---:|---:|---|
'''+ '\n'.join(rows)+'''

固定检查样本33、61、74、82、91、100、108、118、129、155；每版保存RGB/模型深度，
M2–M4同时保存自身DA3深度、绝对/相对/有符号残差、有效域和边界对照。
M1仅有模型自身深度，不与DA3一致性混称。

'''+ '\n'.join(quality)+'''

### Table 9/10/11

Table9双向表面距离单位米；Table10固定评测视角0/36/72/108/144，PSNR/SSIM/LPIPS；
Table11为20个同轨迹确定性扰动相机的光轴Z深度误差。十视角用于建模修订，五视角用于既定冻结后外观评分。

| 方法 | Model→GT(m) | ObservedGT→model(m) | PSNR(dB) | SSIM | LPIPS | 扰动视角AbsRel | RMSE(m) |
|---|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(metrics)+'''

M1只在冻结RGB估计相机满足配准条件时进行GT相机辅助Sim(3)诊断，否则N/A；
M2/M3用180建模相机拟合一次SE(3)，scale1，M4按输入坐标关系。
GT来源是此前重新生成并验证的680视角GT。原目录已迁移，本轮使用HF快照中与原生成清单哈希完全一致的副本`astra_blender2/evaluation/gt_reference/`，来源及核验见`provenance/gt_reference_relocation.json`；
Table11扰动视角GT从原始USD本轮重新求交。没有使用旧legacy GT缓存。

### 本地交付和发布边界

- 新模型、脚本、参数、测量、配对图与审查：`astra_blender2/models/M1..M4/`。
- 全部冻结文件SHA256：各方法`freeze_manifest.json`与`SHA256SUMS`。
- 180/500模型深度：`astra_blender2/evaluation/depth/summary.json`。
- Table9/11：`astra_blender2/evaluation/blog_tables_456/tables_4_6.json`。
- Table10及逐视角CSV：同目录`table5_appearance.json`和CSV。
- 已观察到的CLI调用/token与工具统计：`astra_blender2/provenance/usage_accounting.json`；明确披露未获得的collaboration作者用量。
- HF本轮仅发布原Table9/10/11对应指标和相关数值/来源记录。发布前远端已重排为Table3/4/5，本轮保留最新编号并标注原表号。网页其他表格、三维模型、模型下载与渲染图仍属于此前轮次；没有上传新模型或新渲染图。
- HF完成提交与远端哈希验证记录：`astra_blender2/provenance/hf_upload.json`。

质量状态和未解决问题随结果保留。本轮为一次工程实验，不表述为重复建模方差或跨场景泛化。
'''
    P.write_text(plan+record);print('Wrote current execution record',P)
if __name__=='__main__':main()
