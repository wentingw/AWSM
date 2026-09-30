"""Read only this run's method outputs and scoped task event logs."""
import json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for method in ['M1','M2','M3','M4']:
 d=R/'models'/method
 o={'method':method,'files':sum(p.is_file() for p in d.rglob('*')),'scene':(d/'scene.blend').exists(),'paired_rgb':len(list(d.glob('checks/v*/*_rgb.png'))),'paired_reports':len(list(d.glob('checks/v*/paired_report.json'))),'input_passes':len(list(d.glob('checks/input*/report.json')))}
 p=d/'modelling_manifest.json'
 if p.exists():
  try:
   m=json.loads(p.read_text());o.update(version=m.get('revisions'),state=m.get('status'))
  except json.JSONDecodeError:pass
 for phase in ['initial','initial_review','repair','final_review']:
  p=R/f'provenance/{method.lower()}_{phase}_events.jsonl'
  if p.exists():
   lines=p.read_text().splitlines();o[phase]={'events':len(lines),'last_event_age_s':round(time.time()-p.stat().st_mtime),'final':(p.parent/f'{method.lower()}_{phase}_final.txt').exists()}
 print(json.dumps(o))
