import concurrent.futures,hashlib,json,urllib.request,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'runtime/visual_features/dinov2-small';out.mkdir(parents=True,exist_ok=True);chunks=out/'chunks';chunks.mkdir(exist_ok=True)
URL='https://huggingface.co/facebook/dinov2-small/resolve/main/model.safetensors';TOTAL=88249960;CHUNK=1024*1024

def fetch(i):
 start=i*CHUNK;end=min(TOTAL-1,start+CHUNK-1);p=chunks/f'{i:03d}'
 if p.exists() and p.stat().st_size==end-start+1:return i
 for attempt in range(4):
  try:
   r=urllib.request.urlopen(urllib.request.Request(URL+f'?download=true&part={i}',headers={'Range':f'bytes={start}-{end}'}),timeout=45)
   assert r.status==206 and r.headers.get('content-range')==f'bytes {start}-{end}/{TOTAL}',(i,r.status,r.headers.get('content-range'))
   b=r.read();assert len(b)==end-start+1;p.write_bytes(b);print('chunk',i,flush=True);return i
  except Exception as e:
   if attempt==3:raise
   print('retry',i,str(e),flush=True);time.sleep(1)
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:list(pool.map(fetch,range((TOTAL+CHUNK-1)//CHUNK)))
p=out/'model.safetensors'
with p.open('wb') as f:
 for i in range((TOTAL+CHUNK-1)//CHUNK):f.write((chunks/f'{i:03d}').read_bytes())
(out/'provenance.json').write_text(json.dumps({'source':URL,'bytes':TOTAL,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'download':'HTTP byte ranges, each range validated before concatenation'},indent=2)+'\n');print('COMPLETE',flush=True)
