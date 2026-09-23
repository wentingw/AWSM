"""Read frozen reconstructed semantics and declared collision approximations."""
import json
from pathlib import Path
import numpy as np

def rows(path,key):
    d=json.loads(Path(path).read_text());return d if isinstance(d,list) else d[key]

def bounds_of(o):
    b=o.get('bounds',o.get('aabb'))
    if isinstance(b,dict):b=[b.get('min',b.get('minimum')),b.get('max',b.get('maximum'))]
    a=np.asarray(b,float)
    if a.shape!=(2,3) or not np.isfinite(a).all() or np.any(a[1]<a[0]):raise ValueError(f'Invalid bounds: {o.get("object_id")}')
    return a

def load_scene(folder):
    folder=Path(folder);objects=rows(folder/'objects.json','objects');colliders=rows(folder/'colliders.json','colliders')
    for o in objects:
        o['bounds']=bounds_of(o).tolist();o.setdefault('center',np.mean(o['bounds'],axis=0).tolist())
    for o in colliders:o['bounds']=bounds_of(o).tolist()
    return objects,colliders

def floor_and_obstacles(colliders,floor_z=None):
    floors=[c for c in colliders if c.get('role',c.get('category','')).lower() in ('floor','ground') or str(c.get('object_id','')).lower() in ('floor','ground','floor_slab')]
    if floor_z is None:
        if not floors:raise ValueError('Scene needs declared floor collider or explicit model-derived --floor-z')
        floor_z=float(np.median([bounds_of(c)[1,2] for c in floors]))
    obs=[c for c in colliders if c not in floors and bounds_of(c)[1,2]>floor_z+.08]
    return floor_z,obs

def planning_boxes(colliders, floor_z, radius=.32, height=1.35):
    # XY planning over a full upright robot body. Never ignore a low table.
    boxes=[]
    for c in colliders:
        b=bounds_of(c).copy()
        if b[0,2]>=floor_z+height or b[1,2]<=floor_z+.08:continue
        b[0,:2]-=radius;b[1,:2]+=radius;b[:,2]=[floor_z-1,floor_z+height+1];boxes.append(b)
    return np.asarray(boxes).reshape(-1,2,3)

def navigation_constraints(folder):
    p=Path(folder)/'navigation_constraints.json'
    if not p.exists():return [],None
    d=json.loads(p.read_text());regions=d.get('unknown_regions',[])+d.get('vegetation_keepouts',[])
    for x in regions:bounds_of(x)
    b=d.get('known_navigation_bounds')
    if isinstance(b,dict):b=[b.get('min'),b.get('max')]
    return regions,np.asarray(b,float) if b is not None else None
