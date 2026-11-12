"""Raster-only recognition. Layout coordinates contain no shape, digit or answer data."""
from pathlib import Path
from PIL import Image
import numpy as np,json

class PixelError(ValueError):pass
T={k:[np.array([[c=='1' for c in row] for row in v],bool) for v in vs] for k,vs in json.loads((Path(__file__).parent/'glyph_templates.json').read_text()).items()}

def require(ok,msg):
 if not ok:raise PixelError(msg)

def resize(a):return np.array(Image.fromarray(a).resize((24,38),Image.Resampling.NEAREST))
class Page:
 def __init__(self,path):
  im=Image.open(path);require(im.size==(1700,2193),'Unexpected page size');require(im.mode in ('RGB','RGBA'),'Not RGB/RGBA')
  require(not any(k.lower() in ('comment','exif','description') for k in im.info),'Unexpected image metadata')
  rgb=np.array(im.convert('RGB'));require(int((rgb.max(2)-rgb.min(2)>3).sum())==0,'Unexpected color')
  self.a=rgb.min(2)<180;self.cover=np.zeros(self.a.shape,bool);self.items=[];self.exclude=np.zeros(self.a.shape,bool)
 def take(self,b):
  x,y,r,s=b;self.cover[y:s,x:r]=True;return self.a[y:s,x:r].copy()
 def primitive(self,key,b):
  a=self.take(b)
  if key=='copy_arrow':
   t=T[key][0];mask=t.copy()
   for dy in (-2,-1,0,1,2):
    for dx in (-2,-1,0,1,2):mask|=np.roll(np.roll(t,dy,0),dx,1)
   x,y,r,z=b;self.cover[y:z,x:r]=mask;a&=mask
  require(any(a.shape==t.shape and np.array_equal(a,t) for t in T[key]),f'Missing/damaged {key} at {b}')
  self.items.append({'kind':key,'box':list(b)})
  if key=='copy_arrow':
   x,y,r,z=b;self.exclude[y:z,x:r]|=a
 def token(self,x,y,margin=42):
  b=(x-margin,y-margin,x+margin,y+margin);a=self.take(b)
  off=42-margin
  a &= ~self.exclude[b[1]:b[3],b[0]:b[2]]
  keys=[k for k in ('O','S','D','Ox','Sx') if np.count_nonzero(a!=T[k][0][off:84-off,off:84-off])<=4]
  require(len(keys)==1,f'Missing, extra or malformed shape at {b}')
  key=keys[0];self.items.append({'kind':key,'box':list(b)});return 'OSD'.index(key[0])+1,key.endswith('x')
 def word(self,x,y,n,pitch,margin=42):
  r=[self.token(x+i*pitch,y,margin) for i in range(n)];return [a for a,b in r],[i for i,(a,b) in enumerate(r) if b]
 def digits(self,b,count):
  a=self.take(b);cols=np.where(a.any(0))[0];gs=[]
  for c in cols:
   if not gs or c>gs[-1][-1]+1:gs.append([])
   gs[-1].append(int(c))
  require(len(gs)==count,f'Expected {count} digit glyphs at {b}')
  out='';glyphs=[]
  for g in gs:
   v=a[:,g[0]:g[-1]+1];ys=np.where(v.any(1))[0];v=v[ys[0]:ys[-1]+1]
   require(v.shape[0]>=19,'Too-small data digit')
   scores={k[6:]:min(np.mean(resize(v)!=resize(t)) for t in ts) for k,ts in T.items() if k.startswith('digit_')}
   ranked=sorted(scores,key=scores.get);require(scores[ranked[0]]<.12 and scores[ranked[1]]-scores[ranked[0]]>.03,f'Ambiguous/damaged digit at {b}')
   out+=ranked[0];glyphs.append({'digit':ranked[0],'box':[b[0]+g[0],b[1]+int(ys[0]),b[0]+g[-1]+1,b[1]+int(ys[-1])+1],'height':int(v.shape[0])})
  self.items.append({'kind':'digits','value':out,'box':list(b),'glyphs':glyphs});return out
 def options(self,y):
  out=[]
  for cx,lx in zip((398,890,1382),(152,644,1136)):
   w,cross=self.word(cx-144,y,5,72,36);require(not cross,'Crossed candidate')
   label=self.digits((lx,y-18,lx+44,y+18),2);out.append({'label':label,'word':w})
  require(len({x['label'] for x in out})==3,'Repeated candidate labels');require(len({tuple(x['word']) for x in out})==3,'Repeated candidate words')
  return out
 def horizontal(self,b):
  a=self.take(b);ys,xs=np.where(a);require(len(xs)>0,'Missing answer line')
  require(max(xs)-min(xs)+1>=b[2]-b[0]-4,'Short answer line')
  require(np.all(a.any(0)[min(xs):max(xs)+1]),'Broken answer line')
  require(max(ys)-min(ys)+1<=3,'Unexpected ink at answer line')
 def finish(self):
  # Every ink pixel in the puzzle body is accounted for, including between sample slots.
  residual=self.a&~self.cover;residual[:300]=False;residual[2000:]=False
  require(not residual.any(),f'Unaccounted body ink: {np.argwhere(residual)[:6].tolist()}')
  for b in ((130,120,670,190),(130,220,1100,270)):
   x,y,r,s=b;require(self.a[y:s,x:r].sum()>1000,'Missing heading/lede')

def read_images(path):
 path=Path(path);require(sorted(p.name for p in path.glob('*.png'))==['01.png','02.png'],'Expected two ordered pages')
 p=Page(path/'01.png');examples=[]
 for j,y in enumerate((380,880,1380)):
  w,cross=p.word(190,y,13,110);ids=[i for i in range(12) if w[i]==w[i+1]]
  require(len(cross)==2 and cross[1]==cross[0]+1 and w[cross[0]]==w[cross[1]],'Initial crossed pair not equal/adjacent')
  p.primitive('long_arrow',(838,y+50,862,y+110))
  if j<2:
   end,c=p.word(630,y+160,5,110);require(not c,'Crossed terminal');options=None
  else:
   # Ring location is extraction layout, not a selected label value.
   b=(133,1506,212,1574);a=p.take(b);a[14:54,17:65]=False
   require(np.array_equal(a,T['selection_ring'][0]),'Missing/damaged selection circle')
   p.primitive('copy_arrow',(210,1570,750,1636))
   options=p.options(y+160);end=options[0]['word']
   written=p.digits((790,1612,816,1648),1)+p.digits((886,1612,912,1648),1)
   require(written==options[0]['label'],'Copied label does not match circled label')
   p.horizontal((764,1657,840,1663));p.horizontal((860,1657,936,1663))
  examples.append({'word':w,'terminal':end,'crossed':cross,'options':options})
 p.primitive('footer_01',(1498,2024,1568,2058));p.finish()
 q=Page(path/'02.png');queries=[]
 for y in (400,680,960,1240,1520):
  w,cross=q.word(190,y,13,110);require(not cross,'Unexpected query crosses')
  q.primitive('short_arrow',(840,y+46,860,y+71));q.primitive('unknown',(824,y+76,876,y+128))
  queries.append({'word':w,'options':q.options(y+170)})
 for g in range(5):
  for i in range(2):
   x=526+136*g+56*i;q.horizontal((x-1,1847,x+49,1853))
 q.primitive('footer_02',(1498,2024,1568,2058));q.finish()
 return {'examples':examples,'queries':queries,'page_items':{'01.png':p.items,'02.png':q.items}}
