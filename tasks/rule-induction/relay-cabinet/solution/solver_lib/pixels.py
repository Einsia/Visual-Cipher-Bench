"""PNG-only transcription of relay panels. Fixed locations encode layout only.
Templates contain individual cartridge glyphs, characters, rings and neutral frames;
no states, bridge sequences, labels, correct choices or answers are embedded.
"""
from pathlib import Path
import numpy as np
from PIL import Image
T=dict(np.load(Path(__file__).with_name('glyph_templates.npz')))
COLS=[76,600,1124,1648]
class PixelError(ValueError):pass
def need(ok,msg):
 if not ok:raise PixelError(msg)
class Page:
 def __init__(self,path,page):
  im=Image.open(path);need(im.size==(2193,1700),'Unexpected page size');need(not im.info,'Unexpected PNG metadata')
  rgb=np.array(im.convert('RGB'));need(np.max(np.ptp(rgb.astype(int),axis=2))==0,'Nonmonochrome image')
  self.a=rgb[:,:,0];decor=T[f'decor_{page}'];mask=decor<255
  need(np.max(np.abs(self.a[mask].astype(int)-decor[mask].astype(int)))<=1,'Frame or heading differs')
  self.cover=mask.copy();self.text=[{'role':'heading','text':'Relay Cabinet','min_glyph_height_px':47},{'role':'lede','text':'The night shift left these panels on the bench.','min_glyph_height_px':24}];self.parts=[];self.file=Path(path).name
 def region(self,b):
  x0,y0,x1,y1=map(int,b);self.cover[y0:y1,x0:x1]=1;return self.a[y0:y1,x0:x1]
 def compare(self,a,b):
  if a.shape!=b.shape:return 1.
  aa=a<200;bb=b<200;return np.count_nonzero(aa!=bb)/max(1,np.count_nonzero(aa|bb))
 def match(self,b,keys,tol=.03):
  arr=self.region(b);scores=sorted((self.compare(arr,T[k]),k) for k in keys)
  need(scores[0][0]<tol,f'Unknown/damaged glyph at {b}: {scores[:2]}');return scores[0][1]
 def char(self,b,alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?',level='body'):
  arr=self.region(b);yy,xx=np.where(arr<128);need(len(xx)>0,f'Missing character at {b}')
  tight=arr[yy.min():yy.max()+1,xx.min():xx.max()+1]
  scores=sorted((self.compare(tight,T[f'{level}_{c}']),c) for c in alphabet)
  need(scores[0][0]<.06,f'Unknown character at {b}: {scores[:2]}');ch=scores[0][1]
  self.text.append({'role':'label','text':ch,'box':b,'min_glyph_height_px':int(tight.shape[0])});return ch
 def line(self,x0,y0,x1,y1,limit=220):
  need(x0==x1 or y0==y1,'Nonorthogonal audit line')
  if x0==x1:
   arr=self.region([x0-2,y0-3,x0+3,y1+4]);good=(arr[3:-3,:]<limit).any(axis=1)
  else:
   arr=self.region([x0-3,y0-2,x1+4,y0+3]);good=(arr[:,3:-3]<limit).any(axis=0)
  need(good.all(),f'Discontinuous line {(x0,y0,x1,y1)}')
 def triple(self,x,y,gap=110,collars=True):
  st={'order':[],'faces':[None]*3,'records':[None]*3}
  for j in range(3):
   xx=x+j*gap
   if collars:
    k=self.match([xx-26,y-26,xx+69,y+27],[f'piece_{i}_{f}_{t}' for i in range(3) for f in range(2) for t in range(3)])
    _,i,f,t=k.split('_');i,f,t=map(int,[i,f,t]);st['records'][i]=t
   else:
    k=self.match([xx-26,y-26,xx+27,y+27],[f'body_{i}_{f}' for i in range(3) for f in range(2)])
    _,i,f=k.split('_');i,f=map(int,[i,f])
    need((self.region([xx+27,y-26,xx+69,y+27])==255).all(),'Candidate leaks a collar or tag')
   need(i not in st['order'],'Repeated cartridge identity')
   st['order'].append(i);st['faces'][i]=f
  if not collars:del st['records']
  self.parts.append({'kind':'triple','box':[x-26,y-26,x+2*gap+69,y+27],'observed':st});return st
 def bridges(self,x,y0,y1,ys):
  bridges=[];rings=[]
  for y in ys:
   scores=[]
   for lane in range(3):
    xx=x+110*lane;arr=self.a[y-18:y+19,xx-18:xx+19].copy();ref=T['ring'].copy()
    # Ignore only the side pixels where a horizontal stem can meet the ring.
    arr[16:21,:4]=255;arr[16:21,-4:]=255;ref[16:21,:4]=255;ref[16:21,-4:]=255
    scores.append(self.compare(arr,ref))
   lane=int(np.argmin(scores));need(scores[lane]<.035,f'Missing/malformed ring at y={y}: {scores}')
   xx=x+110*lane;self.region([xx-18,y-18,xx+19,y+19]);rings.append((lane,y))
   partners=[]
   for other in [lane-1,lane+1]:
    if not 0<=other<3:continue
    ox=x+110*other;lo=min(xx,ox)+(17 if ox>xx else 0);hi=max(xx,ox)-(17 if ox<xx else 0)
    arr=self.a[y-1:y+2,lo:hi+1]
    if (arr<128).any(axis=0).all():partners.append(other)
   need(len(partners)==1,f'Broken or ambiguous contact at {xx},{y}')
   other=partners[0];ox=x+110*other
   self.line(min(xx,ox)+(17 if ox>xx else 0),y,max(xx,ox)-(17 if ox<xx else 0),y)
   bridges.append([min(lane,other),int(lane>other)])
  for lane in range(3):
   xx=x+110*lane;pos=y0
   for ll,y in rings:
    if lane==ll:self.line(xx,pos,xx,y-17);pos=y+17
   self.line(xx,pos,xx,y1-11)
   arr=self.region([xx-6,y1-13,xx+7,y1+2]);mask=arr<210
   need(mask.sum()>25 and mask[:5].sum()>mask[-4:].sum(),'Missing/damaged downward arrow')
  self.parts.append({'kind':'bridges','box':[x-19,y0-2,x+239,y1+2],'observed':bridges});return bridges
 def finish(self):
  yy,xx=np.where((self.a<235)&~self.cover)
  need(len(xx)<=12,f'Unexpected ink: {len(xx)}, box={None if not len(xx) else [int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]}')
  return {'file':self.file,'text_regions':self.text,'parts':self.parts,'unexpected_ink_pixels':len(xx)}
def parse(images):
 p=Page(Path(images)/'01.png',1);ex=[]
 for left in COLS:
  base=270;ex.append({'initial':p.triple(left+78,base+105),'bridges':p.bridges(left+78,base+150,base+420,[base+200,base+280,base+360]),'final':p.triple(left+78,base+485)})
 left=76;base=960
 w={'initial':p.triple(left+78,base+105),'bridges':p.bridges(left+78,base+150,base+440,[base+180+70*k for k in range(4)]),'final':p.triple(left+78,base+505),'candidates':[]}
 checked=[]
 for j in range(3):
  y=base+145+175*j;ch=p.char([1048,y-18,1080,y+16]);w['candidates'].append({'letter':ch,'state':p.triple(1190,y,gap=240,collars=False)})
  b=[998,y-18,1033,y+15];arr=p.region(b)
  if (arr<128).any():
   need(p.compare(arr,T['tick'])<.03,'Malformed selection tick');checked.append(ch)
 w['letter']=p.char([749,base+319,790,base+352]);need(checked==[w['letter']],'Tick and filled answer do not agree');p.line(740,base+370,796,base+370)
 m1=p.finish()
 p=Page(Path(images)/'02.png',2);rows=[]
 for j in range(8):
  left=COLS[j%4];base=260+710*(j//4)
  n=p.char([left+34,base+19,left+64,base+49],alphabet='12345678',level='label');p.line(left+387,base+55,left+439,base+55)
  r={'number':int(n),'initial':p.triple(left+78,base+105),'bridges':p.bridges(left+78,base+150,base+414,[base+170+42*k for k in range(6)]),'candidates':[]}
  need(p.char([left+200,base+429,left+235,base+464],alphabet='?')=='?','Missing unknown')
  for k in range(3):
   y=base+515+60*k;r['candidates'].append({'letter':p.char([left+403,y-18,left+436,y+16]),'state':p.triple(left+78,y,collars=False)})
  rows.append(r)
 need([r['number'] for r in rows]==list(range(1,9)),'Question order differs');m2=p.finish()
 return {'examples':ex,'worked':w,'rows':rows},[m1,m2]
