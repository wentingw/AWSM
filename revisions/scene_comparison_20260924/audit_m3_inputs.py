"""Read-only evidence-chain audit of M3's OpenVINS-conditioned MapAnything outputs."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
packet=json.loads((ROOT/'data/packets/M3/packet.json').read_text())
poses=np.loadtxt(ROOT/'experiments/world_lobby/M3/openvins_20260923/openvins_camera_pose_180.tum')
cal=json.loads((ROOT/'data/world_lobby/calibration/camera_imu.json').read_text());T_frd=np.asarray(cal['T_imu_camera'],float);S=np.diag([1.,-1.,-1.,1.]);T_flu=S@T_frd
# Source collector uses a fixed calibration; independently compare exported body/camera tracks.
body=np.loadtxt(ROOT/'experiments/world_lobby/M3/openvins_20260923/output/pose_imu.tum')
cam=np.loadtxt(ROOT/'experiments/world_lobby/M3/openvins_20260923/output/pose_cam.tum')
assert body.shape==cam.shape and np.array_equal(body[:,0],cam[:,0])
R=Rotation.from_quat(body[:,4:]).as_matrix();expected_position=body[:,1:4]+np.einsum('nij,j->ni',R,T_flu[:3,3]);expected_rotation=R@T_flu[:3,:3]
rotation_error=Rotation.from_matrix(expected_rotation.transpose(0,2,1)@Rotation.from_quat(cam[:,4:]).as_matrix()).magnitude()
rows=[];windows={}
for f in packet['frames']:
 if 'geometry' not in f:continue
 data=np.load(f['geometry']);source=np.load(f['geometry_source']);window=Path(f['geometry_source']).parent;manifest=json.loads((window/'manifest.json').read_text());windows[str(window)]=manifest
 assert manifest['mode']=='M3' and manifest['metric_scale_flag'] is True and manifest['ground_truth_used'] is False
 t=f['timestamp_ns']/1e9;i=int(np.argmin(abs(poses[:,0]-t)));T=np.eye(4);T[:3,:3]=Rotation.from_quat(poses[i,4:]).as_matrix();T[:3,3]=poses[i,1:4]
 assert np.allclose(data['camera_to_world'],T,rtol=0,atol=3e-6)
 assert np.array_equal(data['camera_to_world'],source['input_camera_pose'])
 assert np.array_equal(data['depth_z_m'],source['depth_z'],equal_nan=True)
 assert np.array_equal(data['valid_mask'],source['mask'])
 assert hashlib.sha256(Path(f['geometry']).read_bytes()).hexdigest()==f['geometry_sha256']
 rows.append({'frame':f['keyframe_index'],'pose_max_difference':float(np.max(abs(data['camera_to_world']-T))), 'timestamp_difference_s':float(abs(poses[i,0]-t)), 'pose_match_error_s':max(x.get('pose_match_error_s') or 0 for x in manifest['frames'])})
report={'status':'pass','pipeline':'RGB + calibration + OpenVINS estimated metric camera-to-world pose -> MapAnything (pose and scale conditioning enabled) -> optical-Z depth -> Astra packet',
 'geometry_frames':len(rows),'total_rgb_frames':len(packet['frames']),'missing_geometry_frames':[f['keyframe_index'] for f in packet['frames'] if 'geometry' not in f],
 'max_pose_difference_from_openvins':max(r['pose_max_difference'] for r in rows),'max_timestamp_difference_s':max(r['timestamp_difference_s'] for r in rows),
 'chosen_window_count':len(windows),'window_modes':sorted(set(m['mode'] for m in windows.values())),
 'mapanything_checkpoint':sorted(set(m['checkpoint'] for m in windows.values())),
 'camera_conversion':{'raw_body_and_camera_samples':len(body),'max_position_residual_m':float(np.max(np.linalg.norm(expected_position-cam[:,1:4],axis=1))),'max_rotation_residual_rad':float(np.max(rotation_error)),'T_imu_camera_FLU':T_flu.tolist()},
 'depth_passthrough_exact':True,'pose_source':'OpenVINS output; not MapAnything output pose','global_gt_scale_correction_applied_to_packet':False,
 'limitation':'This audit verifies file/data conventions and passthrough; it does not prove physical clock accuracy, sensor calibration accuracy, sufficient excitation, or estimator optimality.'}
assert len(rows)==175 and report['camera_conversion']['max_position_residual_m']<1e-5 and report['camera_conversion']['max_rotation_residual_rad']<1e-5
(OUT/'m3_pipeline_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
