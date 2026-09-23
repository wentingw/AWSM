#!/usr/bin/env python3
"""Evaluate one method manifest against GT without touching model assets."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from evaluation.pose import read_tum, pose_metrics

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    m=json.loads(Path(a.manifest).read_text()); pred=read_tum(m["pose_path"]); gt=read_tum(m["gt_pose_path"])
    out={"method_id":m["method_id"],"pose_path":m["pose_path"],"gt_pose_path":m["gt_pose_path"],"native_se3":pose_metrics(pred,gt,"se3"),"sim3_supplement":pose_metrics(pred,gt,"sim3")}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__": main()
