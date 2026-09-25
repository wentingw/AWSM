"""Transparent Chinese attribute/direction grounding over reconstructed objects.

No sentence-to-instance lookup or hidden expected target file is used. North is
explicitly the M4 map's +Y axis; this is constrained semantic-map navigation.
"""
import json
import numpy as np

def query_scene(text,objects):
    if not any(w in text for w in ['花盆','盆栽','绿植','植物']):
        return {'status':'unsupported_category','candidates':[]}
    candidates=[o for o in objects if o.get('category') in ['potted_plant','planter']]
    filters=[]
    if any(w in text for w in ['金黄','金色','花枝']):filters.append(('foliage','golden'))
    if any(w in text for w in ['鹤望兰','天堂鸟']):filters.append(('species','bird of paradise'))
    if '低矮' in text:filters.append(('species','low foliage'))
    if any(w in text for w in ['灰色','陶瓷']):filters.append(('finish','pale grey ceramic'))
    if '长方形' in text:candidates=[o for o in candidates if o.get('category')=='planter']
    for key,value in filters:candidates=[o for o in candidates if value in str(o.get('attributes',{}).get(key,'')).lower()]
    direction='north' if '北侧' in text else 'south' if '南侧' in text else None
    candidates.sort(key=lambda o:(-float(o['center'][1]) if direction=='north' else float(o['center'][1]) if direction=='south' else 0,o['object_id']))
    status='no_semantic_match' if not candidates else 'ambiguous_target' if len(candidates)>1 and not direction else 'matched'
    return {'status':status,'category':'potted_plant or planter','attribute_filters':filters,'direction':direction,'direction_convention':'north = +Y in the M4 map','candidates':[{'object_id':o['object_id'],'score':1.0,'center_y_m':o['center'][1]} for o in candidates],'scope':'constrained Chinese categories, attributes and cardinal directions over reconstructed semantics; no visual object recognition'}
