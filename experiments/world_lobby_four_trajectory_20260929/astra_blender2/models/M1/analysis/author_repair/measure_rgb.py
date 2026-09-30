"""M1-only conditional ray/plane measurements; these are NOT measured depths."""
import json, hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
R=Path(__file__).resolve().parents[2]
C={f['sample_index']:f for f in json.loads((R/'cameras.json').read_text())['frames']}
observations=[(33,'north_table',574,630,.454),(155,'north_table',542,574,.454),(129,'north_table',475,862,.454),(129,'left_planter_front_top',640,672,.70),(129,'right_planter_front_top',900,722,.70),(33,'left_planter_front_top',530,520,.70),(33,'right_planter_front_top',725,529,.70),(91,'right_planter_front_top',446,448,.70),(91,'left_planter_front_top',698,445,.70),(61,'south_seat_A',759,695,.54),(61,'south_seat_B',883,717,.54),(61,'south_seat_C',1014,772,.54),(74,'south_seat_edge',1188,625,.54),(82,'south_table',1130,621,.454)]
rows=[]
for i,n,u,v,z in observations:
 c=C[i];T=np.array(c['camera_to_world']);d=T[:3,:3]@np.linalg.inv(c['intrinsics'])@np.array([u,v,1]);t=(z-T[2,3])/d[2];p=T[:3,3]+t*d
 rows.append(dict(sample_index=i,landmark=n,pixel_uv=[u,v],pixel_region=[u-15,v-15,u+15,v+15],assumed_plane_z_m=z,conditional_world_xyz_m=p.tolist(),conditional_optical_z_m=float(t),input_depth_residual_m=None,depth_reference='N/A; RGB-only; ray-plane distance depends on assumed camera/height',pixel_uncertainty=15))
def project(i,p):
 c=C[i];T=np.array(c['camera_to_world']);q=(np.array(p)-T[:3,3])@T[:3,:3];a=np.array(c['intrinsics'])@q;return a[:2]/a[2]
fitrows=[r for r in rows if r['landmark']=='north_table']
fit=least_squares(lambda xy: np.concatenate([project(r['sample_index'],[*xy,.454])-r['pixel_uv'] for r in fitrows]),[3,7.3],loss='soft_l1',f_scale=30)
for r in fitrows:r['fit_signed_pixel_residual']=list(project(r['sample_index'],[*fit.x,.454])-r['pixel_uv'])
out=dict(method_id='M1',camera_sha256=hashlib.sha256((R/'cameras.json').read_bytes()).hexdigest(),source_resolution=[1280,960],observations=rows,north_table_joint_fit_xy_m=fit.x.tolist(),warning='Large cross-view disagreement retained; positions are inferred compromises, cameras are unchanged.')
(R/'analysis/author_repair/rgb_ray_plane_measurements.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'north_table_fit':fit.x.tolist(),'north_table_residuals':[r['fit_signed_pixel_residual'] for r in fitrows]}))
