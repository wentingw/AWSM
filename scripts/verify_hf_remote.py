"""Anonymous verification of the publicly uploaded immutable model artifacts."""
import json,hashlib,urllib.request
from pathlib import Path
from huggingface_hub import HfApi
ROOT=Path(__file__).resolve().parents[1];pub=json.loads((ROOT/'publish/huggingface_publication.json').read_text());api=HfApi(token=False);info=api.repo_info(pub['repo_id'],repo_type='dataset',revision=pub['commit'],files_metadata=True);assert not info.private;remote={x.rfilename:x for x in info.siblings};checks=[]
for x in json.loads((ROOT/'publish/model_asset_manifest.json').read_text()):
 name='models/'+x['destination'];r=remote[name];lf=r.lfs;actual=lf.get('sha256') if isinstance(lf,dict) else lf.sha256;assert actual==x['sha256'],name;assert r.size==x['bytes'];checks.append({'path':name,'sha256_verified':True,'bytes':r.size})
url=pub['url']+'/resolve/'+pub['commit']+'/payload_manifest.json';data=urllib.request.urlopen(url,timeout=40).read();assert hashlib.sha256(data).hexdigest()==pub['payload_manifest_sha256'];manifest=json.loads(data)
for x in manifest['entries']:
 assert x['path'] in remote,x['path'];assert remote[x['path']].size==x['bytes'],x['path']
report={'status':'pass','anonymous_public_access':True,'repo':pub['repo_id'],'revision':pub['commit'],'remote_files':len(remote),'verified_manifest_entries':len(manifest['entries']),'eight_original_models':checks,'payload_manifest_sha256':hashlib.sha256(data).hexdigest()};(ROOT/'publish/hf_remote_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='eight_original_models'},indent=2))
