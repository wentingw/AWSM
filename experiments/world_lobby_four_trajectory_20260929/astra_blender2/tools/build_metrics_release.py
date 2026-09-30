"""Metrics-only publication for new modelling run; retain all existing model assets."""
import csv,hashlib,json,re,shutil,zipfile
from pathlib import Path
from bs4 import BeautifulSoup
RUN=Path(__file__).resolve().parents[1];OUT=RUN/'report/space';EVAL=RUN/'evaluation/blog_tables_456'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def fmt(v,pct=False):return 'N/A' if v is None else f'{100*v:.2f}%' if pct else f'{v:.4f}'
def main():
    complete=read(RUN/'evaluation/COMPLETE.json');assert complete['status']=='COMPLETE'
    geometry=read(EVAL/'tables_4_6.json');appearance=read(EVAL/'table5_appearance.json');regs=read(RUN/'evaluation/depth/registrations.json')
    facts={}
    for method in ['M1','M2','M3','M4']:
        d=RUN/'models'/method;freeze=read(d/'freeze_manifest.json');manifest=read(d/'modelling_manifest.json');review=read(d/'independent_review/final_review.json')
        for n,h in freeze['files'].items():assert sha(d/n)==h
        facts[method]=dict(scene_sha256=sha(d/'scene.blend'),model_id=manifest['model_id'],revisions=manifest['revisions'],paired_checks=manifest['checking_render_count'],input_bvh_passes=len(list(d.glob('checks/input*/report.json'))),quality_status=review['status'],author_handoff_quality_status=manifest.get('quality_status'),final_review_status=review['status'],input_packet_sha256=sha(RUN/f'inputs/{method}/packet.json'),unresolved_issues=manifest['unresolved_issues'],issue_record_scope='Author handoff preserves pre-review wording; final independent disposition is authoritative',final_review_disposition=[{k:v for k,v in issue.items() if k in ['id','issue_id','initial_issue_id','status','severity','title','finding','summary','technical_protocol_blocker']} for issue in review.get('issues',[])])
    target=OUT/'results/astra_blender2';target.mkdir(parents=True,exist_ok=True)
    for name in ['tables_4_6.json','table5_appearance.json','table5_appearance_per_view.csv','table5_appearance_means.csv']:
        copy(EVAL/name,target/name)
    copy(RUN/'evaluation/depth/summary.json',target/'model_depth_180_500.json');copy(RUN/'evaluation/depth/registrations.json',target/'registrations.json')
    copy(RUN/'configs/run_contract.json',target/'run_contract.json');copy(RUN/'provenance/input_audit.json',target/'input_audit.json')
    copy(RUN/'provenance/gt_reference_relocation.json',target/'gt_reference_provenance.json')
    save(target/'model_provenance.json',dict(run='astra_blender2',frozen_models=facts,publication_scope='metrics only; published 3D models and images still belong to preceding run',check_indices=[33,61,74,82,91,100,108,118,129,155],files_unchanged=True))
    # Numeric arrays only: no new model meshes, source programs, render images or scene parameters.
    with zipfile.ZipFile(target/'numeric_evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(EVAL.glob('*.npz')):z.write(f,f.name)
        for m in facts:
            for split in ['modeling_180','eval_500']:
                p=RUN/f'evaluation/depth/{m}/{split}/per_frame.csv'
                if p.exists():z.write(p,f'{m}/{split}/per_frame.csv')
    g9={r['method']:r for r in geometry['table4']['rows']};g11={r['method']:r for r in geometry['table6']['rows']};g10={r['system']:r for r in appearance['rows']}
    for number,mapping,keys in [(9,g9,['model_to_gt','observed_gt_to_model']),(11,g11,['absrel','rmse_m','valid_coverage','missing_penalty_mae_m'])]:
        rows=[]
        for m in facts:
            row={'method':m,'status':regs[m]['status'],'model_sha256':facts[m]['scene_sha256']}
            for k in keys:
                v=mapping.get(m,{}).get(k);row[k+'_mean_m' if number==9 else k]=v['mean_m'] if number==9 and v else v
            rows.append(row)
        with (target/f'table{number}_means.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    doc=BeautifulSoup((RUN/'provenance/remote_before_index.html').read_text(),'html.parser')
    section=doc.find(id='reference-protocol-evaluation');assert section
    existing=section.find_all('table');assert len(existing)==3
    visible_numbers=[int(re.fullmatch(r'table(\d+)',t['id'])[1]) for t in existing]
    number_map=dict(zip([9,10,11],visible_numbers))
    save(target/'table_number_mapping.json',dict(requested_to_current=number_map,remote_baseline=read(RUN/'provenance/remote_before.json')['revision']))
    prior_note=f'原 Table 9/10/11 对应当前 Table {visible_numbers[0]}/{visible_numbers[1]}/{visible_numbers[2]}。' if visible_numbers!=[9,10,11] else ''
    section.clear()
    section.append(BeautifulSoup('<p class="eyebrow">NEW ASTRA BLENDER RUN / METRICS ONLY</p><p class="notice"><strong>本轮指标已更新，模型暂未发布：</strong>'+prior_note+'这三表使用按新版计划、固定 10 个检查视角重新建模并冻结的 M1–M4。页面其他表格、三维模型、模型下载和渲染图仍对应此前轮次，不代表本轮模型。本轮模型文件保存在本地。</p>','html.parser'))
    m1text='M1 无足够可靠的冻结 RGB 相机对应，按新计划标为不可评；未沿用历史人工 GT 配准。' if regs['M1']['status']!='COMPLETE' else 'M1 使用冻结 RGB 估计相机拟合一次 GT 相机辅助 Sim(3)，仅作形状诊断；M2–M4 主结果 scale=1。'
    p=doc.new_tag('p');p.string=m1text;section.append(p)
    p=doc.new_tag('p');p.string='四组最终独立复审均为 LIMITED：技术与协议阻塞项已关闭，仍有布局、轮廓、材质或物理近似的质量限制。场景哈希、版本预算与遗留问题见下方来源记录。';section.append(p)
    definitions=[(9,'双向表面距离','模型表面按三角形面积采样 100,000 点；可观测 GT 从新生成的 180 帧有效射线命中中均匀采样 100,000 点，按观测频次加权。两方向均使用 BVH 最近三角面距离，单位米。',['Model → GT mean (m) ↓','Observed GT → model mean (m) ↓']),
        (10,'五个建模视角外观一致性','冻结后使用既定评测视角 0/36/72/108/144，统一 GT 相机渲染 640×480，CPU Cycles 16 samples。GT RGB 用 Lanczos 缩小；全图 PSNR、SSIM、LPIPS AlexNet v0.1，不裁剪、不遮罩、不拟合颜色或曝光。这五个评测视角与每版修订使用的十个检查视角不同。',['PSNR (dB) ↑','SSIM ↑','LPIPS ↓']),
        (11,'同轨迹扰动新视角深度','冻结后在同一轨迹上生成 20 个确定性扰动相机，每视角随机固定 5,000 像素；原始 GT 网格与冻结模型均使用 optical-Z 射线深度。GT 有效域 0.1–30 m，固定域覆盖率，缺失预测记 30 m 惩罚。不是跨场景泛化。',['AbsRel ↓','RMSE (m) ↓','Coverage ↑','Penalized MAE (m) ↓'])]
    for number,title,description,headers in definitions:
        visible=number_map[number]
        historical=f'（原 Table {number}）' if visible!=number else ''
        heading=doc.new_tag('h2');heading.string=f'Table {visible}. 新版 Astra/Blender：{title}{historical}';section.append(heading)
        p=doc.new_tag('p');p.string=description;section.append(p)
        wrapper=doc.new_tag('div',attrs={'class':'scroll'});table=doc.new_tag('table',id=f'table{visible}');caption=doc.new_tag('caption');caption.string=f'Table {visible}. {title}（本轮冻结模型）';table.append(caption)
        head=doc.new_tag('thead');tr=doc.new_tag('tr')
        for h in ['方法']+headers:
            th=doc.new_tag('th');th.string=h;tr.append(th)
        head.append(tr);table.append(head);body=doc.new_tag('tbody')
        for m in facts:
            tr=doc.new_tag('tr');th=doc.new_tag('th');th.string=m+(' · GT 相机辅助 Sim(3) 诊断' if m=='M1' and regs[m]['status']=='COMPLETE' else '');tr.append(th)
            if regs[m]['status']!='COMPLETE':values=['N/A']*len(headers)
            elif number==9:values=[fmt(g9[m][k]['mean_m']) for k in ['model_to_gt','observed_gt_to_model']]
            elif number==10:values=[fmt(g10[m][k]) for k in ['psnr_db_mean','ssim_mean','lpips_alex_v01_mean']]
            else:values=[fmt(g11[m][k],k in ['absrel','valid_coverage']) for k in ['absrel','rmse_m','valid_coverage','missing_penalty_mae_m']]
            for val in values:td=doc.new_tag('td');td.string=val;tr.append(td)
            body.append(tr)
        table.append(body);wrapper.append(table);section.append(wrapper)
    section.append(BeautifulSoup('<p><a href="results/astra_blender2/tables_4_6.json">原 Table 9/11 完整指标</a> · <a href="results/astra_blender2/table9_means.csv">原 Table 9 CSV</a> · <a href="results/astra_blender2/table11_means.csv">原 Table 11 CSV</a> · <a href="results/astra_blender2/table5_appearance.json">原 Table 10 完整指标</a> · <a href="results/astra_blender2/table5_appearance_per_view.csv">原 Table 10 逐视角 CSV</a> · <a href="results/astra_blender2/model_depth_180_500.json">180/500 模型深度评测</a> · <a href="results/astra_blender2/numeric_evidence.zip">数值证据 ZIP</a> · <a href="results/astra_blender2/model_provenance.json">模型哈希与预算记录</a> · <a href="docs/ASTRA_BLENDER2_METRICS.md">口径与限制</a> · <a href="docs/plan_astra_blender2.md">新版计划与本轮记录</a></p>','html.parser'))
    (OUT/'index.html').write_text(str(doc))
    notes='# 新版 Astra/Blender：先发布指标\n\n本轮 Table 9/10/11 采用 astra_blender2 的新冻结模型。网页三维模型、模型下载与渲染图仍为上一轮。\n\n每版固定检查样本33、61、74、82、91、100、108、118、129、155；全量180帧输入深度检查每个几何方法三次。输入一致性只衡量与自身DA3预测的一致性，GT评分发生于全部冻结之后，没有反馈修模。\n\n'+m1text+'\n\nTable9：模型表面面积均匀采样100000点(seed20260923)；从180帧GT有效射线均匀选100000个命中点(seed20260925)，观测频次加权；精确最近三角面距离。\n\nTable10：沿用既定五评测视角，完整图像PSNR/SSIM/LPIPS，无配色曝光拟合。Table11：20个同轨迹确定性扰动相机、每视角5000条固定随机射线(seed23)，光轴Z米制深度。\n\nM2/M3只用180建模相机拟合一次SE(3)，scale1；M4使用记录的输入坐标关系。相机与评测采样记录在JSON中。\n\n输入采用物理副本和方法专属新上下文，工具路径有记录；没有强制操作系统文件读取沙箱。每组独立初审和最终复审，有限质量与未解决项见模型来源JSON。一次工程实验，非重复建模方差或跨场景泛化。\n'
    notes=notes.replace('本轮 Table 9/10/11 采用',prior_note+' 本轮这三张表采用')
    (OUT/'docs/ASTRA_BLENDER2_METRICS.md').write_text(notes)
    copy(RUN.parent/'plan_astra_blender2.md',OUT/'docs/plan_astra_blender2.md')
    baseline=read(RUN/'provenance/remote_before.json')
    for n,h in baseline['files'].items():
        if n.startswith(('models/','views/')):assert sha(OUT/n)==h
    before=BeautifulSoup((RUN/'provenance/remote_before_index.html').read_text(),'html.parser')
    before.find(id='reference-protocol-evaluation').extract()
    outside=BeautifulSoup(str(doc),'html.parser');outside.find(id='reference-protocol-evaluation').extract()
    assert str(before)==str(outside),'Page content outside targeted metric section changed'
    missing=[]
    for a in doc.find_all(['a','img','script','link','model-viewer']):
        link=a.get('href') or a.get('src') or ''
        if link and not link.startswith(('http:','https:','data:','#')) and not (OUT/link.split('#')[0]).exists():missing.append(link)
    assert not missing,missing
    for p in target.rglob('*'):
        if p.is_file() and p.suffix in ['.json','.csv','.md']:assert not re.search(r'hf_[A-Za-z0-9]{20,}',p.read_text())
    verification=read(OUT/'release_verification.json');verification.update(status='PASS',metrics_only_new_run='astra_blender2',published_models_unchanged=True,missing_links=missing)
    verification['files']={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='release_verification.json'};save(OUT/'release_verification.json',verification)
    changed=[str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file() and sha(p)!=baseline['files'].get(str(p.relative_to(OUT)))];save(RUN/'report/metrics_allowlist.json',changed)
    print(json.dumps(dict(status='PASS',changed_files=changed,frozen_models=facts),indent=2))
if __name__=='__main__':main()
