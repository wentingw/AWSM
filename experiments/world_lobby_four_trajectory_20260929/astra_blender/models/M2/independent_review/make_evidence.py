from pathlib import Path
from PIL import Image,ImageDraw
import json
O=Path(__file__).resolve().parent;M=O.parent;B=M.parent.parent
rows=[
 (90,(95,45,435,205),'M2-I01: near-end wall / I02: passage'),
 (0,(285,230,555,350),'M2-I03: far cushions intersect'),
 (135,(0,355,380,480),'M2-I04: foreground seating displacement'),
 (45,(520,205,640,385),'M2-I05: mirror reflection distortion'),
]
canvas=Image.new('RGB',(1280,4*310),(28,28,28));d=ImageDraw.Draw(canvas)
for k,(i,box,label) in enumerate(rows):
 y=k*310
 d.text((12,y+8),f'{label} | frame {i} | source RGB (left), existing author render (right)',fill='white')
 a=Image.open(B/f'inputs/M2/rgb/{i:04d}.png').convert('RGB').resize((640,480),Image.Resampling.LANCZOS)
 b=Image.open(M/f'checks/v1_{i:04d}.png').convert('RGB')
 for x,im in [(0,a),(640,b)]:
  c=im.crop(box);c.thumbnail((624,268),Image.Resampling.LANCZOS)
  # Preserve aspect and show matched crop at identical scale.
  if c.width<624 and c.height<268:
   scale=min(624/c.width,268/c.height);c=c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST)
  canvas.paste(c,(x+(640-c.width)//2,y+34+(268-c.height)//2))
canvas.save(O/'evidence_crops.jpg',quality=94)
(O/'evidence_crops.json').write_text(json.dumps({'rendering_views_added':0,'operation':'Matched crops of existing source RGB resized to 640x480 and existing author PNG; no Blender renders','coordinate_convention':'640x480 per image, excludes comparison header','rows':[{'frame':i,'crop_xyxy':box,'label':label} for i,box,label in rows]},indent=2)+'\n')

