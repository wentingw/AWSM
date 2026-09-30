import os
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.optimize import least_squares
from session_log import record
R=Path(__file__).resolve().parents[2];I=R.parents[1]/'inputs/M3';P=json.loads((I/'packet.json').read_text());L=json.loads((R/'layout.json').read_text());X=np.array(L['model_from_input']);K=np.array(P['intrinsics'],float);K[:2]*=.5
T={i:X@np.array(f['camera_to_world']) for i,f in enumerate(P['frames'])}
def ray(i,u,v):
 t=T[i];return t[:3,3],t[:3,:3]@np.linalg.inv(K)@np.array([u,v,1.])
def plane(i,u,v,z):
 o,d=ray(i,u,v);return o+(z-o[2])/d[2]*d
obs={129:[(156,420),(202,381),(252,367),(312,380),(322,405),(366,418)],61:[(380,350),(448,368),(507,385),(591,468)]}
print('SEAT_ANCHORS', {i:[plane(i,*uv,.565).round(3).tolist() for uv in v] for i,v in obs.items()})
for i in [33,91,100,108,118,129,155,74,82]:
 im=Image.open(P['frames'][i]['rgb']).resize((640,480));d=ImageDraw.Draw(im)
 for x in range(0,640,50):d.line((x,0,x,480),fill=(240,70,70),width=1);d.text((x+2,5),str(x),fill=(250,30,30))
 for y in range(50,480,50):d.line((0,y,640,y),fill=(240,70,70),width=1);d.text((2,y+2),str(y),fill=(250,30,30))
 im.save(R/f'analysis/repair/source_grid_{i:04d}.jpg')
record('numeric_read_and_visual_preparation',[I/'packet.json',R/'layout.json']+[P['frames'][i]['rgb'] for i in [33,91,100,108,118,129,155,74,82]],'Ran measure_repairs.py: native camera ray-plane seat anchors, source RGB coordinate grids. No Blender render or BVH.')
record('visual_inspection',[I/'contact_sheets'/f'{a:03d}_{a+29:03d}.jpg' for a in range(0,180,30)]+[R/f'checks/v1/{i:04d}_comparison.jpg' for i in [33,61,74,82,91,100,108,118,129,155]]+[I/f'rgb/{i:04d}.png' for i in [61,118,129]],'All six contact sheets and all ten actual v1 paired sheets viewed; original source61/118/129 viewed full resolution. Generic tools read: paired_check_blender, raycast_scene, visualize_checks, inspect_scene, validate_artifacts; reviewer inspect_static.py read, never executed against independent_review outputs.')
