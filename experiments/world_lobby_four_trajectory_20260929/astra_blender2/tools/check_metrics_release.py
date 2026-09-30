"""Browser checks for metrics-only delta; verify model/download assets unchanged."""
import functools,hashlib,http.server,json,threading
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
RUN=Path(__file__).resolve().parents[1];ROOT=RUN/'report/space'
def main():
    baseline=json.loads((RUN/'provenance/remote_before.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for n,h in baseline['files'].items():
        if n.startswith(('models/','views/')):assert sha(ROOT/n)==h
    errors=[];bad=[];views=[]
    number_map=json.loads((ROOT/'results/astra_blender2/table_number_mapping.json').read_text())['requested_to_current']
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/__baseline':
                data=(RUN/'provenance/remote_before_index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
            else:super().do_GET()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
            page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
            page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle',timeout=60000)
            baseline_page=browser.new_page(viewport={'width':1440,'height':1000});baseline_page.goto(f'http://127.0.0.1:{server.server_port}/__baseline',wait_until='networkidle',timeout=60000)
            for width,height in [(1440,1000),(390,844)]:
                page.set_viewport_size({'width':width,'height':height});page.locator('#reference-protocol-evaluation').scroll_into_view_if_needed()
                baseline_page.set_viewport_size({'width':width,'height':height})
                for n in number_map.values():assert page.locator(f'#table{n} tbody tr').count()==4
                page.screenshot(path=str(RUN/f'report/metrics_{width}.png'))
                actual=page.evaluate('document.documentElement.scrollWidth');prior=baseline_page.evaluate('document.documentElement.scrollWidth')
                section_fits=page.locator('#reference-protocol-evaluation').evaluate('(e)=>e.getBoundingClientRect().right<=innerWidth+1')
                views.append({'width':width,'overflow':actual>width,'page_scroll_width':actual,'baseline_scroll_width':prior,'no_added_page_overflow':actual<=max(width,prior)+1,'metric_section_fits_viewport':section_fits})
            page.set_viewport_size({'width':1440,'height':1000});page.locator('#reference-protocol-evaluation').screenshot(path=str(RUN/'report/tables_9_10_11.png'))
            text=page.locator('#reference-protocol-evaluation').inner_text();assert '本轮指标已更新，模型暂未发布' in text
            browser.close()
        result={'status':'PASS' if not errors and not bad and all(x['no_added_page_overflow'] and x['metric_section_fits_viewport'] for x in views) else 'FAIL','scope':'metrics section and no page regression; existing mobile page overflow recorded rather than concealed','views':views,'javascript_errors':errors,'http_errors':bad,'existing_models_and_visuals_unchanged':True,'index_sha256':sha(ROOT/'index.html')}
        (RUN/'report/browser_qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['status']=='PASS'
    finally:server.shutdown()
if __name__=='__main__':main()
