#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evaluation.depth import depth_metrics
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); ap.add_argument("--out",required=True); a=ap.parse_args(); m=json.loads(Path(a.manifest).read_text())
    p=np.load(m["pred_depth_path"]); g=np.load(m["gt_depth_path"]); p=p[list(p.files)[0]] if isinstance(p,np.lib.npyio.NpzFile) else p; g=g[list(g.files)[0]] if isinstance(g,np.lib.npyio.NpzFile) else g
    out={"method_id":m["method_id"],"depth":depth_metrics(p,g)}; Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__": main()
