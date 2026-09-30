import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import numpy as np,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).parent;P=json.loads((ROOT.parent.parent/'inputs/M2/packet.json').read_text());X=np.array(json.loads((ROOT/'analysis/transform.json').read_text())['model_from_input'])
regions={
 'planter_far_left_33':(33,[470,525,590,552]),'planter_far_right_33':(33,[668,527,780,560]),
 'planter_far_left_129':(129,[567,700,699,737]),'planter_far_right_129':(129,[800,780,1004,835]),
 'planter_near_left_91':(91,[355,461,526,519]),'planter_near_right_91':(91,[620,463,771,505]),
 'seat_far_left_129':(129,[302,807,383,850]),'seat_far_mid_129':(129,[549,754,666,783]),'seat_far_right_129':(129,[696,829,748,861]),
 'seat_far_left_33':(33,[427,620,470,646]),'seat_far_mid_33':(33,[548,552,602,565]),'seat_far_right_33':(33,[671,572,710,590]),
 'seat_near_mid_61':(61,[843,746,907,770]),'seat_near_left_61':(61,[726,691,779,719]),'seat_near_right_61':(61,[1000,781,1053,810]),
 'table_far_33':(33,[541,614,616,633]),'table_far_129':(129,[457,866,539,889]),'table_near_61':(61,[778,847,884,900]),
 'reception_33':(33,[575,443,678,465]),'reception_129':(129,[919,568,1014,594]),
 'pot_mirror_61':(61,[506,544,537,575]),'pot_mirror_74':(74,[675,555,705,584]),
 'column_33':(33,[281,340,317,460]),'column_100':(100,[487,352,515,464]),'column_129':(129,[389,427,420,639]),
 'window_33':(33,[90,361,157,446]),'window_118':(118,[545,346,610,470]),
 'wall_end_91':(91,[401,159,673,220]),'wall_end_129':(129,[816,366,1239,427]),
 'ceiling_91':(91,[565,20,677,48]),'ceiling_129':(129,[680,53,937,102]),
 'mirror_wall_61':(61,[601,146,1001,232]),'mirror_wall_82':(82,[540,318,883,374]),
 'wall_recess_82':(82,[69,349,327,405]),
 'lamp_floor_33':(33,[823,400,844,418]),'lamp_floor_82':(82,[386,518,418,547]),
 'tree_far_left_129':(129,[799,486,831,530]),'tree_far_right_129':(129,[1138,502,1181,536]),
 'grass_window_129':(129,[244,673,301,716]),'grass_window_91':(91,[829,380,861,413]),
 'tall_plant_near_91':(91,[438,514,456,530]),
 'light_a_33':(33,[393,119,505,142]),'light_b_33':(33,[717,135,830,152]),
 'light_c_33':(33,[1055,106,1189,129]),'light_d_129':(129,[597,83,724,120]),
}
res={}
for name,(i,box) in regions.items():
 f=P['frames'][i];n=np.load(f['geometry']);d=n['depth_z_m'];K=n['intrinsics'];u,v=np.meshgrid(np.arange(d.shape[1])+.5,np.arange(d.shape[0])+.5); uu=u*1280/d.shape[1];vv=v*960/d.shape[0];m=n['valid_mask']&(uu>=box[0])&(uu<=box[2])&(vv>=box[1])&(vv<=box[3]);q=np.stack([(u-K[0,2])*d/K[0,0],(v-K[1,2])*d/K[1,1],d],-1)[m];T=X@np.array(f['camera_to_world']);a=q@T[:3,:3].T+T[:3,3];res[name]={'sample_index':i,'rgb_box':box,'model_p10_p50_p90':np.percentile(a,[10,50,90],axis=0).tolist(),'points':len(a)};print(name,np.round(np.median(a,0),3).tolist(), 'range',np.round(np.ptp(np.percentile(a,[10,90],axis=0),axis=0),3).tolist())
(ROOT/'analysis/object_depth_regions.json').write_text(json.dumps(res,indent=2))
# Orthographic measured point image is diagnostic only.
n=np.load(ROOT/'analysis/measured_points.npz');a=n['points'];c=n['colors'];sel=(a[:,2]>.2)&(a[:,2]<2.3)&(a[:,0]>-6)&(a[:,0]<8)&(a[:,1]>-3)&(a[:,1]<22);a=a[sel];c=c[sel];im=Image.new('RGB',(900,1400),(245,245,245));pix=im.load()
for q,color in zip(a[::3],c[::3]):
 x=int((q[0]+6)*60);y=int((22-q[1])*55)
 if 0<=x<900 and 0<=y<1400:pix[x,y]=tuple(color)
draw=ImageDraw.Draw(im)
for y in range(-2,23,2):draw.line((0,(22-y)*55,850,(22-y)*55),fill=(180,80,80));draw.text((5,(22-y)*55+2),str(y),fill=(230,0,0))
for x in range(-6,9,2):draw.line(((x+6)*60,0,(x+6)*60,1399),fill=(180,80,80));draw.text(((x+6)*60+2,5),str(x),fill=(230,0,0))
im.save(ROOT/'analysis/measured_plan.png')
