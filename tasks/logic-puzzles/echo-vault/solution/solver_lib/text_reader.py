"""Glyph recovery from PNGs, using outline fonts and layout-only windows."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
from .glyph_ocr import read,G,glyph
ROOT=Path(__file__).parent
REGIONS=json.loads((ROOT/'regions.json').read_text())
# Fixed vocabulary for headings and diagram grammar only. Specimen names,
# ring values, pairs and observation parameters are recovered glyph by glyph.
LABELS=['Echo Vault','Calibration / 01','Reading the vault / 02','Unfiled sequence / 03',
'The tidal laboratory has misplaced its sound specimens.','Initial','Final','After',
'Transfer log','Exchange tubes','Then: rings','Calibration specimens ×1','Rings ×1',
'After ?','Sound specimens ×1','Unfiled','Transfers','Observations']+[f'After {i}' for i in range(1,9)]+[f'Step {i}' for i in range(1,9)]
def read_label(a,r):
 face,size=r['face'],r['size'];font=G[face];candidates=[]
 ix=math.floor(r['x']);iy=math.floor(r['y'])-size
 for word in LABELS:
  width=sum(font['glyphs'][c]['adv'] for c in word)*size/font['units_per_em']
  if abs(width-r['width'])>1:continue
  H=math.ceil(size*1.3+3);W=math.ceil(width+size*.3+5);canvas=np.zeros((H,W));xx=r['x']-ix
  for c in word:
   g,adv=glyph(face,size,c,round(xx-math.floor(xx),2),round(r['y']-math.floor(r['y']),2),math.tan(math.radians(11)) if r['italic'] else 0)
   lo=math.floor(xx);ww=min(g.shape[1],W-lo);canvas[:g.shape[0],lo:lo+ww]=np.maximum(canvas[:g.shape[0],lo:lo+ww],g[:,:ww]);xx+=adv
  target=(255-a[iy:iy+H,ix:ix+W].astype(float))/238
  score=float(np.square(target-canvas).mean());candidates.append((score,word))
 if not candidates:return None
 score,word=min(candidates)
 return (word,score) if score<.04 else None
def read_text(images):
 arrays={f:np.asarray(Image.open(Path(images)/f).convert('L')) for f in ('01.png','02.png','03.png')};results=[]
 for rr in REGIONS:
  r=dict(rr);a=arrays[r['image']]
  label=read_label(a,r) if r['face']!='mono' else None
  if label:observed,err=label
  else:
   observed,scores=read(a,r['face'],r['size'],r['x'],r['y'],r['width'],r['italic']);err=max(scores,default=0)
  if err>.17:raise ValueError(f'Unrecognized text {r["id"]}: {observed!r} error={err}')
  r.update(observed=observed,recognition_error=err)
  if not observed.strip():r.update(box=None,must_read=False,glyph_height_px=None);results.append(r);continue
  x,y,X,Y=r['box'];crop=a[y:Y,x:X];yy,xx=np.where(crop<128)
  if not len(xx):raise ValueError('Missing text '+r['id'])
  r['box']=[int(x+xx.min()),int(y+yy.min()),int(x+xx.max()+1),int(y+yy.max()+1)]
  heights=[];xx=r['x'];face=G[r['face']]
  for ch in observed:
   adv=face['glyphs'][ch]['adv']*r['size']/face['units_per_em']
   if ch.isupper() or ch.isdigit() or ch=='?':
    lo=max(x,math.floor(xx));hi=min(X,math.ceil(xx+adv));ys=np.flatnonzero((a[y:Y,lo:hi]<128).any(1))
    if len(ys):heights.append(int(ys[-1]-ys[0]+1))
   xx+=adv
  r.update(must_read=bool(heights),glyph_height_px=min(heights) if heights else None)
  if heights and min(heights)<19:raise ValueError('Undersized letter '+r['id'])
  results.append(r)
 return results
