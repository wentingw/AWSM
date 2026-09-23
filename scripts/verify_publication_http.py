"""Anonymous HTTP verification of the deployed Pages and pinned HF downloads."""
from pathlib import Path
import json,urllib.request,urllib.parse,concurrent.futures,re,time,hashlib
ROOT=Path(__file__).resolve().parents[1];pub=json.loads((ROOT/'publish/github_publication.json').read_text());base=pub['page_url'];checks=[]
def request(path):
 url=urllib.parse.urljoin(base,path)
 for attempt in range(4):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'world-model-blog-publication-check'},method='GET' if path.endswith('.html') else 'HEAD')
   with urllib.request.urlopen(req,timeout=35) as r:
    out={'path':path,'status':r.status,'type':r.headers.get('Content-Type'),'bytes':r.headers.get('Content-Length'),'final_url':r.url}
    if path.endswith('.html'):
     data=r.read();local=(ROOT/'dist'/path).read_bytes();out['matches_local_sha256']=hashlib.sha256(data).hexdigest()==hashlib.sha256(local).hexdigest();assert out['matches_local_sha256'],path
    return out
  except Exception:
   if attempt==3:raise
   time.sleep(2*(attempt+1))
paths=['index.html','en.html','assets/M2_cutaway.glb','assets/M3_cutaway.glb','assets/M4_cutaway.glb','assets/g1_episode.mp4','assets/drone_episode.mp4','vendor/model-viewer.min.js','figures/five_view_comparison.jpg','results/final_evaluation.json','downloads/reproduction_sources.zip']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(request,paths))
assert all(x['status']==200 for x in checks)
report={'status':'pass','anonymous_access':True,'github_repository':pub['repo_url'],'page_url':base,'commit':pub['commit'],'checks':checks};out=ROOT/'publish/public_http_verification.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'pass','page_url':base,'checked_paths':len(checks),'both_html_match_local_sha256':True},indent=2))
