"""Frozen DINOv2 CPU descriptors for reference-image viewpoint retrieval."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from transformers import Dinov2Model
ROOT=Path(__file__).resolve().parents[2]

def descriptor(model,path):
 im=Image.open(path).convert('RGB');w,h=im.size;scale=256/min(w,h);im=im.resize((round(w*scale),round(h*scale)),Image.Resampling.BICUBIC);left=(im.width-224)//2;top=(im.height-224)//2;im=im.crop((left,top,left+224,top+224));x=np.asarray(im,dtype=np.float32)/255;x=(x-np.array([.485,.456,.406]))/np.array([.229,.224,.225]);x=torch.from_numpy(x.transpose(2,0,1).copy()).float()[None]
 with torch.inference_mode():y=model(x).last_hidden_state[:,0].numpy()[0]
 return y/max(np.linalg.norm(y),1e-12)

def main():
 p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--query',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();torch.set_num_threads(4);model=Dinov2Model.from_pretrained(str(ROOT/'runtime/visual_features/dinov2-small'),local_files_only=True).eval();d=json.loads(a.cache.read_text());views=d['views'];hashes=[hashlib.sha256(Path(v['rgb']).read_bytes()).hexdigest() for v in views];feature_path=a.cache.parent/'dinov2_features.npz'
 if feature_path.exists():
  old=np.load(feature_path);assert old['image_sha256'].tolist()==hashes;features=old['features']
 else:
  features=np.array([descriptor(model,v['rgb']) for v in views]);np.savez_compressed(feature_path,features=features,image_sha256=np.array(hashes))
 q=descriptor(model,a.query);scores=features@q;order=np.argsort(-scores);ranking=[dict(view_id=views[i]['view_id'],score=float(scores[i]),rgb=views[i]['rgb'],camera_to_world=views[i]['camera_to_world']) for i in order];result={'query_rgb_sha256':hashlib.sha256(a.query.read_bytes()).hexdigest(),'model':'official facebook/dinov2-small ViT-S/14','feature':'L2-normalized CLS cosine similarity','model_weight_sha256':json.loads((ROOT/'runtime/visual_features/dinov2-small/provenance.json').read_text())['sha256'],'query_pose_input':False,'GT_geometry_access':False,'candidate_cache':str(a.cache.resolve()),'ranking':ranking};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(ranking[:3]))
if __name__=='__main__':main()
