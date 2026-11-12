"""PNG-only parser. Static coordinates are layout knowledge, never state data."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).parent

def tight(a,box,threshold=100):
 x,y,u,v=map(int,box);ys,xs=np.where(a[y:v,x:u]<threshold)
 if not len(xs):raise ValueError('Missing ink at '+str(box))
 return [int(x+xs.min()),int(y+ys.min()),int(x+xs.max()+1),int(y+ys.max()+1)]
def mask(a,b):
 x,y,u,v=map(int,b);return a[y:v,x:u]<100
def groups(z):
 q=np.where(z)[0];return [g for g in np.split(q,np.where(np.diff(q)>1)[0]+1) if len(g)]
def read_text(a,box,templates):
 b=tight(a,box);m=mask(a,b);out='';cb=[]
 for g in groups(m.any(axis=0)):
  bb=tight(a,[b[0]+int(g[0]),b[1],b[0]+int(g[-1])+1,b[3]]);z=mask(a,bb);matches=[]
  for ch,variants in templates.items():
   for variant in variants:
    t=np.array(variant,bool)
    if t.shape==z.shape:matches.append((float(np.mean(z!=t)),ch))
  if not matches or min(matches)[0]>.10:raise ValueError('Unrecognized glyph '+str(bb))
  out+=min(matches)[1];cb.append(bb)
 return out,b,min(q[3]-q[1] for q in cb)
def locations():
 gs=[];ts=[]
 def tx(f,key,x,y):ts.append(dict(image=f,key=key,search_box=[x-22,y-32,x+22,y+5]))
 def fig(f,key,cx,cy):
  gs.append(dict(id=key,image=f,center=[cx,cy],box=[cx-84,cy-84,cx+84,cy+84]));tx(f,key,cx,cy-131)
 for j in range(3):
  x=90+770*j
  for key,cx,cy in [('plate_before',x+170,590),('stamp_before',x+510,590),('plate_after',x+170,1100),('stamp_after',x+510,1100)]:fig('01.png',f'worked{j+1}.{key}',cx,cy)
 tx('01.png','worked_letter',1800,1290)
 for i in range(8):
  x=70+(i%4)*580;y=295+(i//4)*710
  for key,cx,cy in [('plate',x+260,y+166),('A',x+130,y+418),('B',x+390,y+418)]:fig('02.png',f'target{i+1}.{key}',cx,cy)
  for j in range(3):tx('02.png',f'target{i+1}.sequence{j}',x+125+j*90,y+590)
  tx('02.png',f'target{i+1}.index',x+42,y+631)
  # Crop inside the unknown frame, excluding the border.
  ts.append(dict(image='02.png',key=f'target{i+1}.unknown',search_box=[x+378,y+551,x+428,y+601]))
 return gs,ts
def line(a,p,q,threshold=190):
 x,y=p;u,v=q
 if y==v:ok=(a[y-1:y+2,min(x,u):max(x,u)+1]<threshold).any(axis=0).all()
 elif x==u:ok=(a[min(y,v):max(y,v)+1,x-1:x+2]<threshold).any(axis=1).all()
 else:raise ValueError('Nonaxial line')
 if not ok:raise ValueError(f'Broken connection {p}->{q}')
def arrow(a,x,y,u,v):
 line(a,(x,y),(u,v),100)
 if y==v:
  m=a[v-5:v+6,u-10:u+1]<100
  assert m[:3].any() and m[-3:].any(),'Arrow head missing'
 else:
  m=a[v-18:v+1,u-7:u+8]<100
  assert m[:,:5].any() and m[:,-5:].any(),'Arrow head missing'
def symbol(a,cx,cy,templates):
 box=[cx-10,cy-10,cx+11,cy+11];m=mask(a,box)
 yy,xx=np.ogrid[-10:11,-10:11];m &= xx*xx+yy*yy<=49
 if not m.any():return '0'
 yy,xx=np.where(m);b=[cx-10+int(xx.min()),cy-10+int(yy.min()),cx-9+int(xx.max()),cy-9+int(yy.max())]
 m=m[yy.min():yy.max()+1,xx.min():xx.max()+1];hits=[]
 for k,t in templates.items():
  t=np.array(t,bool)
  if t.shape==m.shape and np.mean(m!=t)<.035:hits.append(k)
 if len(hits)!=1:raise ValueError('Malformed mark '+str(b))
 if abs((b[0]+b[2])/2-cx)>.6 or abs((b[1]+b[3])/2-cy)>.6:raise ValueError('Off-centre mark')
 return hits[0]
def read(images):
 templates=json.loads((HERE/'glyph_templates.json').read_text());a={};meta={}
 for f in ['01.png','02.png']:
  im=Image.open(Path(images)/f)
  if im.size!=(2400,1800) or im.mode not in ['RGB','RGBA']:raise ValueError('Unexpected canvas')
  if im.info:raise ValueError('Unexpected PNG metadata')
  rgb=np.array(im.convert('RGB'))
  if (rgb.max(axis=2)!=rgb.min(axis=2)).any():raise ValueError('Nonmonochrome image')
  a[f]=np.array(im.convert('L'));meta[f]=dict(size=list(im.size),mode=im.mode)
 gs,ts=locations();gd={};td={}
 for g in gs:
  cx,cy=g['center'];z=a[g['image']]
  # Verify both housing axes and registration notch; inspect all 49 actual cells.
  for dx,dy in [(-115,0),(115,0),(0,-115),(0,115)]:
   if not (z[cy+dy-2:cy+dy+3,cx+dx-2:cx+dx+3]<100).any():raise ValueError('Missing dial housing')
  vals=[symbol(z,cx+(c-3)*24,cy+(r-3)*24,templates['symbols']) for r in range(7) for c in range(7)]
  gd[g['id']]=dict(g,grid=[''.join(vals[j:j+7]) for j in range(0,49,7)])
 for t in ts:
  txt,b,h=read_text(a[t['image']],t['search_box'],templates['chars'])
  if h<19.8:raise ValueError('Required character below 1.1 percent of short side')
  td[t['key']]=dict(text=txt,box=b,glyph_height_px=h,image=t['image'])
 for j in range(3):
  x=90+770*j;z=a['01.png'];arrow(z,x+340,790,x+340,860)
  for yy,sg in [(755,-1),(900,1)]:
   line(z,(x+170,yy+sg*16),(x+170,yy));line(z,(x+170,yy),(x+510,yy));line(z,(x+510,yy),(x+510,yy+sg*16))
 for i in range(8):
  x=70+(i%4)*580;y=295+(i//4)*710;z=a['02.png']
  for j in range(3):arrow(z,x+151+j*90,y+578,x+184+j*90,y+578)
  line(z,(x+85,y+635),(x+445,y+635),100)
  for p,q in [((x+373,y+546),(x+433,y+546)),((x+373,y+606),(x+433,y+606)),((x+373,y+546),(x+373,y+606)),((x+433,y+546),(x+433,y+606))]:line(z,p,q,100)
  assert td[f'target{i+1}.index']['text']==str(i+1)
  assert td[f'target{i+1}.unknown']['text']=='?'
  assert [td[f'target{i+1}.{k}']['text'] for k in ['plate','A','B']]==['P','A','B']
 want=[['P0','A0','P1','A1'],['P1','B0','P2','B1'],['P2','A1','P3','A2']]
 for j,w in enumerate(want,1):assert [td[f'worked{j}.{k}']['text'] for k in ['plate_before','stamp_before','plate_after','stamp_after']]==w
 assert [symbol(a['01.png'],x,174,templates['symbols']) for x in [1850,2010,2170]]==['0','1','2']
 for x,u in [(1885,1975),(2045,2135)]:arrow(a['01.png'],x,174,u,174)
 for p,q in [((2170,204),(2170,219)),((2170,219),(1850,219)),((1850,219),(1850,204))]:line(a['01.png'],p,q,100)
 return dict(grids=gd,text=td,metadata=meta)
