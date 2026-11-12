import json,re,math
from PIL import Image,ImageDraw
import numpy as np
from functools import lru_cache
from pathlib import Path
G=json.loads((Path(__file__).parent/'glyphs.json').read_text())['faces']
@lru_cache(maxsize=10000)
def glyph(face,size,ch,xf,yf,slant=0):
 f=G[face];scale=size/f['units_per_em'];g=f['glyphs'][ch];adv=g['adv']*scale;W=int(math.ceil(adv+size*.3+3));H=int(math.ceil(size*1.3+3));S=8
 mask=Image.new('1',(W*S,H*S));toks=re.findall(r'[MLQCZ]|-?\d+(?:\.\d+)?',g['d']);i=0;cur=None;points=[]
 def point():
  nonlocal i
  x,y=float(toks[i]),float(toks[i+1]);i+=2
  return ((xf+x*scale+y*scale*slant)*S,(size+ yf-y*scale)*S)
 def contour():
  nonlocal points,mask
  if len(points)>1:
   part=Image.new('1',mask.size);ImageDraw.Draw(part).polygon(points,fill=1)
   mask=Image.fromarray(np.asarray(mask)^np.asarray(part));points=[]
 while i<len(toks):
  op=toks[i];i+=1
  if op=='M':contour();cur=point();points=[cur]
  elif op=='L':cur=point();points.append(cur)
  elif op=='Q':
   c,e=point(),point();start=cur
   for u in np.linspace(0,1,25)[1:]:points.append(tuple((1-u)**2*start[k]+2*(1-u)*u*c[k]+u*u*e[k] for k in range(2)))
   cur=e
  elif op=='C':
   c1,c2,e=point(),point(),point();start=cur
   for u in np.linspace(0,1,33)[1:]:points.append(tuple((1-u)**3*start[k]+3*(1-u)**2*u*c1[k]+3*(1-u)*u*u*c2[k]+u**3*e[k] for k in range(2)))
   cur=e
  elif op=='Z':contour()
 contour();aa=np.asarray(mask.convert('L').resize((W,H),Image.Resampling.LANCZOS),dtype=float)/255
 return aa,adv

def read(arr,face,size,x,y,width,slant=False):
 allowed=[c for c in G[face]['glyphs'] if c.isascii() and (c.isalnum() or c in " ,.'?!-=/:")]+['×']
 out='';used=0;scores=[]
 while used<width-.5:
  xx=x+used;ix=int(math.floor(xx));yf=y-math.floor(y);xf=xx-ix;iy=int(math.floor(y))-size
  best=None
  for c in allowed:
   templ,adv=glyph(face,size,c,round(xf,2),round(yf,2),math.tan(math.radians(11)) if slant else 0)
   ww=max(1,int(math.floor(xf+adv)));hh=templ.shape[0];target=(255-arr[iy:iy+hh,ix:ix+ww].astype(float))/238
   if target.shape!=(hh,ww):continue
   # cells are evaluated up to next glyph origin; right overhang is accounted by subsequent cell.
   score=float(np.square(target-templ[:,:ww]).sum())/(ww*size)
   if best is None or score<best[0]:best=(score,c,adv)
  score,c,adv=best;out+=c;scores.append(score);used+=adv
  if len(out)>200:break
 return out,scores
