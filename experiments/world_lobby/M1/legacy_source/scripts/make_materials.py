from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
out=Path(__file__).resolve().parents[1]/'assets';out.mkdir(exist_ok=True)
rng=np.random.default_rng(821)
n=1024
# Authored procedural surface textures. No geometry or image-derived depth is used.
y,x=np.mgrid[0:n,0:n]
noise=rng.normal(0,1,(n,n))
def low(scale):
 a=Image.fromarray(np.uint8(rng.uniform(0,255,(scale,scale)))).resize((n,n),Image.Resampling.BICUBIC)
 return (np.asarray(a).astype(float)-127)/127

def save(name,a): Image.fromarray(np.uint8(np.clip(a,0,255))).save(out/name)
grain=low(80)*2+noise*1.8
for i in range(4):
 f=np.asarray(Image.fromarray(np.uint8(rng.uniform(0,255,(16,n)))).resize((n,n),Image.Resampling.BICUBIC)).astype(float)
 grain+=(f-127)*.035
veins=np.sin(x*.21+low(9)*1.8+y*.0008)+np.sin(x*.075+low(7)*2)
base=np.array([151,143,125])[None,None,:]
save('oak.jpg',base+(grain+veins*5)[...,None])
stone=low(12)*7+low(80)*3+noise*2
save('limestone.jpg',np.array([157,154,140])[None,None,:]+stone[...,None])
fabric=(noise*4+((x%3==0)+(y%3==0))*2+low(40)*3)
save('sage_fabric.jpg',np.array([125,138,108])[None,None,:]+fabric[...,None])
# Almost black lacquer with delicate irregular brass flecks.
base=np.zeros((n,n,3));base[:]=[23,24,21];base+=low(12)[...,None]*2
for row in range(0,n,15):
 for col in range(0,n,15):
  if rng.random()<.84:
   yy=row+int(rng.integers(-2,3));xx=col+int(rng.integers(-2,3));h=int(rng.integers(2,6));w=int(rng.integers(2,5))
   c=np.array([105,88,54])*rng.uniform(.45,1.25)
   base[max(0,yy):yy+h,max(0,xx):xx+w]=c
save('black_brass.jpg',base)
save('plaster.jpg',np.array([197,194,185])[None,None,:]+(low(8)*4+noise)[...,None])
print('Generated five procedural textures')

save('concrete.jpg',np.array([99,101,97])[None,None,:]+stone[...,None])
