import json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parent;C=R/'checks/v1'
regions={33:{'far_wall':[215,145,475,240],'seating_A':[195,260,375,350],'pendants':[90,0,620,150],'floor':[200,365,440,450]},61:{'wall_panel':[240,70,390,140],'missing_pendant':[225,20,350,75],'mirror_virtual_depth':[324,164,410,252],'seats_B':[340,327,550,439]},74:{'wall_panel':[190,50,330,145],'missing_pendant':[365,0,480,60],'return_wall':[10,75,135,190],'seat_A':[218,362,350,470]},82:{'pendants':[25,0,620,175],'troughs_and_foliage':[260,285,600,470],'return_wall':[10,110,190,230]},91:{'missing_west_lights':[20,0,410,105],'west_wall':[215,110,340,160],'troughs':[165,180,400,290],'floor':[170,325,520,450]},100:{'pendants':[0,0,635,140],'glazing':[300,150,400,250],'entry_door':[412,142,500,278],'troughs':[35,240,240,330]},108:{'pendants':[0,0,630,130],'glazing':[245,195,330,260],'desk':[555,270,635,345],'shrub':[40,260,195,475]},118:{'pendants':[160,0,630,140],'glazing':[235,140,310,255],'shrub':[160,340,470,475],'column':[30,125,78,350]},129:{'pendants':[40,0,625,180],'far_wall':[390,180,610,270],'seats_A':[120,363,393,475],'planters':[270,300,510,425]},155:{'far_wall':[240,120,460,220],'pendants':[40,0,620,150],'seats_A':[180,250,365,350],'floor':[160,330,390,420]}}
rows=[]
for i,rs in regions.items():
 n=np.load(C/f'{i:04d}_errors.npz');d=np.load(C/f'{i:04d}_depth.npz');signed=n['signed_z_residual_m']
 for name,rect in rs.items():
  x0,y0,x1,y1=rect;a=signed[y0:y1,x0:x1];ref=d['input_da3_z_m'][y0:y1,x0:x1];pred=d['model_z_m'][y0:y1,x0:x1];v=np.isfinite(a)
  rows.append(dict(sample_index=i,region=name,pixel_region_640x480=rect,valid_pixels=int(v.sum()),median_signed_model_minus_DA3_m=float(np.nanmedian(a)),mae_m=float(np.nanmean(np.abs(a))),p10_signed_m=float(np.nanpercentile(a,10)),p90_signed_m=float(np.nanpercentile(a,90)),median_model_z_m=float(np.nanmedian(pred[v])),median_input_DA3_z_m=float(np.nanmedian(ref[v]))))
json.dump(dict(scope='Spatial diagnostics from existing counted v1 outputs; no new renders/raycast pass; rectangles not score masks',regions=rows),open(R/'analysis/spatial_residuals_v1.json','w'),indent=2)
for r in rows:print(r['sample_index'],r['region'],'signed',round(r['median_signed_model_minus_DA3_m'],3),'mae',round(r['mae_m'],3))
f=json.load(open(R/'checks/input_v1/report.json'))['per_frame'];worst=sorted(f,key=lambda x:x['absrel'],reverse=True)[:12];print('WORST FULL INPUT FRAMES',[(r['sample_index'],round(r['mae_m'],3),round(r['absrel'],3)) for r in worst]);n=np.load(R/'checks/input_v1/depth.npz');ext=[]
for r in worst:
 i=r['sample_index'];z=n['reference_z_m'][i];pred=n['prediction_z_m'][i];ext.append(dict(sample_index=i,stats=r,reference_percentiles=np.nanpercentile(z,[0,10,50,90,100]).tolist(),model_percentiles=np.nanpercentile(pred,[0,10,50,90,100]).tolist()))
json.dump(dict(scope='Diagnostics of the existing single full180 input pass; predicted DA3 only',worst_absrel_frames=ext),open(R/'analysis/full_input_diagnostics_v1.json','w'),indent=2)
