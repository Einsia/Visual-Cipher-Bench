"""Validate complete native-pixel contours and paths, including unexpected ink.

The resource contains only non-text drawing geometry. Numeric values are read by
text_reader; glyph values and puzzle solutions are never stored here.
"""
from pathlib import Path
import json,math
from collections import deque
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
G=json.loads((ROOT/'geometry.json').read_text())

def path_present(mask,a,b,width):
 x0=max(0,math.floor(min(a[0],b[0])-width-3));x1=min(mask.shape[1],math.ceil(max(a[0],b[0])+width+4))
 y0=max(0,math.floor(min(a[1],b[1])-width-3));y1=min(mask.shape[0],math.ceil(max(a[1],b[1])+width+4))
 yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
 dx=b[0]-a[0];dy=b[1]-a[1];l2=dx*dx+dy*dy
 if l2==0:raise ValueError('zero length path')
 u=np.clip(((xx-a[0])*dx+(yy-a[1])*dy)/l2,0,1)
 dist=(xx-(a[0]+u*dx))**2+(yy-(a[1]+u*dy))**2
 corridor=dist<=(width/2+1.1)**2
 actual=mask[y0:y1,x0:x1]&corridor
 st=np.argwhere(actual&((xx-a[0])**2+(yy-a[1])**2<=2.3**2))
 end=actual&((xx-b[0])**2+(yy-b[1])**2<=2.3**2)
 if not len(st) or not end.any():return False
 seen=np.zeros_like(actual);q=deque()
 for y,x in st:seen[y,x]=1;q.append((int(y),int(x)))
 while q:
  y,x=q.popleft()
  if end[y,x]:return True
  for dy in (-1,0,1):
   for dx in (-1,0,1):
    Y,X=y+dy,x+dx
    if 0<=Y<actual.shape[0] and 0<=X<actual.shape[1] and actual[Y,X] and not seen[Y,X]:seen[Y,X]=1;q.append((Y,X))
 return False

def inspect(images,regions,check_extra=True):
 reports=[]
 for filename,primitives in G.items():
  im=Image.open(Path(images)/filename).convert('RGB');arr=np.asarray(im)
  if im.size!=(1700,2193):raise ValueError('Unexpected canvas '+filename)
  mask=arr.min(2)<128
  allowed=Image.new('1',im.size);draw=ImageDraw.Draw(allowed)
  count={};paths=0
  for i,g in enumerate(primitives):
   typ=g['type'];count[typ]=count.get(typ,0)+1;sw=float(g.get('stroke-width',2.5));wide=math.ceil(sw+4)
   if typ=='line':
    a=tuple(float(g[k]) for k in ('x1','y1'));b=tuple(float(g[k]) for k in ('x2','y2'))
    if not path_present(mask,a,b,sw):raise ValueError(f'{filename}: disconnected line {i}: {a} -> {b}')
    draw.line([a,b],fill=1,width=wide);paths+=1
    for x,y in (a,b):draw.ellipse((x-wide/2,y-wide/2,x+wide/2,y+wide/2),fill=1)
   elif typ=='rect':
    x,y,w,h=[float(g[k]) for k in ('x','y','width','height')]
    corners=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
    for a,b in zip(corners,corners[1:]+corners[:1]):
     if not path_present(mask,a,b,sw):raise ValueError(f'{filename}: incomplete rectangle {i}: {a} -> {b}')
     draw.line([a,b],fill=1,width=wide);paths+=1
    for x,y in corners:draw.ellipse((x-wide/2,y-wide/2,x+wide/2,y+wide/2),fill=1)
   elif typ=='circle':
    cx,cy,r=[float(g[k]) for k in ('cx','cy','r')]
    # Each short arc must have a connected path, ensuring no absent rim segment.
    angles=np.linspace(0,2*math.pi,49)
    points=[(cx+r*math.cos(t),cy+r*math.sin(t)) for t in angles]
    for a,b in zip(points,points[1:]):
     if not path_present(mask,a,b,sw):raise ValueError(f'{filename}: incomplete circle {i}: {a} -> {b}')
     paths+=1
    draw.ellipse((cx-r-3,cy-r-3,cx+r+3,cy+r+3),outline=1,width=wide)
   else:
    pts=[tuple(map(float,p.split(','))) for p in g['points'].split()]
    inner=Image.new('1',im.size);ImageDraw.Draw(inner).polygon(pts,fill=1);m=np.asarray(inner)
    # Require arrowhead ink, independently of shaft continuity.
    if np.count_nonzero(mask&m)<.65*np.count_nonzero(m):raise ValueError(f'{filename}: missing arrowhead {i}')
    draw.polygon(pts,fill=1);draw.line(pts+[pts[0]],fill=1,width=5)
  for r in regions:
   if r['image']!=filename or r['box'] is None:continue
   x,y,X,Y=r['box'];draw.rectangle((x-1,y-1,X,Y),fill=1)
  # Route topology is recovered independently from pixels, never this resource.
  if filename in ('02.png','03.png'):
   from .wires import PANELS,read_wires
   panel=PANELS[filename];read_wires(images,filename)
   draw.rectangle((min(panel['xs'])-6,panel['top']-1,max(panel['xs'])+30,panel['bottom']+1),fill=1)
  extra=mask&~np.asarray(allowed)
  if check_extra and extra.any():
   ys,xs=np.where(extra);raise ValueError(f'{filename}: unexplained ink {len(xs)} px, bounds {[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]}')
  reports.append(dict(image=filename,primitive_counts=count,continuous_paths_checked=paths,unexplained_ink=0 if check_extra else None,color_pixel_ratio=float(np.mean(arr.max(2)!=arr.min(2)))))
 return reports
