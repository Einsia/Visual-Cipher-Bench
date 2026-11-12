"""Recover source/destination incidence from PNG line geometry, without a route table."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

# Generic port locations and drawing area only; no edge assignments.
PANELS={'02.png':dict(xs=[540,820,1100,1380],top=1519,bottom=1605),
        '03.png':dict(xs=[225.25+178.5*i for i in range(8)],top=1724,bottom=1900)}

def read_wires(images,filename):
 panel=PANELS[filename];xs=panel['xs'];top=panel['top'];bottom=panel['bottom'];n=len(xs)
 a=np.asarray(Image.open(Path(images)/filename).convert('L'))
 # Stroke centers, not labels or render data, identify the horizontal routes.
 mask=a[top+3:bottom-3,:]<150
 rows=np.flatnonzero(mask.sum(1)>50);groups=[]
 for y in rows:
  if not groups or y-groups[-1][-1]>1:groups.append([int(y)])
  else:groups[-1].append(int(y))
 if len(groups)!=n:raise ValueError(f'{filename}: expected {n} distinct wire lanes, got {len(groups)}')
 edges=[];mapping=[None]*n
 for group in groups:
  y=top+3+int(round(sum(group)/len(group)))
  # Horizontal pixels are supported on both sides; discard isolated stems.
  row=a[y,:]<150
  horizontal=row.copy()
  horizontal[4:-4]&=row[:-8]&row[8:]
  xx=np.flatnonzero(horizontal[4:-4])+4
  if not len(xx):raise ValueError('Missing horizontal span')
  lo,hi=float(xx.min()-4),float(xx.max()+4)
  candidates=[]
  for src,sx in enumerate(xs):
   for dest,dx0 in enumerate(xs):
    dx=dx0+24
    err=abs(min(sx,dx)-lo)+abs(max(sx,dx)-hi)
    if err<6:candidates.append((src,dest))
  if len(candidates)!=1:raise ValueError(f'Ambiguous wire ends {lo,hi}: {candidates}')
  src,dest=candidates[0]
  if mapping[dest] is not None:raise ValueError('Duplicate destination wire')
  mapping[dest]=src+1;edges.append((src,dest,y))
 if sorted(mapping)!=list(range(1,n+1)):raise ValueError('Wire sources are not a bijection')
 # Rasterize just the recovered graph. A missing/extra/cross-connected stroke
 # must not be silently accepted. A two-pixel contour tolerance allows Cairo AA.
 expected=Image.new('L',(1700,2193),255);d=ImageDraw.Draw(expected)
 for src,dest,y in edges:
  points=[(xs[src],top),(xs[src],y),(xs[dest]+24,y),(xs[dest]+24,bottom)]
  d.line(points,fill=255,width=9);d.line(points,fill=85,width=3)
 y0,y1=top+3,bottom-3;x0,x1=int(min(xs)-8),int(max(xs)+33)
 actual=a[y0:y1,x0:x1]<150;pred=np.asarray(expected)[y0:y1,x0:x1]<150
 def expand(m):return np.asarray(Image.fromarray(np.uint8(m)*255).filter(ImageFilter.MaxFilter(5)))>0
 extra=actual&~expand(pred);missing=pred&~expand(actual)
 if extra.any() or missing.any():raise ValueError(f'{filename}: broken/unexpected wire ink: extra={extra.sum()}, missing={missing.sum()}')
 return dict(sources=mapping,edges=[dict(source=s+1,destination=t+1,lane_y=y) for s,t,y in edges],pixel_checked=True)
