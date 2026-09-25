"""Show five preselected G1 M4 endpoints and evaluator-only target overlays."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/evaluation/tasks/g1_M4_20260924';OUT=ROOT/'figures/m4_tasks/g1_comparison.jpg'
def font(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
def main():
 report=json.loads((BASE/'visibility.json').read_text());rows={r['episode_id']:r for r in report['episodes']}
 names=['Low foliage / pale-grey ceramic pot','North / golden-flower planter','South / golden-flower planter','North / bird-of-paradise planter','South / bird-of-paradise planter']
 pad=24;gap=24;w=576;h=432;rowh=524;top=128;canvas=Image.new('RGB',(2*w+gap+2*pad,top+5*rowh+pad),'#f7f6f1');d=ImageDraw.Draw(canvas)
 d.text((pad,24),'M4 + G1 | Follow the planter instruction',font=font(29),fill='#182c29');d.text((pad,66),'Five targets, first start each. All 20 executions are included in the reported metrics.',font=font(20),fill='#576860')
 for i,k in enumerate([0,4,8,12,16]):
  r=rows[k];im=Image.open(BASE/'endpoint_rgb'/f'episode_{k:02d}.png').convert('RGB');mask=Image.open(BASE/'visibility_masks'/f'episode_{k:02d}_mask.png').convert('L');a=np.asarray(mask)>127
  assert abs(a.mean()-r['target_pixel_fraction'])<1e-6
  mask=mask.resize(im.size,Image.Resampling.NEAREST);edge=Image.fromarray(np.uint8(np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>np.asarray(mask.filter(ImageFilter.MinFilter(3))))*255)
  overlay=Image.blend(im,Image.composite(Image.new('RGB',im.size,'#12ba83'),im,mask),.23);overlay.paste('#0db581',mask=edge)
  y=top+i*rowh;d.text((pad,y),f'Instruction {i+1} · {names[i]}',font=font(23),fill='#182c29')
  canvas.paste(im.resize((w,h)),(pad,y+38));canvas.paste(overlay.resize((w,h)),(pad+w+gap,y+38))
  d.text((pad,y+478),f'Episode {k:02d} | recorded body-camera view',font=font(19),fill='#576860');d.text((pad+w+gap,y+478),f'Evaluator target mask | {100*r["target_pixel_fraction"]:.2f}% of image',font=font(19),fill='#196451')
 OUT.parent.mkdir(parents=True,exist_ok=True);canvas.save(OUT,quality=93,optimize=True);print(OUT)
if __name__=='__main__':main()
