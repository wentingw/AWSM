"""Frozen calibrated-depth TSDF baselines. No GT, extra pose fitting, or semantics."""
import argparse,hashlib,json,time,os
from pathlib import Path
import cv2,numpy as np,open3d as o3d
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--method',choices=['B1','B2','B2p'],required=True);p.add_argument('--voxel',type=float,default=.05);a=p.parse_args();source={'B1':'M2','B2':'B2','B2p':'M3'}[a.method];packet_path=ROOT/'data/packets'/source/'packet.json';packet=json.loads(packet_path.read_text());out=ROOT/'experiments/world_lobby'/a.method/'tsdf_20260923';out.mkdir(parents=True,exist_ok=True)
 volume=o3d.pipelines.integration.ScalableTSDFVolume(voxel_length=a.voxel,sdf_trunc=3*a.voxel,color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8);frames=[];start=time.monotonic()
 for f in packet['frames']:
  if 'geometry' not in f:continue
  z=np.load(f['geometry']);depth=z['depth_z_m'].copy();depth[~z['valid_mask'].astype(bool)]=0;depth[~np.isfinite(depth)]=0;K=z['intrinsics'].astype(float);T=z['camera_to_world'];h,w=depth.shape
  rgb=cv2.cvtColor(cv2.imread(f.get('processed_rgb',f['rgb'])),cv2.COLOR_BGR2RGB)
  assert rgb.shape[:2]==depth.shape,(rgb.shape,depth.shape,f['keyframe_index'])
  if w>640:
   scale=640/w;size=(640,int(round(h*scale)));depth=cv2.resize(depth,size,interpolation=cv2.INTER_NEAREST);rgb=cv2.resize(rgb,size,interpolation=cv2.INTER_AREA);K[:2]*=scale;h,w=depth.shape
  intr=o3d.camera.PinholeCameraIntrinsic(w,h,K[0,0],K[1,1],K[0,2],K[1,2]);rgbd=o3d.geometry.RGBDImage.create_from_color_and_depth(o3d.geometry.Image(np.ascontiguousarray(rgb)),o3d.geometry.Image(np.ascontiguousarray(depth.astype(np.float32))),depth_scale=1.0,depth_trunc=30,convert_rgb_to_intensity=False);volume.integrate(rgbd,intr,np.linalg.inv(T));frames.append(f['keyframe_index'])
  if len(frames)%10==0:print(a.method,len(frames),time.monotonic()-start,flush=True)
 mesh=volume.extract_triangle_mesh();mesh.compute_vertex_normals();o3d.io.write_triangle_mesh(str(out/'mesh.ply'),mesh,write_ascii=False);m={'status':'complete','method_id':a.method,'geometry_source':source,'input_packet_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),'voxel_m':a.voxel,'sdf_trunc_m':3*a.voxel,'depth_trunc_m':30,'input_depth_max_width':640,'pose_alignment_during_fusion':'none; native poses','GT_access':False,'semantic_objects':False,'frames':frames,'vertices':len(mesh.vertices),'triangles':len(mesh.triangles),'bounds':[mesh.get_min_bound().tolist(),mesh.get_max_bound().tolist()],'seconds':time.monotonic()-start};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m),flush=True)
if __name__=='__main__':main()
