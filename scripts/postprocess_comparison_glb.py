"""Hide audited remaining GT architectural shells in the browser display scene.

Only the separate display GLB scene graph changes. Vertex buffers, transforms,
original USD, reconstruction models and evaluation artifacts are untouched.
"""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blog/assets/comparison'
PREFIXES=('marble_577061','concrete_masonry_units_415','paint_defaultnullmaterial','aluminum_141538','aluminium_')

def main():
 p=OUT/'GT.glb';raw=p.read_bytes();magic,version,total=struct.unpack_from('<4sII',raw)
 assert magic==b'glTF' and version==2 and total==len(raw)
 chunks=[];offset=12
 while offset<len(raw):
  size,kind=struct.unpack_from('<I4s',raw,offset);chunks.append([kind,raw[offset+8:offset+8+size]]);offset+=8+size
 assert chunks[0][0]==b'JSON'
 doc=json.loads(chunks[0][1]);nodes=doc['nodes'];hidden={i for i,n in enumerate(nodes) if n.get('name','').lower().startswith(PREFIXES)}
 names=[nodes[i].get('name') for i in sorted(hidden)]
 for scene in doc['scenes']:scene['nodes']=[i for i in scene.get('nodes',[]) if i not in hidden]
 for node in nodes:
  if 'children' in node:node['children']=[i for i in node['children'] if i not in hidden]
 doc.setdefault('extras',{})['display_cutaway_hidden_nodes']=names
 payload=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();payload+=b' '*((-len(payload))%4);chunks[0][1]=payload
 body=b''.join(struct.pack('<I4s',len(data),kind)+data for kind,data in chunks);result=struct.pack('<4sII',b'glTF',2,len(body)+12)+body;p.write_bytes(result)
 provenance=json.loads((OUT/'comparison_provenance.json').read_text());asset=next(a for a in provenance['assets'] if a['id']=='GT')
 asset.update(asset_sha256=hashlib.sha256(result).hexdigest(),bytes=len(result))
 asset['hidden_display_objects']=sorted(set(asset['hidden_display_objects']+names))
 asset['scene_graph_cutaway']={'script':'scripts/postprocess_comparison_glb.py','hidden_architectural_node_count':len(hidden),'name_prefixes':list(PREFIXES),'reason':'Audited GT wall panels at y≈15 m, window frames and overhead structural beams obscure the lobby from the shared comparison view. Furniture and real floor surfaces remain.','geometry_buffers_unchanged':True,'no_per_model_alignment_change':True}
 (OUT/'comparison_provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'hidden_nodes':len(hidden),'bytes':len(result),'sha256':asset['asset_sha256']}))
if __name__=='__main__':main()
