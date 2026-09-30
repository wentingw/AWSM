"""Snapshot current Space or publish an explicit metrics-only allowlist."""
import argparse,getpass,hashlib,json,shutil,time
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_download,snapshot_download
from huggingface_hub.utils import disable_progress_bars
RUN=Path(__file__).resolve().parents[1];REPO='Ooliva/world-lobby-exps-new'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','rebase','publish']);a=p.parse_args()
    token=getpass.getpass('HF credential: ');disable_progress_bars();api=HfApi(token=token)
    info=api.repo_info(REPO,repo_type='space');out=RUN/'report/space'
    if a.action in ['prepare','rebase']:
        if a.action=='prepare':assert not out.exists()
        else:
            previous=json.loads((RUN/'provenance/remote_before.json').read_text())
            if previous['revision']==info.sha:
                print(json.dumps(dict(status='BASELINE_CURRENT',revision=info.sha)));return
            out.rename(RUN/'report'/('staging_before_rebase_'+time.strftime('%H%M%S',time.gmtime())))
            shutil.copyfile(RUN/'provenance/remote_before.json',RUN/'provenance'/('remote_before_'+previous['revision']+'.json'))
        snap=Path(snapshot_download(REPO,repo_type='space',revision=info.sha,token=token,max_workers=4));shutil.copytree(snap,out)
        files={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (RUN/'provenance/remote_before.json').write_text(json.dumps(dict(revision=info.sha,private=info.private,files=files),indent=2)+'\n')
        shutil.copyfile(out/'index.html',RUN/'provenance/remote_before_index.html')
        print(json.dumps(dict(status='PREPARED',revision=info.sha,files=len(files))));return
    prior=json.loads((RUN/'provenance/remote_before.json').read_text());assert info.sha==prior['revision'],'Remote changed; rebase before publication'
    allowed=json.loads((RUN/'report/metrics_allowlist.json').read_text())
    assert all(n in ['index.html','release_verification.json','docs/plan_astra_blender2.md','docs/ASTRA_BLENDER2_METRICS.md'] or n.startswith('results/astra_blender2/') for n in allowed)
    assert not any(Path(n).suffix in ['.blend','.glb','.png','.jpg','.jpeg'] or 'models/' in n for n in allowed),'User authorized metrics only'
    qa=json.loads((RUN/'report/browser_qa.json').read_text());assert qa['status']=='PASS' and qa['index_sha256']==sha(out/'index.html')
    numeric=json.loads((RUN/'report/numeric_release_validation.json').read_text());assert numeric['status']=='PASS' and numeric['new_models_or_images_in_upload'] is False
    for name,h in prior['files'].items():
        if name.startswith(('models/','views/')):assert sha(out/name)==h,'Model/visual publication changed'
    commit=api.upload_folder(repo_id=REPO,repo_type='space',folder_path=str(out),allow_patterns=allowed,parent_commit=info.sha,commit_message='Update Tables 9–11 with new ten-check-view Astra Blender run; keep published models unchanged')
    after=api.repo_info(REPO,repo_type='space');assert after.private==info.private
    verified={}
    for name in allowed:
        remote=Path(hf_hub_download(REPO,name,repo_type='space',revision=after.sha,token=token));assert sha(remote)==sha(out/name);verified[name]=sha(remote)
    runtime=api.get_space_runtime(REPO)
    record=dict(status='COMPLETE',before_revision=info.sha,after_revision=after.sha,commit_url=str(commit.commit_url),verified_files=verified,models_not_uploaded=True,privacy_preserved=True,runtime_stage=str(runtime.stage),completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    (RUN/'provenance/hf_upload.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='verified_files'},indent=2))
if __name__=='__main__':main()
