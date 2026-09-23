#!/usr/bin/env python3
"""Build frozen evaluation summary and publication figures without rerunning experiments."""
from pathlib import Path
import csv, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
VIEWS = [0, 36, 72, 108, 144]
SYSTEMS = ["M1","M2","M3","M4","B1","B2"]
GEOM_DIR = {"M1":"M1_observed_eval","M2":"M2","M3":"M3","M4":"M4","B1":"B1","B2":"B2","B2p":"B2p"}
POSE_LABEL = {"M1":"no native pose (RGB-only Astra model)",
              "M2":"ViPE estimated",
              "M3":"OpenVINS estimated",
              "M4":"GT pose input (oracle)",
              "B1":"ViPE direct baseline",
              "B2":"calibrated RGB-only (known intrinsics)"}

def load(p):
    p = ROOT / p
    return json.loads(p.read_text()) if p.exists() else None

def pick(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d: return d[k]
    return None

def summary_depth(method, kind):
    d = load(f"results/evaluation/depth/{method}_{kind}/{'depth_metrics.json' if kind=='native' else 'model_depth_metrics.json'}")
    if not d: return {}
    def block(name):
        x=d.get(name,{})
        return {"valid_coverage":x.get("valid_coverage"),"invalid_rate":x.get("invalid_rate"),
          "absrel":x.get("absrel"),"rmse_m":x.get("rmse_m"),"delta1":x.get("delta1"),
          "pixels_domain":x.get("pixels_domain"),"pixels_valid":x.get("pixels_valid"),
          "missing_penalty_mae_m":x.get("missing_penalty_mae_m")}
    out={"all180":block("all180"),"common175":block("common175"),
         "scale_fit":d.get("scale_fit"),"alignment":d.get("alignment"),
         "kind":d.get("kind",d.get("scope"))}
    # retain all180 aliases for compact CSV compatibility
    out.update(out["all180"])
    return out

def summary_pose(method, report):
    for row in report.get("methods", []):
        if row.get("method_id") != method: continue
        x = row.get("native_se3") or {}
        t, r = x.get("translation_m",{}), x.get("rotation_deg",{})
        return {"pose_count":row.get("pose_count"), "frame_coverage":row.get("frame_coverage"),
                "translation_rmse_m":t.get("rmse"), "translation_mean_m":t.get("mean"),
                "rotation_rmse_deg":r.get("rmse"), "rotation_mean_deg":r.get("mean"),
                "rpe10_translation_rmse_m":x.get("rpe",{}).get("10.0",{}).get("translation_m",{}).get("rmse"),
                "rpe10_rotation_rmse_deg":x.get("rpe",{}).get("10.0",{}).get("rotation_deg",{}).get("rmse"),
                "pose_alignment":x.get("align"), "pose_label":POSE_LABEL.get(method)}
    return {"pose_label":POSE_LABEL.get(method)}

def summary_geometry(method):
    d = load(f"results/evaluation/geometry/{GEOM_DIR[method]}/surface_metrics.json")
    if not d: return {}
    def vals(x):
        return {f"{x}_mean_m":d.get(x,{}).get("mean_m"),
                f"{x}_median_m":d.get(x,{}).get("median_m"),
                f"{x}_p90_m":d.get(x,{}).get("p90_m"),
                f"{x}_coverage_10cm":d.get(x,{}).get("threshold_coverage",{}).get("0.1")}
    out = {"samples_each":d.get("samples_each"), "alignment":d.get("alignment"),
           "model_triangles":d.get("model_triangles"), "gt_triangles":d.get("gt_triangles")}
    out.update(vals("model_to_gt")); out.update(vals("gt_to_model"))
    out["symmetric_chamfer_mean_m"] = d.get("symmetric_chamfer_mean_m")
    if d.get("observed_gt_to_model"): out.update(vals("observed_gt_to_model"))
    return out

def make_contact():
    out=ROOT/"figures"; out.mkdir(exist_ok=True)
    gtroot=ROOT/"data/world_lobby/rgb_180"
    cols=["M1","M2","M3","GT"]; tiles=[]
    for idx in VIEWS:
        row=[]
        gt=Image.open(next(gtroot.glob(f"{idx:06d}_*.png"))).convert("RGB")
        for m in cols:
            if m=="GT": im=gt
            else: im=Image.open(ROOT/f"results/{m}/renders/{idx:03d}.png").convert("RGB")
            row.append(im.resize((320,240)))
        tiles.append(row)
    canvas=Image.new("RGB",(4*320+90,5*240+60),(245,245,245))
    d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",24)
    for x,name in enumerate(cols):
        d.text((90+x*320+110,8),name,fill="black",font=font)
    for y,row in enumerate(tiles):
        d.text((8,60+y*240+108),str(VIEWS[y]),fill="black",font=font)
        for x,im in enumerate(row):
            canvas.paste(im,(90+x*320,60+y*240))
    canvas.save(out/"five_view_comparison.jpg",quality=95)
    canvas.save(out/"five_view_comparison.png")
    # M4 supplement
    sup=Image.new("RGB",(5*320,240))
    for x,idx in enumerate(VIEWS):
        sup.paste(Image.open(ROOT/f"results/M4/renders/{idx:03d}.png").convert("RGB").resize((320,240)),(x*320,0))
    sup.save(out/"m4_pose_oracle_supplement.jpg",quality=95)

def rgb_metrics():
    from skimage.metrics import structural_similarity
    gtroot=ROOT/"data/world_lobby/rgb_180"; records=[]
    for m in SYSTEMS+["B2p"]:
        vals=[]
        for idx in VIEWS:
            gt=Image.open(next(gtroot.glob(f"{idx:06d}_*.png"))).convert("RGB")
            pred=Image.open(ROOT/f"results/{m}/renders/{idx:03d}.png").convert("RGB")
            assert pred.size == (640,480)
            a=np.asarray(pred,dtype=np.float32)/255.0
            b=np.asarray(gt.resize((640,480),Image.Resampling.LANCZOS),dtype=np.float32)/255.0
            mse=float(np.mean((a-b)**2)); psnr=float("inf") if mse==0 else float(-10*np.log10(mse))
            ss=float(structural_similarity(a,b,channel_axis=2,data_range=1.0))
            records.append({"system":m,"keyframe_index":idx,"psnr_db":psnr,"ssim":ss,"pred_path":str(ROOT/f"results/{m}/renders/{idx:03d}.png"),"gt_path":str(next(gtroot.glob(f"{idx:06d}_*.png")))})
    (ROOT/"results/rgb_metrics_five_views.json").write_text(json.dumps({"domain":"same input views; 640x480; GT downsample Lanczos; skimage window7 SSIM channel mean; no color fitting","rows":records},indent=2)+"\n")
    with (ROOT/"results/rgb_metrics_five_views.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["system","keyframe_index","psnr_db","ssim","pred_path","gt_path"]); w.writeheader(); w.writerows(records)
    means=[]
    for m in SYSTEMS+["B2p"]:
        q=[r for r in records if r["system"]==m]
        means.append({"system":m,"psnr_db_mean":float(np.mean([r["psnr_db"] for r in q])),"ssim_mean":float(np.mean([r["ssim"] for r in q]))})
    (ROOT/"results/rgb_metrics_five_views_mean.json").write_text(json.dumps({"rows":means},indent=2)+"\n")
    return {"per_frame":records,"mean":means}

def render_metrics():
    out=[]
    rgb=rgb_metrics()
    report=load("results/evaluation/pose/current/report.json") or {}
    for m in SYSTEMS:
        fm={"B1":"M2","B2p":"M3"}.get(m,m)
        row={"system":m, "shared_frontend":({"B1":"M2","B2p":"M3"}.get(m)), "pose":summary_pose(fm,report),
             "native_depth":summary_depth(fm,"native"),
             "model_depth":summary_depth(m,"model"),
             "geometry":summary_geometry(m), "rgb": {"mean": next((x for x in rgb["mean"] if x["system"]==m),None), "per_frame":[x for x in rgb["per_frame"] if x["system"]==m]}}
        out.append(row)
    (ROOT/"results/final_evaluation.json").write_text(json.dumps({
      "schema":"world_model_blog.final_evaluation.v1",
      "views":VIEWS,"systems":SYSTEMS,"supplementary":["B2p"],
      "definitions":{"pose":"native SE(3) alignment; M1 has no native trajectory and uses GT-assisted Sim3 for shape/display only; M4 GT input",
        "depth":"all180 and common175 fixed valid GT optical-Z masks; native frontend and rendered model separate; missing penalties retained",
        "geometry":"single supplied global transform; no ICP; observed coverage separate", "frontend_sharing":{"B1":"M2 (ViPE frontend)", "B2p":"M3 (OpenVINS+MapAnything frontend)"}, "rgb":"same input views; pixel metrics after resize only; no color fitting"},
      "rows":out,
      "supplementary_rows":{"B2p":{"shared_frontend":"M3","pose":summary_pose("M3",report),"native_depth":summary_depth("M3","native"),
        "model_depth":summary_depth("B2p","model"),"geometry":summary_geometry("B2p")}}
    },indent=2)+"\n")
    fields=["system","pose_count","frame_coverage","translation_rmse_m","rotation_rmse_deg","rpe10_translation_rmse_m",
            "shared_frontend","native_all180_absrel","native_common175_absrel","native_all180_coverage","native_common175_coverage","native_all180_missing_penalty_mae_m","native_common175_missing_penalty_mae_m","native_absrel","native_rmse_m","native_delta1","native_valid_coverage","model_absrel","model_rmse_m",
            "model_delta1","model_valid_coverage","geometry_model_to_gt_mean_m","geometry_observed_gt_to_model_mean_m",
            "geometry_symmetric_chamfer_mean_m"]
    with (ROOT/"results/final_evaluation.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in out:
            p=r["pose"]; n=r["native_depth"]; md=r["model_depth"]; g=r["geometry"]
            w.writerow({"system":r["system"],"pose_count":p.get("pose_count"),"frame_coverage":p.get("frame_coverage"),
              "translation_rmse_m":p.get("translation_rmse_m"),"rotation_rmse_deg":p.get("rotation_rmse_deg"),
              "rpe10_translation_rmse_m":p.get("rpe10_translation_rmse_m"),
              "shared_frontend":r.get("shared_frontend"),"native_all180_absrel":n.get("all180",{}).get("absrel"),"native_common175_absrel":n.get("common175",{}).get("absrel"),"native_all180_coverage":n.get("all180",{}).get("valid_coverage"),"native_common175_coverage":n.get("common175",{}).get("valid_coverage"),"native_all180_missing_penalty_mae_m":n.get("all180",{}).get("missing_penalty_mae_m"),"native_common175_missing_penalty_mae_m":n.get("common175",{}).get("missing_penalty_mae_m"),"native_absrel":n.get("absrel"),"native_rmse_m":n.get("rmse_m"),"native_delta1":n.get("delta1"),
              "native_valid_coverage":n.get("valid_coverage"),"model_absrel":md.get("absrel"),
              "model_rmse_m":md.get("rmse_m"),"model_delta1":md.get("delta1"),"model_valid_coverage":md.get("valid_coverage"),
              "geometry_model_to_gt_mean_m":g.get("model_to_gt_mean_m"),
              "geometry_observed_gt_to_model_mean_m":g.get("observed_gt_to_model_mean_m"),
              "geometry_symmetric_chamfer_mean_m":g.get("symmetric_chamfer_mean_m")})
    return out

def load_npz(p):
    try: return np.load(p)
    except: return None

def make_plots(rows):
    out=ROOT/"figures"; methods=[r["system"] for r in rows]
    # Per-frame model depth error curves for five fixed views.
    fig,ax=plt.subplots(figsize=(10,5))
    for r in rows:
        d=load(f"results/evaluation/depth/{r['system']}_model/model_depth_metrics.json")
        if not d: continue
        vals={x.get("keyframe_index"):x.get("absrel") for x in d.get("per_frame",[])}
        y=[vals.get(i,np.nan) for i in VIEWS]
        ax.plot(VIEWS,y,"o-",label=r["system"])
    ax.set(xlabel="keyframe index",ylabel="model depth AbsRel",title="Rendered model depth error at fixed views")
    ax.grid(alpha=.25); ax.legend(ncol=3); fig.tight_layout(); fig.savefig(out/"model_depth_error_five_views.png",dpi=180); plt.close(fig)
    # Each row is a fixed input view; every panel shares the same color scale.
    gt=np.load(ROOT/"results/ground_truth/gt_depth_mapping_180.npz")
    truth=gt["truth_z_m"]; methods=["M1","M2","M3","M4","B1","B2"]
    fig,axs=plt.subplots(5,6,figsize=(16,11),layout="constrained")
    cmap=plt.get_cmap("magma").copy();cmap.set_bad("#90d5cf")
    for j,m in enumerate(methods):
        pred=np.load(ROOT/f"results/evaluation/depth/{m}_model/model_depth_samples.npz")["predicted_z_m"]
        for i,k in enumerate(VIEWS):
            valid=np.isfinite(pred[k])&(pred[k]>=.1)&(pred[k]<=30)&np.isfinite(truth[k])&(truth[k]>=.1)&(truth[k]<=30)
            err=np.full(19200,np.nan);err[valid]=np.abs(pred[k,valid]-truth[k,valid])/truth[k,valid]
            q=axs[i,j].imshow(err.reshape(120,160),vmin=0,vmax=1,cmap=cmap,interpolation="nearest")
            axs[i,j].set_xticks([]);axs[i,j].set_yticks([])
            if i==0:axs[i,j].set_title(m,fontsize=14)
            if j==0:axs[i,j].set_ylabel(f"Frame {k}",fontsize=12)
    fig.colorbar(q,ax=axs.ravel().tolist(),shrink=.65,label="|predicted Z - GT Z| / GT Z; clipped at 1.0")
    fig.suptitle("Model depth error at fixed GT cameras · teal = missing/invalid prediction",fontsize=15)
    fig.savefig(out/"model_depth_error_pixel_heatmap.png",dpi=160);plt.close(fig)
    # observed geometry means
    fig,ax=plt.subplots(figsize=(9,5)); ys=[]
    for r in rows:
        x=r["geometry"].get("observed_gt_to_model_mean_m",np.nan); ys.append(x)
    ax.bar(methods,ys,color=["#526b54" if m.startswith("M") else "#9b7b49" for m in methods])
    ax.set(ylabel="observed GT → model mean distance (m)",title="Observed-region geometry error")
    ax.grid(axis="y",alpha=.25); fig.tight_layout(); fig.savefig(out/"observed_geometry_error.png",dpi=180); plt.close(fig)

if __name__=="__main__":
    make_contact(); rows=render_metrics(); make_plots(rows)
    print("wrote final_evaluation.json/.csv and figures")
