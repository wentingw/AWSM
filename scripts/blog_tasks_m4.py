"""Render the M4 task table only from the finalized, independently checked report."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'results/evaluation/tasks/m4_downstream_20260924/report.json'

def load_m4_tasks():
    data=json.loads(REPORT.read_text())
    if data.get('status')!='complete' or data.get('scene_method')!='M4':
        raise ValueError('M4 downstream section requires completed M4 experiments')
    for task in ('drone','g1'):
        if not data[task].get('episodes'):
            raise ValueError(f'Missing actual {task} episodes')
    return data

def m4_task_table(zh, table, table_heading):
    r=load_m4_tasks();d=r['drone']['counts'];g=r['g1']['counts']
    n=d['episodes'];ng=g['episodes']
    rows=[
        ['无人机' if zh else 'Drone',n,'无碰撞到达检索候选视点' if zh else 'Collision-free arrival at retrieved viewpoint',f"{d['collision_free_candidate_arrivals']} / {n}"],
        ['无人机' if zh else 'Drone',n,'严格复拍：≤0.10 m 且 ≤5°，无碰撞' if zh else 'Strict photo pose: ≤0.10 m and ≤5°, collision-free',f"{d['strict_rephotography_successes']} / {n}"],
        ['无人机' if zh else 'Drone',n,'宽松复拍：≤0.25 m 且 ≤10°，无碰撞' if zh else 'Relaxed photo pose: ≤0.25 m and ≤10°, collision-free',f"{d['relaxed_rephotography_successes']} / {n}"],
        ['宇树 G1' if zh else 'Unitree G1',ng,'正确目标、无碰撞到达、朝向与可见性均通过' if zh else 'Correct target, collision-free arrival, facing and visibility',f"{g['verified_target_successes']} / {ng}"],
    ]
    # Different task criteria are not ranked against one another. Only a perfect
    # success fraction reaches the shared theoretical maximum.
    for row in rows:
        successes,total=map(int,row[3].split('/'))
        if successes==total:row[3]='**'+row[3]+'**'
    note=('不同任务与判据不作横向排名；此表仅将达到满分的成功数加粗，试验数和阈值不参与排名。' if zh else 'Different tasks and criteria are not ranked against each other; bold here marks a perfect success count only. Episode counts and thresholds are not ranked.')
    return table_heading('m4_tasks')+'\n\n'+table(['任务' if zh else 'Task','试验数' if zh else 'Episodes','判定条件' if zh else 'Criterion','成功数' if zh else 'Successful'],rows)+'\n\n'+note


def m4_task_section(zh):
    report=load_m4_tasks()
    lang='zh' if zh else 'en'
    text=(ROOT/f'blog/templates/m4_tasks.{lang}.md').read_text()
    for key in ['DRONE_STEPS','DRONE_RESULTS','DRONE_LIMITATIONS','G1_PROTOCOL','G1_STEPS','G1_RESULTS','G1_LIMITATIONS','M4_TASK_EVIDENCE']:
        value=report['article'][lang][key]
        if not isinstance(value,str) or not value.strip():raise ValueError('Missing measured task narrative: '+key)
        text=text.replace('{{'+key+'}}',value)
    return text
