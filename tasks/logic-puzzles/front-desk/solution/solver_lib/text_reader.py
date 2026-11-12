"""Read glyphs from the delivered rasters; no target transcript or answer lookup."""
from pathlib import Path
import json,math,re
import numpy as np
from PIL import Image
from .glyph_ocr import read,G,glyph
ROOT=Path(__file__).resolve().parent
REGIONS=json.loads((ROOT/'regions.json').read_text())

def tight(a):
 y,x=np.where(a>.5)
 if not len(x):raise ValueError('empty glyph image')
 return a[y.min():y.max()+1,x.min():x.max()+1]
def token_template(word,size=34,face='sans'):
 a=np.zeros((int(size*1.5+5),int(size*len(word)+10)));x=0
 for c in word:
  ix=int(x);aa,adv=glyph(face,size,c,round(x-ix,2),0)
  a[:aa.shape[0],ix:ix+aa.shape[1]]=np.maximum(a[:aa.shape[0],ix:ix+aa.shape[1]],aa);x+=adv
 return tight(a)
def normalize(a):return np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).resize((160,40),Image.Resampling.BILINEAR))/255

def read_text(images):
 arrays={f:np.asarray(Image.open(Path(images)/f).convert('L')) for f in ('01.png','02.png','03.png')}
 results=[];labels=['Initial','Final','Initial badges','Final badges','Separation','Either order']+['Then '+str(i) for i in range(1,9)]
 templates={w:token_template(w,28) for w in labels}
 for rr in REGIONS:
  r=dict(rr)
  if r['box'] is None:
   r.update(observed=' ',glyph_height_px=None,must_read=False);results.append(r);continue
  a=arrays[r['image']]
  observed,scores=read(a,r['face'],r['size'],r['x'],r['y'],r['width'],r['italic'])
  err=max(scores,default=0)
  if r['size']==28 and r['face']=='sans' and err>.05:
   x,y,X,Y=r['box'];target=(255-a[y:Y,x:X])/238;nn=normalize(target)
   ranked=sorted((float(np.square(nn-normalize(t)).mean())+.025*abs(t.shape[1]-target.shape[1])+.025*abs(t.shape[0]-target.shape[0]),w) for w,t in templates.items())
   if ranked[0][0]<.15:observed=ranked[0][1];err=ranked[0][0]
  r.update(observed=observed,recognition_error=err);results.append(r)
 by={r['id']:r for r in results}
 names=[by['text_01_'+str(k)]['observed'] for k in range(137,145)]
 if len(set(names))!=8 or not all(re.fullmatch('[A-Z]{8}',s) for s in names):raise ValueError('Cannot recover eight distinct eight-letter names')
 for r in results:
  if r['box'] is None:continue
  if r['recognition_error']>.15:raise ValueError(f"Unrecognized text {r['id']}: {r['recognition_error']}")
  # Tight bounds are remeasured from the recognized width, allowing legal data
  # changes with different proportional letter widths.
  fw=G[r['face']];width=sum(fw['glyphs'][ch]['adv'] for ch in r['observed'])*r['size']/fw['units_per_em']
  rect=[math.floor(r['x']-2),math.floor(r['y']-.82*r['size']),math.ceil(r['x']+width+2),math.ceil(r['y']+.24*r['size'])]
  rx,ry,rX,rY=rect;ys,xs=np.where(arrays[r['image']][ry:rY,rx:rX]<128)
  if not len(xs):raise ValueError('Missing text ink '+r['id'])
  r['box']=[int(xs.min()+rx),int(ys.min()+ry),int(xs.max()+rx+1),int(ys.max()+ry+1)]
  # Native cap and digit ink measurements, not the nominal em size.
  heights=[];x=r['x'];f=G[r['face']];size=r['size'];bx,by,bX,bY=r['box']
  for ch in r['observed']:
   adv=f['glyphs'][ch]['adv']*size/f['units_per_em']
   if ch.isupper() or ch.isdigit() or ch=='?':
    lo=max(bx,math.floor(x));hi=min(bX,math.ceil(x+adv))
    if hi>lo:
     rows=np.flatnonzero((arrays[r['image']][by:bY,lo:hi]<128).any(1))
     if len(rows):heights.append(int(rows[-1]-rows[0]+1))
   x+=adv
  r['must_read']=bool(heights);r['glyph_height_px']=min(heights) if heights else None
  if heights and min(heights)<19:raise ValueError('Unreadable cap/digit: '+r['id'])
 return results
