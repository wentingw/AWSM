import json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];run=ROOT/'experiments/world_lobby/M2/vipe_full_20260923';rgb=json.loads((ROOT/'data/world_lobby/rgb_180_manifest.json').read_text())['frames'];assert (run/'modelling_ready.json').exists();out=ROOT/'data/packets/M2';out.mkdir(parents=True,exist_ok=True)
records=[]
for f in rgb:
 k=f['keyframe_index'];src=run/'depth'/f'{k*50:06d}.npz';v=np.load(src);fx,fy,cx,cy=v['intrinsics'];K=np.array([[fx,0,cx],[0,fy,cy],[0,0,1]]);d=v['depth_z_m'];target=out/f'{k:03d}_geometry.npz';np.savez_compressed(target,depth_z_m=d,intrinsics=K,camera_to_world=v['camera_to_world'],valid_mask=np.isfinite(d)&(d>0));records.append(dict(keyframe_index=k,timestamp_ns=f['timestamp_ns'],rgb=f['sampled_rgb'],rgb_sha256=f['sha256'],geometry=str(target),geometry_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),geometry_source=str(src),pose_convention='OpenCV RDF c2w',units='ViPE native near-metric metres',depth_axis='optical_z'))
packet=dict(method_id='M2',status='complete',geometry_frames=180,rgb_frames=180,pose_source='ViPE full8999 RGB-video pose estimation',depth_source='ViPE adaptive_unidepth-s native sampled depths',coordinate_frame='native ViPE coordinate; preserve scale and export exact gravity normalization transform if used',calibration_source='ViPE GeoCalib + optimization; no external calibration',allowed_inputs='sampled RGB + ViPE poses/intrinsics/depth only',forbidden_inputs=['GT poses/depth/geometry','other methods or legacy reconstructed scenes','GT evaluation results'],frames=records,output_contract=str(ROOT/'configs/astra_modelling_contract.md'))
(out/'packet.json').write_text(json.dumps(packet,indent=2)+'\n');print(out/'packet.json')
