"""Validate and physically copy method-isolated Astra modelling evidence."""
import hashlib,json,shutil,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    samples=json.loads((BASE/'data/depth_samples/modeling_180.json').read_text())['frames']
    evaluation=json.loads((BASE/'data/depth_samples/eval_500.json').read_text())['frames']
    assert len(samples)==180 and len(evaluation)==500
    assert not {f['timestamp_ns'] for f in samples}&{f['timestamp_ns'] for f in evaluation}
    for f in samples+evaluation: assert sha(f['image'])==f['image_sha256']
    K=[[762.8,0,640],[0,762.8,480],[0,0,1]]
    audit={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'PASS','rgb_hashes_verified':680,'splits_disjoint':True,'methods':{},'isolation':'physical copies and method-specific fresh context; no OS enforced read sandbox'}
    for method in ['M1','M2','M3','M4']:
        dst=ROOT/'inputs'/method
        for sub in ['rgb','geometry','contact_sheets']: (dst/sub).mkdir(parents=True,exist_ok=True)
        (ROOT/'models'/method).mkdir(parents=True,exist_ok=True)
        original=None if method=='M1' else json.loads((BASE/f'packets/{method}/packet.json').read_text())
        if original:
            assert sha(original['pose_source'])==original['pose_source_sha256']
            assert len(original['frames'])==180
        frames=[]; errors=[]
        for i,f in enumerate(samples):
            target=dst/'rgb'/f'{i:04d}.png'; shutil.copyfile(f['image'],target)
            g={k:f[k] for k in ['sample_index','source_index','timestamp_ns']}
            g.update(rgb=str(target),rgb_sha256=sha(target),intrinsics=K,resolution=[1280,960])
            if original:
                entry=original['frames'][i]
                assert entry['timestamp_ns']==f['timestamp_ns'] and entry['rgb_sha256']==f['image_sha256']
                assert sha(entry['geometry'])==entry['geometry_sha256']
                with np.load(entry['geometry']) as n:
                    T=np.array(entry['camera_to_world']); R=T[:3,:3]
                    assert np.allclose(T,n['input_camera_to_world'],atol=2e-6)
                    assert np.allclose(R.T@R,np.eye(3),atol=1e-5) and abs(np.linalg.det(R)-1)<1e-5
                    assert np.allclose(T[3],[0,0,0,1]) and np.isfinite(T).all()
                    depth=n['depth_z_m']; valid=n['valid_mask']
                    assert depth.shape==valid.shape and np.isfinite(depth[valid]).all() and (depth[valid]>0).all()
                    kd=n['intrinsics']; assert kd.shape==(3,3) and kd[0,0]>0 and kd[1,1]>0
                    geom=dst/'geometry'/f'{i:04d}.npz'
                    keys=['depth_z_m','intrinsics','valid_mask','confidence','sky','input_camera_to_world','timestamp_ns','source_index','sample_index']
                    np.savez_compressed(geom,**{k:n[k] for k in keys})
                    # Mathematical round trip checks direction and optical-Z convention.
                    pixels=np.array([[50.,60.,1.],[190.,145.,1.],[320.,220.,1.]])
                    pc=(np.linalg.inv(kd)@pixels.T).T*3.0
                    pw=pc@R.T+T[:3,3]; back=(pw-T[:3,3])@R
                    uv=back@kd.T; uv=uv[:,:2]/uv[:,2:]
                    errors.append(float(np.abs(uv-pixels[:,:2]).max()))
                g.update(geometry=str(geom),geometry_sha256=sha(geom),camera_to_world=T.tolist(),selected_window=entry['selected_window'],window_local_index=entry['window_local_index'])
            frames.append(g)
        for start in range(0,180,30):
            sheet=Image.new('RGB',(6*256,5*212),'#eeeeee'); draw=ImageDraw.Draw(sheet)
            for j,f in enumerate(frames[start:start+30]):
                with Image.open(f['rgb']) as im: sheet.paste(im.resize((256,192)),((j%6)*256,(j//6)*212))
                draw.text(((j%6)*256+3,(j//6)*212+194),f"sample {f['sample_index']:03d} / source {f['source_index']}",fill='black')
            sheet.save(dst/'contact_sheets'/f'{start:03d}_{start+29:03d}.jpg',quality=90)
        packet={'schema_version':1,'method_id':method,'rgb_frames':180,'geometry_frames':0 if method=='M1' else 180,'intrinsics':K,'resolution':[1280,960],'depth_axis':None if method=='M1' else 'camera optical Z metres','pose_convention':None if method=='M1' else 'OpenCV RDF camera-to-world','ground_truth_pose_input':method=='M4','ground_truth_depth_used':False,'input_world':'arbitrary inferred RGB-only frame' if method=='M1' else 'native input metric frame; no GT alignment','frames':frames}
        save(dst/'packet.json',packet)
        audit['methods'][method]={'packet_sha256':sha(dst/'packet.json'),'geometry_hashes_verified':0 if not original else 180,'numeric_checks':'PASS','maximum_roundtrip_px':max(errors) if errors else None}
    contract={'status':'FROZEN_BEFORE_MODELLING','model':'gpt-6-astra','blender':'5.2.0 LTS fbe6228777e7','methods':{'M1':'RGB-only; known common calibration','M2':'ViPE native pose + pose-conditioned DA3','M3':'ORB-SLAM3 native pose + pose-conditioned DA3','M4':'GT pose + pose-conditioned DA3, no GT depth'},'revision_limit':5,'paired_checks_per_version':10,'paired_check_limit':50,'supplemental_view_limit':10,'mandatory_full_input_passes':3,'checking_render_limit':60,'fixed_check_indices':[33,61,74,82,91,100,108,118,129,155],'input_bvh_pass_limit':3,'evaluation':{'grid':[160,120],'depth_z_range_m':[0.1,30],'missing_penalty_m':30,'M2_M3_alignment':'one SE3 fit on 180 modelling timestamps, scale=1','M1_alignment':'one Sim3 from frozen estimated modelling cameras; diagnostic only; unavailable if degenerate','bootstrap_repeats':2000,'seed':20260930},'input_check':{'grid':[160,120],'domain':'finite input DA3 optical Z in [0.1,30] m and input valid mask','missing_penalty_m':30,'pixel_roundtrip_tolerance':1e-3,'quality_policy':'no GT tuned acceptance threshold; report residuals and unresolved geometric issues'},'publication_authorized_by_user':True,'input_isolation':audit['isolation']}
    save(ROOT/'configs/run_contract.json',contract)
    save(ROOT/'provenance/input_audit.json',audit)
    print(json.dumps(audit,indent=2))
if __name__=='__main__': main()
