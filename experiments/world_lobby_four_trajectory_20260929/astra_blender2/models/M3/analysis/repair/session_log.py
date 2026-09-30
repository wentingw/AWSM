import json,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def record(kind,paths,detail):
 p=R/'input_access_log.json';a=json.loads(p.read_text());a.setdefault('revision_author_records',[]).append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':kind,'paths':[str(x) for x in paths],'detail':detail});p.write_text(json.dumps(a,indent=2)+'\n')
if __name__=='__main__':
 record('session_start_and_reads',[R,R.parents[1]/'inputs/M3',R.parents[1]/'configs/modelling_contract.md'],'Fresh revision author; no subagents. Initial commands: cat contract; pwd and rg --files scoped to M3; batched cat/sed reads of initial_review.md/json, HANDOFF_V1.md, manifest, layout, build_scene.py, measurements, paired_region_residuals_v1, input_access_log, iteration_log, input_pass_observations_v1, camera_checks, analysis/access_log.py, coordinator_invocation.json/log and packet schema. Output from initial batches was truncated; subsequently using focused reads. No root provenance logs or other contexts accessed. Runtime binaries/packages allowed as generic dependencies. Writes restricted to models/M3.')
