"""Pixel parser for this worksheet's geometry; no answers or state transcript.
Object/glyph exemplars are isolated labelled visual classes, independent of slots.
Links are recovered as continuous components, including endpoints, not cached.
"""
from pathlib import Path
from collections import deque
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).parent
class InvalidImage(ValueError): pass
def need(ok,message):
 if not ok: raise InvalidImage(message)
def bbox(m):
 yy,xx=np.where(m)
 if not len(xx): return None
 return [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
def runs(v):
 p=np.pad(v.astype(int),(1,1));return [(int(l),int(r)) for l,r in zip(np.where(np.diff(p)==1)[0],np.where(np.diff(p)==-1)[0])]
def components(m):
 seen=np.zeros(m.shape,bool);out=[];h,w=m.shape
 for sy,sx in zip(*np.where(m)):
  if seen[sy,sx]:continue
  q=[(int(sy),int(sx))];seen[sy,sx]=True;pts=[]
  while q:
   y,x=q.pop();pts.append((y,x))
   for dy,dx in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
    Y,X=y+dy,x+dx
    if 0<=Y<h and 0<=X<w and m[Y,X] and not seen[Y,X]:seen[Y,X]=True;q.append((Y,X))
  out.append(pts)
 return out

def distance(a,b):
 # Rasterization phase may differ by 1px. Shape dimensions must still agree.
 if max(abs(a.shape[0]-b.shape[0]),abs(a.shape[1]-b.shape[1]))>1:return 1.
 if a.shape!=b.shape:b=np.asarray(Image.fromarray(b).resize((a.shape[1],a.shape[0]),Image.Resampling.NEAREST))
 return float(np.logical_xor(a,b).sum()/max(1,np.logical_or(a,b).sum()))

ALIASES={
 'bed':['bed','cot','bunk'],
 'coal':['coal','rock','rocks','stone','stones'],
 'ribbon':['ribbon','bow','strip','tape','knot','fabric'],
 'ring':['ring','band','hoop','jewelry','jewellery','jewel','diamond','gem','stone','ornament','circle'],
 'forest':['forest','wood','woods','trees','woodland','grove','tree','pine','fir','pines','firs'],
 'table':['table','desk','stand','furniture','bench','trestle']}

class Parser:
 def __init__(self,path):
  im=Image.open(path);need(im.format=='PNG' and im.mode in ('RGB','RGBA'),'Expected RGB/RGBA PNG')
  need(im.size==(1700,2193),'Unexpected worksheet dimensions')
  need(not any(k.lower() in ('exif','comment','description','text') for k in im.info),'Forbidden metadata')
  if im.mode=='RGBA':need(np.asarray(im)[:,:,3].min()==255,'Nonopaque image')
  a=np.asarray(im.convert('RGB'));need((a.max(2)-a.min(2)>10).mean()<0.002,'Unexpected semantic colour')
  self.m=a[:,:,0]<180;self.cover=np.zeros(self.m.shape,bool);self.records=[]
  self.templates=np.load(ROOT/'visual_templates.npz');self.labels=json.loads((ROOT/'template_labels.json').read_text())
 def area(self,b):
  x,y,X,Y=b;self.cover[y:Y,x:X]=True;return self.m[y:Y,x:X]
 def ocr(self,b,font='mono'):
  x,y,X,Y=b;m=self.area(b); chars=[];boxes=[];last=None
  for l,r in runs(m.any(0)):
   z=bbox(m[:,l:r]);p=m[z[1]:z[3],l:r]
   ranked=sorted((distance(p,self.templates[v['key']]),v['char']) for v in self.labels['glyphs'] if v['font']==font)
   need(ranked and ranked[0][0]<0.20,f'Unrecognized glyph at {x+l},{y+z[1]}')
   same=[ch for score,ch in ranked if score<=ranked[0][0]+0.025]
   need(len(set(same))==1,'Ambiguous glyph')
   if last is not None and l-last>13:chars.append(' ')
   chars.append(ranked[0][1]);boxes.append([x+l,y+z[1],x+r,y+z[3]]);last=r
  return ''.join(chars),boxes
 def icon(self,b):
  m=self.area(b);z=bbox(m)
  if z is None:return None
  p=m[z[1]:z[3],z[0]:z[2]]
  ranked=sorted((distance(p,self.templates[v['key']]),v['label']) for v in self.labels['icons'])
  need(ranked[0][0]<0.10,f'Unknown/incomplete/extra pictogram in {b}: {ranked[0]}')
  self.records.append({'type':'icon','class':ranked[0][1],'box':[b[0]+z[0],b[1]+z[1],b[0]+z[2],b[1]+z[3]],'distance':ranked[0][0]})
  return ranked[0][1]
 def cell(self,c,y,split):
  # Continuous complete rectangular frame, rounded corners excluded from straight checks.
  b=[c-142,y-2,c+142,y+83];m=self.area(b);x0=b[0];y0=b[1]
  for yy in (y,y+80):
   need(self.m[yy-1:yy+2,c-135:c+136].any(0).all(),f'Broken horizontal cell frame {c},{y}')
  for xx in (c-140,c+140):
   need(self.m[y+5:y+76,xx-1:xx+2].any(1).all(),f'Broken vertical cell frame {c},{y}')
  interior=self.m[y+6:y+75,c-134:c+135].copy()
  # No stray glyphs in gutters; divider is evaluated independently.
  if split:
   v=self.m[y+10:y+70,c-2:c+3];sp=runs(v.any(1))
   need(len(sp)>=5 and all(4<=r-l<=10 for l,r in sp),'Missing/invalid dashed half divider')
   need(not self.m[y+6:y+75,c-8:c-2].any() and not self.m[y+6:y+75,c+3:c+9].any(),'Extra mark beside divider')
   parts=[];boxes=[]
   for lo,hi in ((c-130,c-10),(c+10,c+130)):
    t,bb=self.ocr([lo,y+12,hi,y+69]);parts.append(t or None);boxes+=bb
   interior[:,132:137]=False
  else:
   t,boxes=self.ocr([c-130,y+12,c+130,y+69]);parts=t or None
  # Ignore legal text rectangle(s), detect extra ink inside outside OCR band.
  if split:
   interior[6:63,4:124]=False;interior[6:63,144:264]=False
  else:interior[6:63,4:264]=False
  need(not interior.any(),f'Extra symbol inside frame {c},{y}')
  self.records.append({'type':'cell','center':c,'top':y,'split':split,'value':parts,'glyph_boxes':boxes})
  return parts
 def link(self,centers,y):
  # y is the bottom edge of the source row. Exclude that edge from connectivity.
  b=[135,y+2,1550,y+99];m=self.area(b);comps=components(m)
  need(len(comps)==2,f'Exchange must have one continuous bracket and one down arrow, got {len(comps)} components at y={y}')
  parts=[]
  for pts in comps:
   yy,xx=zip(*pts);parts.append(([min(xx)+b[0],min(yy)+b[1],max(xx)+b[0]+1,max(yy)+b[1]+1],pts))
  down=[v for v in parts if v[0][2]<170];links=[v for v in parts if v[0][0]>170]
  need(len(down)==1 and len(links)==1,'Extra/displaced arrow or connector')
  db=down[0][0];need(db[0]<=150<db[2] and 55<=db[3]-db[1]<=66,'Malformed stage arrow')
  dm=self.m[db[1]:db[3],db[0]:db[2]];widths=dm.sum(1)
  need(widths[-15:].max()>=8 and widths[:20].max()<=4,'Stage arrow must point downward')
  lb=links[0][0];p=self.m[b[1]:lb[3],lb[0]:lb[2]]
  top=runs(p[:3].any(0));need(len(top)==2,'Missing/extra bracket tips')
  ends=[lb[0]+(l+r-1)/2 for l,r in top]
  need(p[-3:,round(ends[0])-lb[0]:round(ends[1])-lb[0]+1].any(0).all(),'Broken bracket baseline')
  ops=[]
  for ex in ends:
   choices=[(abs(ex-(c+s*70)),i,'left' if s<0 else 'right',c+s*70) for i,c in enumerate(centers) for s in (-1,1)]
   d,i,side,xx=min(choices);need(d<2,'Connector not aligned to half slot')
   need(self.m[y:y+4,xx-1:xx+2].any(1).all(),'Endpoint detached from source box')
   shaft=self.m[y+2:lb[3],xx-2:xx+3]
   need(shaft.any(1).all(),'Broken vertical bracket segment')
   head=self.m[y+2:y+16,xx-7:xx+8];w=head.sum(1)
   need(w.max()>=8 and w[0]<w.max(),'Missing upward arrowhead')
   ops.append((i,side))
  need(ops[0][0]!=ops[1][0],'Self exchange is invalid')
  # Restrict all bracket ink to two posts, the baseline, and the arrow heads.
  allowed=np.zeros_like(p)
  allowed[-5:,:]=True
  for ex in ends:
   xx=round(ex)-lb[0];allowed[:,max(0,xx-2):xx+3]=True;allowed[:15,max(0,xx-7):xx+8]=True
  need(not (p&~allowed).any(),'Extra branch or mark on connector')
  op=[ops[0][0],ops[1][0],ops[0][1],ops[1][1]]
  self.records.append({'type':'exchange','op':op,'box':lb,'down_arrow_box':db,'continuous_pixels':len(links[0][1])})
  return op
 def read(self):
  # Title/lede not algorithm data; publication wording is independently transcribed.
  need(self.area([130,120,1300,275]).sum()>1000,'Missing page heading')
  label,_=self.ocr([210,345,350,390],'label');need(label=='Example','Missing example label')
  ec=[360,850,1340];pc=[310,670,1030,1390]
  ei=[];ew=[]
  for c in ec:
   region=[c-70,390,c+70,470]
   try:
    label=self.icon(region);ei.append(label);ew.append(None)
   except InvalidImage:
    value,boxes=self.ocr(region)
    need(bool(value),'Missing input word')
    ei.append(None);ew.append(value)
    self.records.append({'type':'input_word','value':value,'glyph_boxes':boxes})
  pi=[self.icon([c-70,990,c+70,1120]) for c in pc]
  need(all(pi),'Missing puzzle object')
  er=[ [self.cell(c,y,k<2) for c in ec] for k,y in enumerate((480,660,840))]
  pr=[ [self.cell(c,y,k<4) for c in pc] for k,y in enumerate((1140,1320,1500,1680,1860))]
  eo=[self.link(ec,y) for y in (560,740)];po=[self.link(pc,y) for y in (1220,1400,1580,1760)]
  target=[i for i,v in enumerate(pr[-1]) if v=='?'];need(len(target)==1,'Exactly one final question mark required')
  need(all(v is None or v=='?' for v in pr[-1]),'Unrecognized output markings')
  stray=self.m & ~self.cover;need(not stray.any(),f'Unclassified extra ink: {bbox(stray)}')
  return {'example':{'icons':ei,'input_words':ew,'rows':er,'operations':eo},'problem':{'icons':pi,'rows':pr,'operations':po,'target':target[0]},'records':self.records}
