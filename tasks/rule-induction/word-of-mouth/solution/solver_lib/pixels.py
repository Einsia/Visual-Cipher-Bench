"""Recover letters, holes and radial record relations from PNG pixels.
Coordinates describe page geometry only. No expected row data or answer is stored.
"""
import json,math
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

class Invalid(ValueError):pass

def require(ok,msg):
 if not ok:raise Invalid(msg)

def components(a):
 seen=np.zeros(a.shape,bool);out=[]
 for y,x in zip(*np.where(a)):
  if seen[y,x]:continue
  seen[y,x]=1;q=[(int(y),int(x))];pts=[]
  while q:
   v,u=q.pop();pts.append((v,u))
   for yy,xx in [(v-1,u),(v+1,u),(v,u-1),(v,u+1)]:
    if 0<=yy<a.shape[0] and 0<=xx<a.shape[1] and a[yy,xx] and not seen[yy,xx]:seen[yy,xx]=1;q.append((yy,xx))
  ys,xs=zip(*pts);out.append((min(xs),min(ys),max(xs)+1,max(ys)+1,len(pts)))
 return out

class Parser:
 def __init__(self,path):
  im=Image.open(path);require(im.size==(1700,2193),'Unexpected canvas');require(im.mode in ('RGB','RGBA'),'Non-RGB PNG')
  require(not any(k in im.info for k in ('exif','comment','text')),'Unexpected metadata')
  self.rgb=np.array(im.convert('RGB'));self.ink=self.rgb[:,:,0]<128
  require(np.max(self.rgb.max(axis=2)-self.rgb.min(axis=2))<=1,'Non-monochrome pixels')
  self.allowed=Image.new('1',im.size);self.draw=ImageDraw.Draw(self.allowed);self.text=[];self.geometry=[];self.holes=[]
  raw=json.loads((Path(__file__).parent/'glyph_templates.json').read_text())
  self.templates={k:[np.array([[v=='1' for v in r]for r in a])for a in arr]for k,arr in raw.items()}
 def allow(self,b):self.draw.rectangle([b[0]-1,b[1]-1,b[2],b[3]],fill=1)
 def crop(self,b):return self.ink[b[1]:b[3],b[0]:b[2]]
 def text_at(self,b,family,domain,role='label',blank=False):
  a=self.crop(b);occ=a.any(axis=0)
  if not occ.any():require(blank,'Missing text '+str(b));return ''
  ls=np.where(occ & ~np.r_[False,occ[:-1]])[0];rs=np.where(occ & ~np.r_[occ[1:],False])[0]+1
  result='';boxes=[];heights=[]
  for l,r in zip(ls,rs):
   z=a[:,l:r];ys=np.where(z.any(axis=1))[0];t=int(ys[0]);bt=int(ys[-1])+1;z=z[t:bt];scores=[]
   for c in domain:
    for template in self.templates.get(family+':'+c,[]):
     if abs(z.shape[0]-template.shape[0])>2 or abs(z.shape[1]-template.shape[1])>2:continue
     norm=np.array(Image.fromarray(z).resize((template.shape[1],template.shape[0]),Image.Resampling.NEAREST))
     score=np.logical_xor(norm,template).sum()/max(1,np.logical_or(norm,template).sum());scores.append((float(score),c))
   require(bool(scores),'Unrecognized glyph dimensions '+str(b));scores.sort();best,c=scores[0]
   require(best<.32,'Unrecognized glyph '+str(b)+' score '+str(best))
   others=[s for s,ch in scores if ch!=c];require(not others or min(others)-best>.025,'Ambiguous glyph '+str(b))
   result+=c;box=[b[0]+int(l),b[1]+t,b[0]+int(r),b[1]+bt];boxes.append(box);heights.append(bt-t);self.allow(box)
  box=[min(x[0]for x in boxes),min(x[1]for x in boxes),max(x[2]for x in boxes),max(x[3]for x in boxes)]
  self.text.append(dict(role=role,text=result,box=box,min_glyph_height_px=min(heights),glyph_boxes=boxes))
  require(min(heights)>=19,'Required character too small');return result
 def path(self,pts,width=2,label='path',gray=False):
  if 2<len(pts)<=5:
   for a,b in zip(pts,pts[1:]):self.path([a,b],width,label,gray)
   return
  # Actual connected path, not merely occupancy near successive samples.
  xs=[p[0]for p in pts];ys=[p[1]for p in pts];b=[int(min(xs))-6,int(min(ys))-6,int(max(xs))+7,int(max(ys))+7]
  mask=Image.new('1',(b[2]-b[0],b[3]-b[1]));d=ImageDraw.Draw(mask);local=[(x-b[0],y-b[1])for x,y in pts];d.line(local,fill=1,width=width+6)
  pixels=self.rgb[b[1]:b[3],b[0]:b[2],0]<210 if gray else self.crop(b)
  a=pixels&np.array(mask);cc=components(a)
  # Seed near first endpoint and require the same 4-connected component at the last.
  sx,sy=local[0];tx,ty=local[-1];starts=[(int(y),int(x))for y,x in zip(*np.where(a))if abs(x-sx)<=3 and abs(y-sy)<=3]
  require(starts,'Missing start '+label);seen=set(starts);q=list(starts)
  while q:
   y,x=q.pop()
   for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
    if 0<=yy<a.shape[0] and 0<=xx<a.shape[1] and a[yy,xx] and (yy,xx)not in seen:seen.add((yy,xx));q.append((yy,xx))
  require(any(abs(x-tx)<=2 and abs(y-ty)<=2 for y,x in seen),'Disconnected '+label)
  self.draw.line(pts,fill=1,width=width+6)
  for x,y in pts:self.draw.ellipse((x-4,y-4,x+4,y+4),fill=1)
  self.geometry.append({'type':label,'box':b,'continuous':True})
 def ring(self,cx,cy,r,width,notch):
  # Exclude intentional gap at twelve o'clock; check all of the remaining arc as one path.
  gap=math.asin(notch/r)
  ts=np.linspace(gap,math.tau-gap,max(300,int(r*8)))
  pts=[(cx+r*math.sin(t),cy-r*math.cos(t))for t in ts]
  self.path(pts,width,'circle outline')
 def closed_ring(self,cx,cy,r,width=2,gray=False):
  pts=[(cx+r*math.sin(t),cy-r*math.cos(t))for t in np.linspace(0,math.tau,max(100,int(r*8)))]
  self.path(pts,width,'badge ring' if gray else 'unlabelled wheel socket',gray)
 def wheel(self,cx,cy,hidden=False):
  self.ring(cx,cy,110,4,12);self.path([(cx,cy-110),(cx,cy-103)],2,'wheel top notch')
  s=''
  for i in range(10):
   t=i*math.tau/10;x=round(cx+76*math.sin(t));y=round(cy-76*math.cos(t))
   if hidden:
    sx=cx+77*math.sin(t);sy=cy-77*math.cos(t)
    self.closed_ring(sx,sy,6)
    require(not self.crop([round(sx)-3,round(sy)-3,round(sx)+3,round(sy)+3]).any(),'Filled hidden socket')
    s+='.'
   else:
    c=self.text_at([x-13,y-16,x+14,y+17],'label','AEILNORSTU');require(len(c)==1,'Extra wheel label');s+=c
  require(hidden or len(set(s))==10,'Wheel not a permutation');return s
 def badges(self,cx,cy,count):
  found={}
  for slot in range(10):
   a=slot*math.tau/10
   point=lambda r:(cx+r*math.sin(a),cy-r*math.cos(a))
   levels=[]
   for depth in range(count):
    radius=135+42*depth;bx,by=point(radius)
    if bx-19<0 or bx+19>=self.ink.shape[1] or by-19<0 or by+19>=self.ink.shape[0]:break
    # Badges are discovered from their grey circular outline, not stored data.
    angles=np.linspace(0,math.tau,80,endpoint=False)
    samples=[]
    for t in angles:
     x=round(bx+17*math.sin(t));y=round(by-17*math.cos(t))
     samples.append((self.rgb[y-1:y+2,x-1:x+2,0]<210).any())
    if np.mean(samples)<.95:break
    self.closed_ring(bx,by,17,2,True)
    b=[round(bx)-13,round(by)-15,round(bx)+14,round(by)+16]
    c=self.text_at(b,'body','123456789',role='record ordinal')
    require(len(c)==1 and int(c)not in found,'Repeated or invalid record ordinal')
    found[int(c)]=slot;levels.append(radius)
   if levels:
    begin=94
    for radius in levels:
     self.path([point(begin),point(radius-17)],2,'radial record link',True)
     begin=radius+17
  require(set(found)==set(range(1,count+1)),'Record ordinals are not 1..n')
  return [found[i]for i in range(1,count+1)]
 def tray(self,cx,cy,query=False):
  self.path([(cx-110,cy+128),(cx-110,cy+209),(cx+110,cy+209),(cx+110,cy+128)],2,'tray boundary')
  s=self.text_at([cx-103,cy+137,cx+104,cy+201],'body','AEILNORSTU?',role='clue',blank=True)
  if query:require(s=='?','Missing unique query marker')
  else:require('?'not in s,'Unexpected query marker')
  return s
 def dial(self,cx,cy):
  self.ring(cx,cy,43,2,6);self.path([(cx,cy-43),(cx,cy-36)],2,'dial notch')
  # Square is data: accept either a complete square or its complete absence.
  b=[cx-56,cy-56,cx+57,cy+57];a=self.crop(b);z=a[:6].sum()+a[-6:].sum()+a[:,:6].sum()+a[:,-6:].sum();boxed=z>50
  if boxed:self.path([(cx-53,cy-53),(cx+53,cy-53),(cx+53,cy+53),(cx-53,cy+53),(cx-53,cy-53)],4,'box frame')
  filled=[]
  for i in range(10):
   t=i*math.tau/10;x=cx+31*math.sin(t);y=cy-31*math.cos(t);b=[math.floor(x)-6,math.floor(y)-6,math.ceil(x)+7,math.ceil(y)+7]
   a=self.crop(b);yy,xx=np.indices(a.shape);rr=np.hypot(xx+b[0]+.5-x,yy+b[1]+.5-y)
   inner=rr<2.3;ann=(rr>=3.7)&(rr<=4.4)
   full=a[inner].mean()>.85
   require(a[ann].mean()>.75,'Missing or damaged hole '+str((cx,cy,i)))
   require(full or a[inner].mean()<.12,'Indeterminate hole state')
   # Require ring occupancy in every sector, including for an unfilled hole.
   for sector in range(8):
    angle=np.mod(np.arctan2(yy+b[1]+.5-y,xx+b[0]+.5-x),math.tau);part=ann&(angle>=sector*math.tau/8)&(angle<(sector+1)*math.tau/8)
    require(a[part].any(),'Broken hole outline')
   if full:filled.append(i)
   # Tight circular allowance excludes extra marks inside the dial away from the ten holes.
   self.draw.ellipse((x-5.6,y-5.6,x+5.6,y+5.6),fill=1)
   self.holes.append({'center':[x,y],'filled':bool(full),'row_y':cy,'dial_x':cx,'slot':i})
  require(len(filled)==1,'Dial needs exactly one selected hole')
  return {'slot':filled[0],'boxed':bool(boxed)}
 def arrow(self,pts):
  self.path(pts,2,'row arrow shaft');x,y=pts[-1];vertical=pts[-2][0]==x
  b=[x-6,y-12,x+6,y+2]if vertical else [x-12,y-6,x+2,y+6]
  a=self.crop(b);cc=components(a);require(len(cc)==1 and cc[0][4]>=35,'Damaged arrow head')
  if vertical:require(cc[0][2]-cc[0][0]>=8,'Missing arrow head wings')
  else:require(cc[0][3]-cc[0][1]>=8,'Missing arrow head wings')
  self.allow(b)
 def parse(self):
  # Fixed non-operative title and lede are permitted prose, not solving data.
  # Bind these two approved text shapes; no unchecked text band is permitted.
  prose=json.loads((Path(__file__).parent/'prose_templates.json').read_text())
  for item in prose:
   template=np.array([[v=='1' for v in row]for row in item['bitmap']]);a=self.crop(item['box'])
   require(np.logical_xor(a,template).sum()<=2,'Changed or damaged heading prose')
   self.allow(item['box'])
  rows=[]
  for row,cy in enumerate([480,940,1400,1860]):
   start={'wheel':self.wheel(248,cy),'record':self.tray(248,cy)}
   # Short incoming connector must be a single component spanning its full length.
   b=[362,cy-5,379,cy+6];cc=components(self.crop(b));require(len(cc)==1 and cc[0][2]-cc[0][0]>=11 and cc[0][4]>=24,'Broken short connector');self.allow(b)
   count=[3,7,7,8][row];tokens=[self.dial(426+118*j,cy)for j in range(count)]
   require(not tokens[0]['boxed']or bool(start['record']),'No feedback before first box')
   if row<3:
    self.arrow([(426+118*(count-1)+64,cy),(1324,cy)])
    end={'wheel':self.wheel(1452,cy,hidden=row>0),'record_positions':self.badges(1452,cy,count)}
    if row==0:
     end['record']=self.tray(1452,cy)
     require(len(end['record'])==len(start['record'])+len(tokens),'Record length mismatch')
    rows.append({'start':start,'tokens':tokens,'end':end})
   else:
    self.arrow([(1316,cy),(1452,cy),(1452,cy+108)]);self.tray(1452,cy,True)
    target_start=start;target_tokens=tokens
  # Separators are light-gray but still validated as uninterrupted lines.
  for y in (740,1200,1660):
   require((self.rgb[y,136:1564,0]<220).mean()>.99,'Missing row separator');self.allow([134,y-2,1566,y+3])
  outside=(self.rgb[:,:,0]<210)&~np.array(self.allowed)
  require(not outside.any(),'Extra ink outside recognized elements: '+str(np.argwhere(outside)[:8].tolist()))
  return {'ordinary':rows[0],'observations':rows[1:],'target_start':target_start,'target_tokens':target_tokens,'answer_length':len(target_tokens),'pixel_evidence':{'text_regions':self.text,'geometry':self.geometry,'holes':self.holes,'extra_dark_pixels':int(outside.sum()),'min_glyph_height_px':min(t['min_glyph_height_px']for t in self.text)}}

def read(images):
 p=Path(images);files=list(p.glob('*.png')) if p.is_dir() else [p];require(len(files)==1,'Expected one public image');return Parser(files[0]).parse()
