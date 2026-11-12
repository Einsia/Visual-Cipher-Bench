"""Fixed-layout raster reader. No puzzle values or answers are embedded."""
from pathlib import Path
from collections import deque
import json
import numpy as np
from PIL import Image
from .discovery import search
from .model import predict_transition
from .interval_routes import solve as interval_search
HERE=Path(__file__).parent
class PixelError(ValueError):pass

def require(ok,reason):
 if not ok:raise PixelError(reason)

def dilate(a):
 p=np.pad(a,1);out=np.zeros_like(a)
 for dy in range(3):
  for dx in range(3):out|=p[dy:dy+a.shape[0],dx:dx+a.shape[1]]
 return out

def largest_component(a):
 seen=np.zeros_like(a);best=[]
 for y,x in zip(*np.where(a)):
  if seen[y,x]:continue
  todo=[(int(y),int(x))];seen[y,x]=True;component=[]
  while todo:
   yy,xx=todo.pop();component.append((yy,xx))
   for dy in [-1,0,1]:
    for dx in [-1,0,1]:
     j,k=yy+dy,xx+dx
     if 0<=j<a.shape[0] and 0<=k<a.shape[1] and a[j,k] and not seen[j,k]:seen[j,k]=True;todo.append((j,k))
  if len(component)>len(best):best=component
 out=np.zeros_like(a)
 for y,x in best:out[y,x]=True
 return out

def enclosed(a):
 h,w=a.shape; seen=np.zeros_like(a);q=deque()
 for y in range(h):
  for x in [0,w-1]:
   if not a[y,x]:seen[y,x]=True;q.append((y,x))
 for x in range(w):
  for y in [0,h-1]:
   if not a[y,x] and not seen[y,x]:seen[y,x]=True;q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:
   yy,xx=y+dy,x+dx
   if 0<=yy<h and 0<=xx<w and not a[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((yy,xx))
 return not seen[h//2,w//2]

def connected(ink,start,end,box):
 x0,y0,x1,y1=box;a=ink[y0:y1,x0:x1]
 def nearest(point):
  ys,xs=np.where(a);dist=(xs+x0-point[0])**2+(ys+y0-point[1])**2
  require(len(dist)>0 and dist.min()<=9,"Missing arrow endpoint")
  i=dist.argmin();return (int(ys[i]),int(xs[i]))
 seed=nearest(start);target=nearest(end);todo=[seed];seen={seed}
 while todo:
  y,x=todo.pop()
  if (y,x)==target:return True
  for dy in [-1,0,1]:
   for dx in [-1,0,1]:
    j,k=y+dy,x+dx
    if 0<=j<a.shape[0] and 0<=k<a.shape[1] and a[j,k] and (j,k) not in seen:seen.add((j,k));todo.append((j,k))
 return False

def read(images):
 paths=sorted(Path(images).glob('*.png'));require(len(paths)==1,'Expected one PNG page')
 im=Image.open(paths[0]);require(im.mode in ('RGB','RGBA'),'PNG is not RGB/RGBA')
 require(not im.info,'Unexpected PNG metadata')
 geo=json.loads((HERE/'geometry.json').read_text());require(list(im.size)==geo['size'],'Wrong canvas size')
 rgb=np.array(im.convert('RGB'));require(np.all(rgb.max(2)==rgb.min(2)),'Non-data colour introduced')
 ink=rgb.min(2)<128
 arrows=[((1365,426),(1429,426),(1362,419,1433,433)),((1365,1048),(1429,1048),(1362,1041,1433,1055)),((1280,730),(1280,745),(1274,727,1287,749)),((1280,1244),(1280,1259),(1274,1241,1287,1263)),((855,1568),(896,1578),(852,1564,901,1584)),((1240,1718),(1150,1980),(1147,1715,1244,1985))]
 for j,(start,end,box) in enumerate(arrows):require(connected(ink,start,end,box),f'Broken full arrow path {j+1}')
 structure=np.load(HERE/'structure.npz');diff=(ink&structure['mask'])^structure['ink']
 require(not diff.any(),f'Missing/extra structural ink outside glyph/counter regions: {int(diff.sum())} pixels')
 # The entire remaining canvas is covered, so off-grid extra cells/marks are not ignored.
 templates=json.loads((HERE/'glyphs.json').read_text());out={};bounds={};scores={}
 for f in geo['fields']:
  x0,y0,x1,y1=f['roi'];crop=ink[y0:y1,x0:x1];ys,xs=np.where(crop)
  require(len(xs)>0,f'Missing glyph field {f["id"]}')
  b=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];g=crop[b[1]:b[3],b[0]:b[2]]
  ranked=[]
  for key,variants in templates.items():
   level,ch=key.split('|',1)
   if level!=f['level']:continue
   best=1.0
   for v in variants:
    t=np.array(v,bool)
    if abs(g.shape[0]-t.shape[0])>2 or abs(g.shape[1]-t.shape[1])>2:continue
    z=np.array(Image.fromarray(g).resize((t.shape[1],t.shape[0]),Image.Resampling.NEAREST))
    score=float(np.logical_xor(z,t).sum()/np.logical_or(z,t).sum());best=min(score,best)
   ranked.append((best,ch))
  ranked.sort();best,ch=ranked[0]
  require(best<=.26,f'Unrecognized/damaged glyph field {f["id"]}: {ranked[:2]}')
  require(len(ranked)<2 or ranked[1][0]-best>.05,f'Ambiguous glyph field {f["id"]}')
  require(g.shape[0]>=19,f'Glyph below native size floor: {f["id"]}')
  out[f['id']]=ch;scores[f['id']]=best;bounds[f['id']]=[x0+b[0],y0+b[1],x0+b[2],y0+b[3]]
 shapes={k:largest_component(np.array(v,bool)) for k,v in json.loads((HERE/'contours.json').read_text()).items()};active={};covered=structure['mask'].copy()
 for f in geo['fields']:
  x0,y0,x1,y1=f['roi'];covered[y0:y1,x0:x1]=True
 for c in geo['counters']:
  x0,y0,x1,y1=c['roi'];a=ink[y0:y1,x0:x1].copy();a[11:46,10:47]=False
  a=largest_component(a)
  covered[y0:y1,x0:x1]|=a
  require(enclosed(a),f'Missing/open counter outline field {c["field"]}')
  fits=[]
  for kind,t in shapes.items():
   extra=(a&~dilate(t)).sum();missing=(t&~dilate(a)).sum()
   if extra<=3 and missing<=3:fits.append(kind)
  require(len(fits)==1,f'Extra/ambiguous/malformed counter outline {c["field"]}: {fits}')
  active[c['field']]=fits[0]=='circle'
 require(not (ink&~covered).any(),'Extra ink/outline inside counter regions outside recognized symbols')
 def val(i,alphabet=None):
  v=out[i]
  require(alphabet is None or v in alphabet,f'Invalid datum {i}: {v}')
  return v
 def number(i):
  v=val(i);require(v.isdigit(),f'Non-numeric field {i}');return int(v)
 demos=[]
 for base in [2,56]:
  require(val(base)=='t','Missing time label')
  times=[number(base+1+j) for j in range(3)]
  require(times[0]==0 and times[0]<times[1]<times[2]<=100,'Invalid snapshot times')
  states=[]
  for j in range(3):
   letters=[];counts=[];p=[]
   for r in range(6):
    require(number(base+4+7*r)==r+1,'Row labels are not consecutive')
    li=base+5+7*r+2*j;ci=li+1
    letters.append(val(li,'ABCDEFGHIJKLMNOPQRSTUVWXYZ'));counts.append(number(ci))
    if active[ci]:p.append(r)
   require(len(p)==1,'Each snapshot needs exactly one activity circle')
   states.append(dict(letters=''.join(letters),counts=counts,active=p[0]))
  slots=[number(base+46+2*j) for j in range(4)];result=''.join(val(base+47+2*j,'ABCDEFGHIJKLMNOPQRSTUVWXYZ') for j in range(4))
  require(all(1<=s<=6 for s in slots),'Invalid example extraction index')
  require(''.join(states[-1]['letters'][s-1] for s in slots)==result,'Example extraction does not match terminal state')
  require(states[-1]['counts'][states[-1]['active']]==0,'Pause column does not mark zero arrival')
  demos.append(dict(**states[0],times=times,states=states,read_slots=slots,result=result))
 letters=[];counts=[];p=[]
 for r in range(12):
  letters.append(val(110+3*r,'ABCDEFGHIJKLMNOPQRSTUVWXYZ'));counts.append(number(111+3*r))
  require(number(112+3*r)==r+1,'Ring labels are not consecutive clockwise')
  if active[111+3*r]:p.append(r)
 require(len(p)==1,'Ring needs exactly one activity circle')
 require(val(146)=='?','Unknown target missing')
 slots=[number(147+j) for j in range(8)];require(all(1<=s<=12 for s in slots),'Invalid output index')
 question=dict(letters=''.join(letters),counts=counts,active=p[0],read_slots=slots)
 return dict(demonstrations=demos,question=question,glyph_boxes=bounds,max_ocr_error=max(scores.values()),min_glyph_height_px=min(b[3]-b[1] for b in bounds.values()),structure_checked_pixels=int(structure['mask'].sum()),counter_outlines_checked=len(active),connected_arrow_paths=6)

def compute(images):
 data=read(images);found=search(data['demonstrations'])
 require(found['semantic_classes']==1,f'Rule evidence leaves {found["semantic_classes"]} semantic classes')
 q=data['question'];answers=set();runs=[]
 for rule in found['survivors']:
  counts=q['counts'][:];cards=list(q['letters']);p=q['active'];trace=[]
  for t in range(sum(counts)+1):
   trace.append(dict(t=t,letters=''.join(cards),counts=counts[:],active=p))
   if counts[p]==0:break
   counts,cards,p=predict_transition(rule,counts,cards,p,q['counts'])
  else:raise PixelError('Failed strict-decrease termination bound')
  answers.add(''.join(cards[s-1] for s in q['read_slots']));runs.append(trace)
 require(len(answers)==1,'Surviving interpretations predict different answers')
 return dict(answer=answers.pop(),parsed=data,rule_search=found,trace=runs[0],equivalent_trace_match=all(x==runs[0] for x in runs),interval_evidence=interval_search(data['demonstrations']))
