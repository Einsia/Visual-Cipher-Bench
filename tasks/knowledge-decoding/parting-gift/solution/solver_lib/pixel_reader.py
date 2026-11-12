"""Pixel reader for the outlined spatial-language page.

The assets are small pictogram templates, not a page or a transcript. Labels,
phrases, double-ring states, connectivity and spatial relations are read anew.
"""
from pathlib import Path
import json,string
from collections import deque
from PIL import Image,ImageDraw,ImageFont
import numpy as np
BASE=Path(__file__).parent
class ReadError(ValueError):pass

def bounds(a):
 y,x=np.where(a)
 if not len(x):raise ReadError('Missing glyph/shape')
 return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]

def canonical(a):
 b=bounds(a); a=a[b[1]:b[3],b[0]:b[2]]
 return np.asarray(Image.fromarray(a.astype('uint8')*255).resize((max(1,round(a.shape[1]*40/a.shape[0])),40)))>127

def text_score(a,b):
 aa=canonical(a);bb=canonical(b)
 if abs(aa.shape[1]-bb.shape[1])>max(5,aa.shape[1]*.15):return 1
 bb=np.asarray(Image.fromarray(bb.astype('uint8')*255).resize((aa.shape[1],40)))>127
 # Small rasterization differences are expected between native paths and BASIC fonts.
 best=1
 for dy in [-1,0,1]:
  for dx in [-1,0,1]:
   t=np.roll(bb,(dy,dx),(0,1));score=np.logical_xor(aa,t).sum()/max(1,np.logical_or(aa,t).sum());best=min(best,float(score))
 return best

def rendered(text,size,mono=False):
 f=ImageFont.truetype(str(BASE/('DejaVuSansMono.ttf' if mono else 'DejaVuSans.ttf')),size,layout_engine=ImageFont.Layout.BASIC)
 im=Image.new('L',(1000,120),255);ImageDraw.Draw(im).text((10,10),text,font=f,fill=17)
 return np.asarray(im)<180

def read_text(a,box,words,size=34,mono=False,optional=False):
 x,y,r,b=map(int,box);m=a[y:b,x:r]<180
 if not m.any():
  if optional:return None
  raise ReadError('Missing text at '+str(box))
 scores=sorted((text_score(m,rendered(w,size,mono)),w) for w in words)
 if scores[0][0]>.34:raise ReadError('Unrecognized text at '+str(box)+' '+str(scores[:3]))
 if len(scores)>1 and scores[1][0]-scores[0][0]<.018:raise ReadError('Ambiguous glyph '+str(scores[:3]))
 return scores[0][1]

def path_mask(shape,points,width=7,loc=None):
 im=Image.new('1',(shape[1],shape[0]));d=ImageDraw.Draw(im);d.line([tuple(p) for p in points],fill=1,width=width)
 for x,y in points:d.ellipse((x-4,y-4,x+4,y+4),fill=1)
 if loc:
  x,y=loc;d.ellipse((x-9,y-9,x+9,y+9),fill=1)
 return np.asarray(im).astype(bool)

def connected(a,points,loc=None,width=7):
 # Genuine 8-connected path: a short blank cut is not bridged by neighborhood sampling.
 corridor=path_mask(a.shape,points,width,loc);m=(a<180)&corridor
 def near(p):
  x,y=map(round,p);return [(yy,xx) for yy in range(max(0,y-3),min(a.shape[0],y+4)) for xx in range(max(0,x-3),min(a.shape[1],x+4)) if m[yy,xx]]
 start=near(points[0]);end=set(near(points[-1]));q=deque(start);seen=set(start)
 while q:
  y,x=q.popleft()
  if (y,x) in end:return corridor
  for dy in (-1,0,1):
   for dx in (-1,0,1):
    p=(y+dy,x+dx)
    if 0<=p[0]<a.shape[0] and 0<=p[1]<a.shape[1] and p not in seen and m[p]:seen.add(p);q.append(p)
 raise ReadError('Broken connection '+str(points))

def read(images):
 files=sorted(Path(images).glob('*.png'))
 if len(files)!=1:raise ReadError('Expected one page')
 im=Image.open(files[0]).convert('RGB');rgb=np.asarray(im)
 if im.size!=(1700,2193):raise ReadError('Unsupported page dimensions')
 if np.max(rgb.max(2).astype(int)-rgb.min(2).astype(int))>2:raise ReadError('Unexpected colour')
 a=np.asarray(im.convert('L'));cover=np.zeros(a.shape,bool)
 layout=json.loads((BASE/'layout.json').read_text());obs=[]
 for ent in layout['symbols']:
  t=np.asarray(Image.open(BASE/ent['asset']).convert('L'));mask=np.asarray(Image.open(BASE/ent['mask']))>0
  x,y,r,b=ent['search'];h,w=t.shape;scores=[]
  for yy in range(y,b-h+1):
   for xx in range(x,r-w+1):
    patch=a[yy:yy+h,xx:xx+w]
    # Compare contour/fill at observed native scale, including white inside the object box.
    diff=np.abs(patch.astype(float)-t.astype(float))/255
    score=float(diff[mask].sum()/max(1,((t<200)&mask).sum()))
    scores.append((score,xx,yy))
  score,xx,yy=min(scores)
  if score>.04:raise ReadError('Missing/damaged pictogram '+ent['kind']+' score '+str(score))
  cover[yy:yy+h,xx:xx+w]|=mask
  box=[xx,yy,xx+w,yy+h]
  frame=next((i for i,(l,top,right,bot) in enumerate(layout['frames']) if l<xx and yy>top and xx+w<right and yy+h<bot),-1)
  obj={'kind':ent['kind'],'box':box,'frame':frame,'parts':{k:[v[0]+xx,v[1]+yy,v[2]+xx,v[3]+yy] for k,v in ent['parts'].items()},'score':score}
  obs.append(obj)
 stations=[]
 vocab=list(json.loads((BASE/'english.json').read_text()))
 def ring(center):
  x,y=center
  yy,xx=np.mgrid[y-43:y+44,x-43:x+44];rr=np.hypot(xx-x,yy-y)
  ink=a[y-43:y+44,x-43:x+44]<180
  if ink[abs(rr-34)<.7].mean()<.93:raise ReadError('Missing token ring')
  if ink[abs(rr-40)<.7].mean()<.93:raise ReadError('Missing terminal ring')
  letter=read_text(a,[x-23,y-16,x+24,y+17],list(string.ascii_uppercase),28)
  cover[y-43:y+44,x-43:x+44]|=(abs(rr-34)<2.5)|(abs(rr-40)<2.5)
  cover[y-16:y+17,x-23:x+24]=True
  return letter
 def selection(box,origin,cell,word):
  l,t,r,b=map(round,box);m=a[t:b,l:r]<180
  row=int(m.sum(1).argmax());xs=np.where(m[row])[0]
  if len(xs)<10 or np.any(np.diff(xs)>1):raise ReadError('Missing/broken selection cap')
  left=l+int(xs[0]);right=l+int(xs[-1]);yy=t+row
  cells=[i for i in range(len(word)) if left<=origin+(i+.5)*cell<=right]
  if not cells or any(word[i]==' ' for i in cells):raise ReadError('Selection does not meet a letter cell')
  # Cap must be centered on the selected cell(s), not guessed from word membership.
  center=(left+right)/2
  expected=origin+(cells[0]+cells[-1]+1)*cell/2
  if abs(center-expected)>2:raise ReadError('Misaligned selection cap')
  cover[t:b,left-2:right+3]=True
  return ''.join(word[i] for i in cells).upper(),center,yy,cells
 for st in layout['stations']:
  if st['mode']=='terminal':
   letter=ring(st['center']);phrase=None;terminal=True
   track=st['track'];cover|=connected(a,track,st['locator'],7)
   selected_cells=[]
  else:
   phrase=read_text(a,st['text_box'],vocab,34,True)
   letter,cx,uy,selected_cells=selection(st['scan_box'],st['text_origin'],st['cell_width'],phrase)
   if len(letter)!=1:raise ReadError('Main station must select one character')
   terminal=False
   track=st['track_prefix']+[[cx,st['spine_y']],[cx,uy]]
   cover|=connected(a,track,st['locator'],7)
   l,t,r,b=map(round,st['text_box']);cover[t:b,l:r]=True
  px,py=track[0]
  candidates=[o for o in obs if o['box'][0]-4<=px<=o['box'][2]+4 and o['box'][1]-4<=py<=o['box'][3]+4]
  if not candidates:raise ReadError('Leader has no selected object')
  obj=min(candidates,key=lambda o:(o['box'][2]-o['box'][0])*(o['box'][3]-o['box'][1]))
  name=obj['kind'];bb=obj['box']
  if name=='needle':name='eye';bb=obj['parts']['eye']
  stations.append({'letter':letter,'next':phrase,'terminal':terminal,'kind':name,'box':bb,'frame':obj['frame'],'selected_cells':selected_cells})
 for x,y,r,b in layout['frames']:
  for points in [[[x,y],[r,y]],[[r,y],[r,b]],[[r,b],[x,b]],[[x,b],[x,y]]]:cover|=connected(a,points,width=5)
 for x,y,r,b in layout['arrows']:
  cover|=connected(a,[[x,y],[r,b]],width=7)
  tri=a[y-9:y+10,r-18:r+2]<180
  if tri.sum()<55:raise ReadError('Missing arrowhead')
  cover[y-9:y+10,r-18:r+2]=True
 start=read_text(a,[130,1905,310,1960],vocab,34,True)
 cal=layout['calibration'];l,t,r,b=cal['text_box'];cell=cal['cell_width'];chars=[]
 for i in range(int((r-l)/cell)):
  ch=read_text(a,[round(l+i*cell),t,round(l+(i+1)*cell),b],list(string.ascii_uppercase),34,True,optional=True)
  if ch is None:break
  chars.append(ch)
 word=''.join(chars)
 raw,cx,uy,cells=selection(cal['scan_box'],cal['text_origin'],cell,word)
 if len(raw)<2:raise ReadError('Calibration needs a multicharacter selection')
 cover[t:b,l:r]=True
 # Reconstruct the cap location from pixels rather than trusting a chosen index.
 feed=[[cal['feed'][0][0]+7,cal['feed'][0][1]],[cx,cal['feed'][0][1]],[cx,uy]]
 cover|=connected(a,feed,cal['feed'][0],7)
 raw+=ring(cal['terminal_center'])
 shown=read_text(a,cal['output_box'],['POT','TOP','PTO','OPT','OTP','TPO'],34)
 for l,t,r,b in [[130,1905,310,1960],cal['output_box'],[130,120,570,200]]:cover[t:b,l:r]=True
 for pts in [[[1020,1785],[1135,1785]],[[334,2024],[1134,2024]]]:cover|=connected(a,pts,width=5)
 unknown=(a<180)&~cover
 if unknown.sum()>50:raise ReadError('Unaccounted ink '+str(int(unknown.sum()))+' pixels; bbox '+str(bounds(unknown)))
 return {'start':start,'example_raw':raw,'example_output':shown,'example_word':word,'example_cells':cells,'stations':stations,'objects':obs,'unaccounted_ink':int(unknown.sum())}
