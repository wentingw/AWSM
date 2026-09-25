"""Build a display-only M4/G1 world; recorded physical episode stays unchanged."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/tasks/g1_M4/presentation_20260924';SOURCE=ROOT/'experiments/tasks/g1_M4/replay_20260924/episode_00/episode_world.xml'
def main():
 manifest=OUT/'material_manifest.json';m=json.loads(manifest.read_text());tree=ET.parse(SOURCE);r=tree.getroot();world=r.find('worldbody');asset=r.find('asset');visual=r.find('visual')
 for g in list(world.findall('geom')):world.remove(g)
 for light in list(world.findall('light')):world.remove(light)
 for x in list(visual.findall('headlight')):visual.remove(x)
 ET.SubElement(visual,'headlight',{'ambient':'.3 .3 .3','diffuse':'.5 .5 .5','specular':'.1 .1 .1'})
 ET.SubElement(world,'light',{'pos':'17 22 9','dir':'0 0 -1','directional':'true','diffuse':'.75 .75 .75','ambient':'.35 .35 .35','castshadow':'false'})
 for i,g in enumerate(m['groups']):
  name=f'M4_visual_{i:03d}';ET.SubElement(asset,'mesh',{'name':name,'file':str(OUT/g['obj']),'inertia':'shell'});ET.SubElement(world,'geom',{'name':name,'type':'mesh','mesh':name,'contype':'0','conaffinity':'0','rgba':' '.join(map(str,g['rgba']))})
 target=OUT/'episode_display.xml';tree.write(target)
 meta={'source_episode_xml':str(SOURCE),'source_episode_xml_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_manifest':str(manifest),'source_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'source_scene_sha256':m['source_sha256'],'display_xml':str(target),'display_xml_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'coordinate_frame':m['coordinate_frame'],'display_only':True,'collision_boxes_and_duplicate_floor_removed_from_display':True,'display_mesh_collision':False,'physics_source_unchanged':True,'omitted_display_objects':m['omitted_objects']};(OUT/'display_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
if __name__=='__main__':main()
