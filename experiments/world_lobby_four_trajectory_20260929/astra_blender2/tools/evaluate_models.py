"""Evaluate only after all four models are frozen; no GT feedback to authors."""
import argparse,csv,hashlib,itertools,json,subprocess,sys,time
from pathlib import Path
import numpy as np
from depth_math import metrics
RUN=Path(__file__).resolve().parents[1];BASE=RUN.parent
BLENDER='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender'
sys.path.insert(0,str(BASE/'code'))
from depth_pipeline import pose_lookup

KEYS=['valid_coverage','invalid_rate','mae_m','rmse_m','absrel','delta1','delta2','delta3','missing_penalty_mae_m']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def register(x,y,scale=False):
    xm=x.mean(0);ym=y.mean(0);X=x-xm;Y=y-ym
    singular=np.linalg.svd(X,compute_uv=False)
    if len(x)<5 or singular[1]<1e-5:raise ValueError('Insufficient or degenerate camera centre correspondences')
    u,s,vt=np.linalg.svd(Y.T@X/len(x));D=np.eye(3);D[-1,-1]=np.linalg.det(u@vt)
    R=u@D@vt;c=float(np.sum(s*np.diag(D))/np.mean(np.sum(X*X,axis=1))) if scale else 1.
    if not np.isfinite(c) or c<=0:raise ValueError('Invalid registration scale')
    T=np.eye(4);T[:3,:3]=c*R;T[:3,3]=ym-c*R@xm
    err=np.linalg.norm(x@T[:3,:3].T+T[:3,3]-y,axis=1)
    return T,{'correspondences':len(x),'scale':c,'rmse_m':float(np.sqrt(np.mean(err**2))),'median_m':float(np.median(err)),'p95_m':float(np.percentile(err,95)),'source_singular_values':singular.tolist()}
def bootstrap(v):
    v=np.array([np.nan if x is None else x for x in v],float);v=v[np.isfinite(v)]
    if not len(v):return {'mean':None,'ci95':[None,None],'frames':0}
    draws=np.random.default_rng(20260930).integers(0,len(v),(2000,len(v)));means=v[draws].mean(1)
    return {'mean':float(v.mean()),'ci95':np.percentile(means,[2.5,97.5]).tolist(),'frames':len(v),'repeats':2000,'seed':20260930}

def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--gt-root',type=Path,required=True,help='Fresh Blender GT generation directory')
    parser.add_argument('--out',type=Path,required=True,help='New empty evaluation directory')
    args=parser.parse_args()
    gt_manifest=json.loads((args.gt_root/'manifest.json').read_text())
    assert gt_manifest['status']=='COMPLETE' and gt_manifest['old_gt_read'] is False
    validation=json.loads((args.gt_root/'ray_validation.json').read_text())
    assert validation['status']=='PASS'
    args.out.mkdir(parents=True,exist_ok=False)
    manifests={}
    for method in ['M1','M2','M3','M4']:
        d=RUN/'models'/method;m=json.loads((d/'modelling_manifest.json').read_text())
        assert m['status']=='frozen_for_independent_GT_evaluation',method
        frozen=json.loads((d/'freeze_manifest.json').read_text())
        for name,h in frozen['files'].items():assert sha(d/name)==h,(method,name)
        manifests[method]=m
    started=time.time();out=args.out
    sample=json.loads((BASE/'data/depth_samples/modeling_180.json').read_text())['frames']
    gt180,_=pose_lookup('M4',[f['timestamp_ns'] for f in sample]);gtbytime={f['timestamp_ns']:gt180[i] for i,f in enumerate(sample)}
    transforms={}; registrations={}
    for method,m in manifests.items():
        if method=='M1':
            cameras=json.loads((RUN/'models/M1/cameras.json').read_text())['frames']
            frames=[f for f in cameras if f.get('valid',True) and f.get('camera_to_world') is not None and f['timestamp_ns'] in gtbytime]
            try:
                if len(frames)<5:raise ValueError('Fewer than five validated RGB-only camera correspondences; manual check cameras are not reliable alignment evidence')
                T,detail=register(np.array([f['camera_to_world'] for f in frames])[:,:3,3],np.array([gtbytime[f['timestamp_ns']] for f in frames])[:,:3,3],True)
                detail.update(scope='GT-camera-assisted Sim3 shape diagnostic only; not comparable to metric primary ranking',fit_split='modeling_180')
            except ValueError as exc:
                registrations[method]={'status':'NOT_EVALUABLE','reason':str(exc)};continue
        else:
            packet=json.loads((RUN/f'inputs/{method}/packet.json').read_text());native=np.array([f['camera_to_world'] for f in packet['frames']])
            if method=='M4':Tnative=np.eye(4);detail={'scale':1.,'scope':'permitted GT input coordinate frame'}
            else:Tnative,detail=register(native[:,:3,3],gt180[:,:3,3],False);detail['scope']='one SE3 from 180 input camera correspondences; no scale fit'
            T=Tnative@np.linalg.inv(np.array(m['model_from_input'],float));detail['fit_split']='modeling_180'
        detail.update(status='COMPLETE',transform=T.tolist(),transform_direction='GT_from_model',model_sha256=sha(RUN/f'models/{method}/scene.blend'))
        transforms[method]=T;registrations[method]=detail;save(out/method/'registration.json',detail)
    save(out/'registrations.json',registrations)
    all_reports={}
    for split in ['modeling_180','eval_500']:
        frames=json.loads((BASE/f'data/depth_samples/{split}.json').read_text())['frames']
        poses,_=pose_lookup('M4',[f['timestamp_ns'] for f in frames])
        cameras={'intrinsics':[[762.8,0,640],[0,762.8,480],[0,0,1]],'frames':[{'sample_index':i,'source_index':f['source_index'],'timestamp_ns':f['timestamp_ns'],'camera_to_world':poses[i].tolist()} for i,f in enumerate(frames)]}
        save(out/f'gt_cameras_{split}.json',cameras)
        gtpath=args.gt_root/f'{split}/gt_depth_{split}.npz'
        assert sha(gtpath)==gt_manifest['splits'][split]['cache_sha256']
        gt=np.load(gtpath);truth=gt['truth_z_m'];domain=gt['valid_domain'];reports={}
        for method in manifests:
            if method not in transforms:reports[method]=registrations[method];continue
            target=out/method/split;target.mkdir(parents=True,exist_ok=True)
            cmd=[BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1','--python',str(RUN/'tools/raycast_scene.py'),'--','--model',str(RUN/f'models/{method}/scene.blend'),'--cameras',str(out/f'gt_cameras_{split}.json'),'--mesh-transform',str(out/method/'registration.json'),'--out',str(target)]
            reuse=False
            if (target/'report.json').exists():
                prior=json.loads((target/'report.json').read_text());reuse=prior['model_sha256']==registrations[method]['model_sha256'] and prior['transform_applied_to_mesh']==transforms[method].tolist() and prior['frames']==len(frames)
            if not reuse:
                with (target/'blender.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            pred=np.load(target/'depth.npz');assert np.array_equal(pred['pixel_uv'],gt['pixel_uv']);assert np.array_equal(pred['timestamps_ns'],gt['timestamps_ns'])
            z=pred['prediction_z_m'];rows=[{'sample_index':i,'source_index':f['source_index'],'timestamp_ns':f['timestamp_ns'],**metrics(z[i],truth[i],domain[i])} for i,f in enumerate(frames)]
            r={'status':'COMPLETE','method_id':method,'split':split,'ranking_role':'diagnostic_Sim3' if method=='M1' else 'metric_primary_SE3','aggregate':metrics(z,truth,domain),'per_frame':rows,'macro_frame_bootstrap':{k:bootstrap([f[k] for f in rows]) for k in KEYS},'model_sha256':registrations[method]['model_sha256'],'ground_truth_cache_sha256':sha(gtpath),'registration':registrations[method]}
            save(target/'metrics.json',r)
            with (target/'per_frame.csv').open('w') as handle:
                writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            reports[method]=r;print(method,split,r['aggregate'],flush=True)
        pairs={}
        for a,b in itertools.combinations(['M2','M3','M4'],2):
            pairs[a+'_minus_'+b]={k:bootstrap([None if x[k] is None or y[k] is None else x[k]-y[k] for x,y in zip(reports[a]['per_frame'],reports[b]['per_frame'])]) for k in KEYS}
        all_reports[split]={'methods':reports,'paired_macro_differences':pairs}
    for method in manifests:
        d=RUN/'models'/method;frozen=json.loads((d/'freeze_manifest.json').read_text())
        for name,h in frozen['files'].items():assert sha(d/name)==h,(method,name,'changed by evaluator')
    save(out/'summary.json',{'status':'COMPLETE','protocol':'frozen Blender model optical-Z versus newly generated GT at identical cameras/pixels; 180/500 disjoint; M1 unavailable without validated camera registration','ground_truth':{'root':str(args.gt_root),'manifest_sha256':sha(args.gt_root/'manifest.json'),'old_gt_read':False,'generated_utc':gt_manifest['completed_utc'],'source':'original USD imported and raycast anew in Blender'},'prediction_source':'full frozen scene.blend meshes, not DA3 depth','files_unchanged':True,'elapsed_seconds':time.time()-started,'splits':all_reports})
if __name__=='__main__':run()
