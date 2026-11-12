"""Native-pixel recognition. Class templates are single objects/letters."""
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
class InvalidPixels(ValueError):pass

def parse(path):
 image=Image.open(path)
 if image.size!=(1700,2193) or image.mode not in ('RGB','RGBA'):raise InvalidPixels('Unexpected canvas/mode')
 rgb=np.array(image.convert('RGB'))
 if np.any(rgb.max(2)-rgb.min(2)>8):raise InvalidPixels('Unexpected semantic colour')
 a=np.array(image.convert('L'));covered=np.zeros(a.shape,bool);templates=np.load(ROOT/'templates.npz');records=[]
 def claim(box):
  x,y,r,b=box;covered[max(0,y-1):b+1,max(0,x-1):r+1]=True
 def patch(box):
  x,y,r,b=box;return a[y:b,x:r]
 def distance(x,y,mask=None):
  if x.shape!=y.shape:return 10
  xx=x.astype(float);yy=y.astype(float)
  if mask is not None:xx=xx[mask];yy=yy[mask]
  return float(np.abs(xx-yy).sum()/max(1,np.maximum(255-xx,255-yy).sum()))
 def fixed(name,box,tolerance=.003):
  p=patch(box);err=distance(p,templates[name]);claim(box)
  if err>tolerance:raise InvalidPixels(f'{name} is incomplete or altered at {box}: {err:.4f}')
  records.append({'kind':name,'box':box,'error':err})
 def icon(x,y):
  box=[x-95,y-95,x+95,y+95];p=patch(box);mask=np.ones(p.shape,bool)
  # Neighbouring exchange-arrow ends fall into narrow lateral strips, checked separately below.
  mask[:4]=False;mask[85:133,:12]=False;mask[85:133,-12:]=False
  ranked=sorted((distance(p,templates[k],mask),k[5:]) for k in templates.files if k.startswith('icon_'))
  err,name=ranked[0]
  if err>.008:raise InvalidPixels(f'Missing, extra or unrecognized object at {box}; best {name}: {err:.4f}')
  covered[y-95:y+95,x-95:x+95]|=mask;records.append({'kind':'object','name':name,'box':box,'error':err});return name.upper()
 def mode(x,y):
  box=[x-28,y-85,x+28,y-29];p=patch(box)
  ranked=sorted((distance(p,templates['marker_'+n]),n) for n in ('pencil','speaker'))
  err,n=ranked[0]
  if err>.005:raise InvalidPixels(f'Missing or damaged mode at {box}')
  claim(box);records.append({'kind':'mode','name':n,'box':box,'error':err});return n
 def exchange(x,y):fixed('exchange',[x-41,y-10,x+41,y+40])
 def panel(x,y):return [mode(x,y),icon(x-125,y),icon(x+125,y)]
 def normal(p):return np.array(Image.fromarray(p).resize((32,48),Image.Resampling.BILINEAR))
 def text(box):
  p=patch(box);m=p<128;on=m.any(0);runs=[];st=None
  for i,v in enumerate(np.r_[on,False]):
   if v and st is None:st=i
   if not v and st is not None:runs.append((st,i));st=None
  out='';heights=[];glyph_boxes=[]
  for l,r in runs:
   ys=np.where(m[:,l:r].any(1))[0];q=p[ys[0]:ys[-1]+1,l:r];n=normal(q)
   byletter={}
   for k in templates.files:
    if k.startswith('glyph_'):
     ch=k.split('_')[1];e=distance(n,normal(templates[k]));byletter[ch]=min(e,byletter.get(ch,99))
   ranked=sorted((v,k) for k,v in byletter.items());e,ch=ranked[0]
   if e>.22 or (len(ranked)>1 and ranked[1][0]-e<.025):raise InvalidPixels(f'Unreadable/ambiguous glyph in {box}: {ranked[:2]}')
   out+=ch;heights.append(len(ys));glyph_boxes.append([box[0]+l,box[1]+int(ys[0]),box[0]+r,box[1]+int(ys[-1]+1)])
  if not out or min(heights)<19:raise InvalidPixels(f'Empty or undersized text at {box}')
  claim(box);records.append({'kind':'text','text':out,'box':box,'glyph_boxes':glyph_boxes,'min_cap_height':min(heights)});return out
 def route(points):
  xs=[p[0] for p in points];ys=[p[1] for p in points];box=[min(xs)-11,min(ys)-11,max(xs)+12,max(ys)+12]
  x0,y0,x1,y1=box;p=patch(box);m=p<128;corridor=np.zeros(m.shape,bool)
  for (x,y),(u,v) in zip(points,points[1:]):
   if x!=u and y!=v:raise InvalidPixels('Non-axis route')
   corridor[min(y,v)-y0-3:max(y,v)-y0+4,min(x,u)-x0-3:max(x,u)-x0+4]=True
  tx,ty=points[-1];sx,sy=points[-2]
  if tx>sx:
   hb=[tx-20,ty-10,tx+2,ty+10];head=templates['head_right']
  elif tx<sx:
   hb=[tx-2,ty-10,tx+20,ty+10];head=np.fliplr(templates['head_right'])
  elif ty>sy:
   hb=[tx-10,ty-20,tx+10,ty+2];head=templates['head_down']
  else:raise InvalidPixels('Unsupported route direction')
  # Subpixel alignment of mirror rasterization may shift a boundary; connectivity remains exact.
  h=patch(hb);best=min(distance(h,np.roll(head,shift,axis=1 if tx!=sx else 0)) for shift in (-1,0,1))
  if best>.14:raise InvalidPixels(f'Arrowhead missing or reversed at {hb}: {best}')
  hx,hy,hr,hb1=hb;corridor[hy-y0:hb1-y0,hx-x0:hr-x0]=True
  allowed=m&corridor
  sx,sy=points[0];starts=[(y,x) for y in range(sy-y0-1,sy-y0+2) for x in range(sx-x0-1,sx-x0+2) if allowed[y,x]]
  seen=set(starts);q=deque(starts)
  while q:
   y,x=q.popleft()
   for dy in (-1,0,1):
    for dx in (-1,0,1):
     v,u=y+dy,x+dx
     if 0<=v<allowed.shape[0] and 0<=u<allowed.shape[1] and allowed[v,u] and (v,u) not in seen:seen.add((v,u));q.append((v,u))
  if not any(abs(x-(tx-x0))<=1 and abs(y-(ty-y0))<=1 for y,x in seen):raise InvalidPixels(f'Disconnected route (head retained): {points}')
  if int(allowed.sum())!=len(seen):raise InvalidPixels(f'Detached ink along route {points}')
  # Reject additions anywhere in the corridor, rather than only sampling a centerline.
  if len(points)==2 and np.any(m&~corridor&~covered[y0:y1,x0:x1]):raise InvalidPixels(f'Extra ink adjacent to connector {points}')
  covered[y0:y1,x0:x1]|=corridor;records.append({'kind':'connected_directed_route','points':points,'ink_pixels':len(seen)})
 fixed('header',[130,120,1070,315])
 examples=[]
 for y in [430,630,830,1030]:
  examples.append(panel(850,y));exchange(850,y)
 before1=text([150,400,435,455]);after1=text([1190,600,1430,655]);before2=text([215,800,380,855]);after2=text([1210,1000,1410,1055])
 fixed('book',[1443,990,1557,1066])
 for y in [430,830]:route([(455,y),(610,y)])
 for y in [630,1030]:route([(1090,y),(1160,y)])
 route([(1090,430),(1310,430),(1310,535),(295,535),(295,630),(610,630)])
 route([(1090,830),(1310,830),(1310,935),(295,935),(295,1030),(610,1030)])
 start=text([280,1155,430,1210])
 centers=[(356,1340),(850,1340),(1344,1340),(1344,1610),(850,1610),(356,1610),(356,1880)]
 ops=[]
 for x,y in centers:ops.append(panel(x,y));exchange(x,y)
 routes=[[(356,1220),(356,1240)],[(586,1340),(620,1340)],[(1080,1340),(1114,1340)],[(1344,1440),(1344,1510)],[(1114,1610),(1080,1610)],[(620,1610),(586,1610)],[(356,1710),(356,1780)],[(586,1880),(690,1880)]]
 for points in routes:route(points)
 fixed('book',[1093,1840,1207,1916])
 box=[695,1891,1080,1901];p=patch(box);mask=p<128;on=mask.any(0);runs=[];st=None
 for i,v in enumerate(np.r_[on,False]):
  if v and st is None:st=i
  if not v and st is not None:runs.append((st,i));st=None
 if not runs:raise InvalidPixels('No answer slots')
 for l,r in runs:
  if not 23<=r-l<=26 or not 1<=int(mask[:,l:r].any(1).sum())<=3:raise InvalidPixels('Malformed answer slot')
 claim(box);records.append({'kind':'answer_slots','count':len(runs),'box':box})
 # The only nonsemantic line is a thin gray divider.
 div=[135,1128,1565,1132];claim(div)
 residual=(a<245)&~covered
 if residual.any():
  yy,xx=np.where(residual);raise InvalidPixels(f'Unrecognized extra ink: {len(xx)} pixels, bounds {[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]}')
 return {'start':start,'operators':ops,'examples':[{'before':before1,'operators':examples[:2],'after':after1},{'before':before2,'operators':examples[2:],'after':after2}],'answer_slots':len(runs),'records':records,'size':list(image.size),'metadata':dict(image.info)}
