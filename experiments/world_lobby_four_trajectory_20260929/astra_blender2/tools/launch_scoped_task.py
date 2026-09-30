"""Launch a clean context with an explicit method-scoped task file."""
import argparse, json, subprocess, time
from pathlib import Path
RUN = Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--method', required=True, choices=['M1','M2','M3','M4'])
    p.add_argument('--name', required=True)
    p.add_argument('--prompt-file', required=True)
    p.add_argument('--work-dir')
    a=p.parse_args()
    prompt=Path(a.prompt_file).read_text()
    out=RUN/'provenance'
    cmd=['codex','exec','-m','gpt-6-astra','-c','model_reasoning_effort="medium"',
         '-c','approval_policy="never"','--sandbox','danger-full-access','--skip-git-repo-check',
         '--json','--color','never','-C',str(Path(a.work_dir).resolve() if a.work_dir else RUN/'models'/a.method),
         '-o',str(out/f'{a.name}_final.txt'),'-']
    (out/f'{a.name}_launch.json').write_text(json.dumps({'model':'gpt-6-astra',
        'fresh_context':True,'method':a.method,'prompt_file':str(Path(a.prompt_file).resolve()),
        'launched_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2)+'\n')
    with (out/f'{a.name}_events.jsonl').open('w') as log,(out/f'{a.name}_stderr.log').open('w') as err:
        result=subprocess.run(cmd,input=prompt,text=True,stdout=log,stderr=err)
    print(a.name,result.returncode)
    raise SystemExit(result.returncode)

if __name__=='__main__':
    main()
