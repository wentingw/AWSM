"""Local Chromium CDP smoke/visual QA without reusing the user's profile."""
import sys,json,time,subprocess,urllib.request,base64,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'runtime/site_python'));import websocket
LIVE_BASE=sys.argv[sys.argv.index('--base-url')+1].rstrip('/')+'/' if '--base-url' in sys.argv else None
OUT=ROOT/('results/site_qa/live' if LIVE_BASE else 'results/site_qa');OUT.mkdir(parents=True,exist_ok=True)
def port():
 s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p
webport,debugport=port(),port();serve=ROOT/'dist' if '--dist' in sys.argv else ROOT;pageprefix='' if '--dist' in sys.argv else 'blog/'
log=(OUT/'browser.log').open('w');server=subprocess.Popen([sys.executable,'-m','http.server',str(webport),'--bind','127.0.0.1','--directory',str(serve)],stdout=log,stderr=log)
chrome=subprocess.Popen(['/usr/bin/google-chrome','--headless=new','--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',f'--remote-debugging-port={debugport}','--remote-allow-origins=*',f'--user-data-dir={ROOT}/runtime/browser_qa_profile','about:blank'],stdout=log,stderr=log)
try:
 for _ in range(100):
  try:tabs=json.load(urllib.request.urlopen(f'http://127.0.0.1:{debugport}/json'));break
  except Exception:time.sleep(.1)
 tab=next(t for t in tabs if t['type']=='page');ws=websocket.create_connection(tab['webSocketDebuggerUrl'],timeout=60);count=0;errors=[]
 def call(method,params={}):
  global count
  count+=1;ws.send(json.dumps({'id':count,'method':method,'params':params}))
  while True:
   r=json.loads(ws.recv())
   if r.get('method')=='Runtime.exceptionThrown':errors.append(r['params'])
   if r.get('id')==count:
    if 'error' in r:raise RuntimeError(r['error'])
    return r.get('result',{})
 def js(expression):
  r=call('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
  if 'exceptionDetails' in r:raise RuntimeError(r)
  return r.get('result',{}).get('value')
 def screenshot(name):
  d=call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False});(OUT/name).write_bytes(base64.b64decode(d['data']))
 call('Page.enable');call('Runtime.enable');reports=[]
 for lang in ['index','en']:
  for mobile in [False,True]:
   width,height=(390,844) if mobile else (1440,1000);call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':mobile});url=(LIVE_BASE+lang+'.html') if LIVE_BASE else f'http://127.0.0.1:{webport}/{pageprefix}{lang}.html';call('Page.navigate',{'url':url})
   for _ in range(100):
    if js('document.readyState')=='complete':break
    time.sleep(.1)
   time.sleep(.5);screenshot(f'{lang}_{"mobile" if mobile else "desktop"}_hero.png');info=js('({title:document.title,bodyWidth:document.body.scrollWidth,viewport:innerWidth,placeholders:document.body.innerText.includes("{{"),images:[...document.images].map(i=>({src:i.getAttribute("src"),complete:i.complete,width:i.naturalWidth,loading:i.loading})),videos:[...document.querySelectorAll("video")].map(v=>({src:v.querySelector("source")?.src,error:v.error?.code,readyState:v.readyState}))})');info.update(language=lang,mobile=mobile)
   js('document.querySelector("#compare").scrollIntoView({behavior:"instant",block:"start"})');js('document.querySelector("#compare-method").value="M4";document.querySelector("#compare-method").dispatchEvent(new Event("change"));document.querySelector("#compare-frame").value="108";document.querySelector("#compare-frame").dispatchEvent(new Event("change"));');
   for _ in range(150 if LIVE_BASE else 20):
    if js('document.querySelector("#compare-pred").complete && document.querySelector("#compare-pred").naturalWidth>0'):break
    time.sleep(.2)
   info['comparison']=js('({source:document.querySelector("#compare-pred").src,loaded:document.querySelector("#compare-pred").naturalWidth})');screenshot(f'{lang}_{"mobile" if mobile else "desktop"}_compare.png')
   if not mobile:
    js('document.querySelector("#scene-viewer").scrollIntoView({behavior:"instant",block:"center"})')
    for _ in range(1200 if LIVE_BASE else 160):
     if js('document.querySelector("#scene-viewer").loaded===true'):break
     time.sleep(.15)
    info['model_loaded']=js('document.querySelector("#scene-viewer").loaded===true');screenshot(f'{lang}_model.png');js('document.querySelector("#model-select").value="M4";document.querySelector("#model-select").dispatchEvent(new Event("change"));')
    for _ in range(600 if LIVE_BASE else 100):
     if js('document.querySelector("#scene-viewer").loaded===true'):break
     time.sleep(.1)
    info['model_switch_loaded']=js('document.querySelector("#scene-viewer").loaded===true')
   info['video_playback']=js('''(async()=>{const out=[];for(const v of document.querySelectorAll("video")){v.muted=true;await v.play();await new Promise(r=>setTimeout(r,350));out.push({time:v.currentTime,frames:v.webkitDecodedFrameCount,readyState:v.readyState});v.pause();}return out;})()''');reports.append(info);print('QA',lang,mobile,info['bodyWidth'],info.get('model_loaded'),flush=True)
 report={'scope':('live public URL' if LIVE_BASE else 'local')+' Chromium desktop/mobile, both languages, selectors, model and video playback','base_url':LIVE_BASE,'pages':reports,'javascript_exceptions':errors};(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 assert not errors,errors
 for r in reports:
  assert not r['placeholders'];assert r['bodyWidth']<=r['viewport']+1;assert r['comparison']['loaded']>0
  assert not any(v.get('error') for v in r['videos'])
  assert len(r['videos'])==2 and all(v['time']>0 and v['frames']>0 for v in r['video_playback'])
  if not r['mobile']:assert r['model_loaded'] and r['model_switch_loaded']
 print('BROWSER_QA_PASS',flush=True)
finally:
 chrome.terminate();server.terminate();chrome.wait(timeout=20);server.wait(timeout=10);log.close()
