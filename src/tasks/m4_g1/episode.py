"""M4-specific language/floor adapter around the validated G1 dynamics runner."""
from pathlib import Path
import argparse,json,sys,xml.etree.ElementTree as ET
import numpy as np
import mujoco
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.tasks import g1_episode as runner
from src.tasks.scene_io import load_scene,bounds_of
from src.tasks.m4_g1.language import query_scene

def main():
    partial=argparse.ArgumentParser(add_help=False);partial.add_argument('--scene',type=Path,required=True);partial.add_argument('--request',type=Path,required=True);partial.add_argument('--out',type=Path,required=True)
    args,_=partial.parse_known_args();objects,colliders=load_scene(args.scene)
    floors=[c for c in colliders if c.get('role')=='floor'];assert len(floors)==2
    original_make=runner.make_model
    def make_model(asset_root,obstacles,floor_z,out,visual_scene=None):
        original_make(asset_root,obstacles,floor_z,out,visual_scene)
        path=out/'episode_world.xml';tree=ET.parse(path);root=tree.getroot();world=root.find('worldbody')
        # Replace the display runner's global plane with both original M4 floor slabs.
        for geom in list(world.findall('geom')):
            if geom.get('type')=='plane':world.remove(geom)
        for i,c in enumerate(floors):
            b=bounds_of(c);center=b.mean(0);size=(b[1]-b[0])/2
            ET.SubElement(world,'geom',{'name':f'world_floor_{i}','type':'box','pos':' '.join(map(str,center)),'size':' '.join(map(str,size)),'rgba':'.72 .72 .68 1','friction':f"{c.get('friction',.55)} .02 .002"})
        tree.write(path);return mujoco.MjModel.from_xml_path(str(path))
    floor_bounds=bounds_of(next(c for c in floors if c['object_id']=='floor_stone')).copy();floor_bounds[0,:2]+=.52;floor_bounds[1,:2]-=.52
    runner.query_scene=query_scene;runner.make_model=make_model;runner.navigation_constraints=lambda folder:([],floor_bounds)
    runner.main()
    p=args.out/'summary.json';s=json.loads(p.read_text());s.update(language_scope='constrained Chinese attributes and north/south instance selection; north is map +Y',scene_method='M4',floor_representation='original stone floor slab top 0.025 m and raised inset top 0.041 m; finite floor bounds',recognition_scope='generated semantic map lookup; target visibility verified separately after execution')
    if s.get('limitations'):s['limitations'][0]='constrained Chinese attribute/direction matching over generated semantics'
    p.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':main()
