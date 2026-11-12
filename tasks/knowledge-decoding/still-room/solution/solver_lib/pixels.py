"""Pixel-only transcription.
The atlases contain isolated glyphs/objects.
"""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image,ImageFilter
P=Path(__file__).resolve().parent

def components(mask):
 h,w=mask.shape;seen=np.zeros_like(mask);out=[]
 for sy,sx in zip(*np.nonzero(mask)):
  if seen[sy,sx]:continue
  stack=[(int(sx),int(sy))];seen[sy,sx]=1
  x0=x1=int(sx);y0=y1=int(sy);area=0
  while stack:
   x,y=stack.pop();area+=1;x0=min(x0,x);x1=max(x1,x);y0=min(y0,y);y1=max(y1,y)
   for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if 0<=xx<w and 0<=yy<h and mask[yy,xx] and not seen[yy,xx]:
     seen[yy,xx]=1;stack.append((xx,yy))
  out.append((x0,y0,x1+1,y1+1,area))
 return out

def blur(a):return np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(1)),dtype=np.float32)/255

def read_cards(a):
 frames=[b for b in components((a>=210)&(a<=225)) if 535<=b[2]-b[0]<=545 and 445<=b[3]-b[1]<=455]
 frames.sort(key=lambda b:(b[1],b[0]))
 if len(frames)!=19:raise ValueError(f'Expected 19 picture frames, found {len(frames)}')
 atlas=np.load(P/'object_atlas.npz',allow_pickle=False);names=list(atlas['names'])
 outer=np.array([blur(t) for t in atlas['outer']]);inner=np.array([blur(t) for t in atlas['inner']])
 mask=np.ones((390,390),bool);mask[146:280,130:260]=False
 result=[]
 for x0,y0,x1,y1,_ in frames:
  # Fixed pictogram field margins are a layout convention, not a transcription.
  x=int(round((x0+x1-540)/2));y=int(round((y0+y1-450)/2))
  ox=x+75;oy=y+30
  observed=blur(a[oy:oy+390,ox:ox+390])
  score=np.mean((outer[:,mask]-observed[mask])**2,axis=1);oi=int(np.argmin(score))
  ix=int(round(ox+136.5));iy=int(round(oy+152.75))
  observed=blur(a[iy:iy+117,ix:ix+117]);score2=np.mean((inner-observed)**2,axis=(1,2));ii=int(np.argmin(score2))
  if score[oi]>.03 or score2[ii]>.05:raise ValueError('unrecognized picture')
  result.append({'outer':str(names[oi]),'inner':str(names[ii]),'outer_error':float(score[oi]),'inner_error':float(score2[ii])})
 return result

GLYPHS=None
def recognize_text(crop,size):
 global GLYPHS
 if GLYPHS is None:GLYPHS=np.load(P/'glyph_atlas.npz',allow_pickle=False)
 mask=crop<128;columns=np.any(mask,axis=0);runs=[];i=0
 while i<len(columns):
  if not columns[i]:i+=1;continue
  j=i+1
  while j<len(columns) and columns[j]:j+=1
  runs.append((i,j));i=j
 out=''
 for i,j in runs:
  part=mask[:,i:j];ys=np.where(part.any(axis=1))[0]
  if len(ys)<8:continue
  part=part[ys[0]:ys[-1]+1]
  best=(99,None)
  for key in GLYPHS.files:
   if not key.startswith(str(size)+'_'):continue
   target=GLYPHS[key]<128
   if abs(target.shape[1]-part.shape[1])>8 or abs(target.shape[0]-part.shape[0])>5:continue
   norm=np.asarray(Image.fromarray(part).resize((target.shape[1],target.shape[0]),Image.Resampling.NEAREST))
   error=float(np.mean(norm!=target))
   if error<best[0]:best=(error,key.split('_')[1])
  if best[1] is None or best[0]>.35:raise ValueError(f'Unrecognized glyph {part.shape}, score {best}')
  out+=best[1]
 return out

def read_network(a):
 # Centre marks are solid grey disks; circuit strokes use a different grey.
 hubs=[]
 for x0,y0,x1,y1,area in components((a>=65)&(a<=110)):
  if 10<=x1-x0<=14 and 10<=y1-y0<=14 and 70<=area<=140:
   hubs.append(((x0+x1-1)/2,(y0+y1-1)/2))
 hubs.sort(key=lambda p:(round(p[1]/10),p[0]))
 if len(hubs)!=19:raise ValueError(f'Expected 19 circuit centres, found {len(hubs)}')
 nodes=[]
 for x0,y0,x1,y1,area in components(a<64):
  if 62<=x1-x0<=68 and 62<=y1-y0<=68 and 450<=area<=1000:
   nodes.append(((x0+x1-1)/2,(y0+y1-1)/2))
 nodes.sort(key=lambda p:(round(p[1]/4),p[0]))
 loops=[]
 for hx,hy in hubs:
  members=[i for i,(x,y) in enumerate(nodes) if 175<math.hypot(x-hx,y-hy)<240]
  members.sort(key=lambda i:math.atan2(nodes[i][1]-hy,nodes[i][0]-hx)%(2*math.pi))
  if len(members) not in (7,8):raise ValueError(f'Circuit has {len(members)} cells')
  loops.append(members)
 givens={};extraction={}
 for c,(x,y) in enumerate(nodes):
  xx,yy=int(round(x)),int(round(y));crop=a[yy-27:yy+28,xx-28:xx+29].copy()
  gy,gx=np.ogrid[-27:28,-28:29];crop[gx*gx+gy*gy>28*28]=255
  s=recognize_text(crop,52)
  if s:
   if len(s)!=1:raise ValueError('non-single given')
   givens[c]=s
 numeric=[]
 for x0,y0,x1,y1,area in components((a>=80)&(a<=90)):
  if area>=65 and 24<=y1-y0<=34:numeric.append([x0,y0,x1,y1])
 groups=[b.copy() for b in numeric]
 changed=True
 while changed:
  changed=False
  for i,g in enumerate(groups):
   for j,b in enumerate(groups[i+1:],i+1):
    gap=max(g[0],b[0])-min(g[2],b[2])
    if abs((g[1]+g[3]-b[1]-b[3])/2)<3 and 0<=gap<=16:
     groups[i]=[min(g[0],b[0]),min(g[1],b[1]),max(g[2],b[2]),max(g[3],b[3])]
     groups.pop(j);changed=True;break
   if changed:break
 # Associate the visible number box with the nearest circle boundary.
 associations=[]
 for x0,y0,x1,y1 in groups:
  crop=a[y0:y1,x0:x1].copy();crop[(crop<80)|(crop>90)]=255
  label=recognize_text(crop,42);n=int(label)
  distances=sorted((math.hypot(max(x0-x,0,x-x1),max(y0-y,0,y-y1))-32.5,c)
                   for c,(x,y) in enumerate(nodes))
  (own,c),(other,other_c)=distances[:2]
  if not 0<own<40 or other<1.8*own:
   raise ValueError(f'Number {label} has ambiguous cell ownership: {own:.2f}, {other:.2f}')
  if n in extraction:raise ValueError(f'duplicate extraction index {n}')
  extraction[n]=c
  associations.append({'number':n,'bbox':[x0,y0,x1,y1],'cell':c,
                       'gap':own,'nearest_other_cell':other_c,
                       'nearest_other_gap':other,'ratio':other/own})
 if sorted(extraction)!=list(range(1,20)):raise ValueError(f'Bad extraction labels: {sorted(extraction)}')
 return {'loops':loops,'givens':givens,'extraction':[extraction[n] for n in range(1,20)],'centres':hubs,'cells':nodes,
         'label_associations':sorted(associations,key=lambda a:a['number'])}

def read(images):
 paths=sorted(Path(images).glob('*.png'))
 if len(paths)!=2:raise ValueError('Two PNG pages required')
 arrays=[np.asarray(Image.open(p).convert('L')) for p in paths]
 # Page with card borders identifies itself; file names carry no data.
 if np.sum((arrays[0]>=215)&(arrays[0]<=219))<np.sum((arrays[1]>=215)&(arrays[1]<=219)):arrays.reverse()
 return read_cards(arrays[0]),read_network(arrays[1])
