import numpy as np
from PIL import Image
from collections import deque

def components(mask):
 todo=mask.copy(); h,w=todo.shape;out=[]
 for y,x in zip(*np.nonzero(mask)):
  if not todo[y,x]:continue
  todo[y,x]=False;stack=[(int(x),int(y))];pix=[]
  while stack:
   u,v=stack.pop();pix.append((u,v))
   for a,b in ((u-1,v),(u+1,v),(u,v-1),(u,v+1),(u-1,v-1),(u+1,v-1),(u-1,v+1),(u+1,v+1)):
    if 0<=a<w and 0<=b<h and todo[b,a]:todo[b,a]=False;stack.append((a,b))
  arr=np.array(pix);lo=arr.min(0);hi=arr.max(0)+1
  out.append({'box':[int(lo[0]),int(lo[1]),int(hi[0]),int(hi[1])],'pixels':arr,'size':len(pix)})
 return out

REGIONS={'example_1_input':[180,330,800,720],'example_1_output':[1000,330,1560,720],'example_2_input':[180,815,800,1100],'example_2_output':[1000,815,1570,1100],'example_3_input':[180,1190,800,1610],'example_3_output':[1000,1240,1570,1550],'target_input':[180,1650,800,2010]}
def holes(mask):
 h,w=mask.shape;out=[]
 for c in components(~mask):
  x0,y0,x1,y1=c['box']
  if 59<=x1-x0<=64 and 59<=y1-y0<=64:
   out.append(((x0+x1-1)/2,(y0+y1-1)/2))
 return out

if __name__=='__main__':
 import json
 im=np.array(Image.open('/app/images/01.png').convert('L'))<128
 result={}
 for name,box in REGIONS.items():
  x0,y0,x1,y1=box;m=im[y0:y1,x0:x1].copy();centres=holes(m);yy,xx=np.indices(m.shape)
  for x,y in centres:m[(xx-x)**2+(yy-y)**2<35**2]=False
  cs=components(m)
  result[name]={'nodes':[[x+x0,y+y0] for x,y in centres],'remaining':[{'box':[c['box'][0]+x0,c['box'][1]+y0,c['box'][2]+x0,c['box'][3]+y0],'size':c['size']} for c in cs]}
 print(json.dumps(result,indent=2))
 with open('/work/components.json','w') as f:json.dump(result,f,indent=2)

from pathlib import Path
import json
class PixelError(ValueError):pass
def need(ok,msg):
 if not ok:raise PixelError(msg)

def tight(m):
 ys,xs=np.nonzero(m);need(len(xs)>0,'missing glyph')
 return m[ys.min():ys.max()+1,xs.min():xs.max()+1]
_BANK=None
def ocr(m,style):
 global _BANK
 if _BANK is None:_BANK=json.loads(Path(__file__).with_name('glyph_bank.json').read_text())
 m=tight(m);scores=[]
 for char,variants in _BANK[style].items():
  ds=[]
  for v in variants:
   t=np.array(v,bool)
   if abs(t.shape[0]-m.shape[0])>2 or abs(t.shape[1]-m.shape[1])>2:continue
   s=np.array(Image.fromarray(m).resize((t.shape[1],t.shape[0]),Image.Resampling.NEAREST),bool)
   ds.append(float(np.mean(s!=t)))
  if ds:scores.append((min(ds),char))
 scores.sort();need(scores and scores[0][0]<.18,'unreadable '+style+' glyph')
 need(len(scores)==1 or scores[1][0]-scores[0][0]>.035,'ambiguous '+style+' glyph')
 return scores[0][1],int(m.shape[0]),scores[0][0]

def graph(mask,box,name):
 x0,y0,x1,y1=box;original=mask[y0:y1,x0:x1].copy()
 if name=='example_1_output':original[700-y0:,1258-x0:1282-x0]=False
 cs=holes(original);need(len(cs)>=2,name+': missing closed circle outlines')
 yy,xx=np.indices(original.shape);m=original.copy();nodes=[];glyphs=[]
 for x,y in cs:
  # The complete enclosed white disk, not just its dark centre, identifies a node.
  cx,cy=round(x),round(y);sub=original[cy-20:cy+21,cx-20:cx+21]
  label,h,score=ocr(sub,'node');need(h>=19,name+': small glyph')
  nodes.append(label);glyphs.append({'letter':label,'centre':[x+x0,y+y0],'height':h,'score':score})
  m[(xx-x)**2+(yy-y)**2<35**2]=False
 need(len(nodes)==len(set(nodes)),name+': repeated node identity')
 edges={};marks={};edge_evidence=[]
 for c in components(m):
  pts=c['pixels'];lo=np.array(c['box'][:2]);hi=np.array(c['box'][2:]);wh=hi-lo
  distances=[float(np.sqrt(((pts-np.array([x,y]))**2).sum(1)).min()) for x,y in cs]
  near=[i for i,d in enumerate(distances) if d<37]
  if len(near)==2:
   i,j=near;start=np.array(cs[i]);end=np.array(cs[j]);delta=end-start;length=np.linalg.norm(delta);u=delta/length;v=np.array([-u[1],u[0]])
   projection=(pts-start)@u;off=(pts-start)@v
   need(abs(off).max()<9,name+': edge strays from straight connection')
   first=abs(off[projection<projection.min()+17]).max();last=abs(off[projection>projection.max()-17]).max()
   need(max(first,last)>4 and abs(first-last)>2,name+': missing or ambiguous arrowhead')
   source,target=(j,i) if first>last else (i,j)
   # Recheck continuous pixels through BOTH ring contacts, including the 31–35px annulus.
   t=(xx-start[0])*u[0]+(yy-start[1])*u[1];d=(xx-start[0])*v[0]+(yy-start[1])*v[1]
   corridor=original&(t>=30)&(t<=length-30)&(abs(d)<9)
   paths=components(corridor)
   ok=False
   for path in paths:
    ts=(path['pixels']-start)@u
    if ts.min()<=35.5 and ts.max()>=length-35.5:ok=True
   need(ok,name+': broken source/segment/target connection '+nodes[source]+'>'+nodes[target]+' paths='+repr([(z['size'],float(((z['pixels']-start)@u).min()),float(((z['pixels']-start)@u).max())) for z in paths]))
   need(nodes[source] not in edges,name+': multiple outgoing arrows')
   edges[nodes[source]]=nodes[target]
   edge_evidence.append({'from':nodes[source],'to':nodes[target],'box':[int(lo[0]+x0),int(lo[1]+y0),int(hi[0]+x0),int(hi[1]+y0)],'continuous':True})
  else:
   need(len(near)==0,name+': disconnected/dangling edge component '+str(c['box']))
   sub=m[lo[1]:hi[1],lo[0]:hi[0]];density=c['size']/int(wh.prod())
   if 16<=wh[0]<=21 and 16<=wh[1]<=21:
    white=components(~sub)
    enclosed=any(z['box'][0]>0 and z['box'][1]>0 and z['box'][2]<wh[0] and z['box'][3]<wh[1] for z in white)
    if enclosed and .25<density<.55:kind='square'
    elif not enclosed and .43<density<.65 and sub[:4].sum()<sub[-4:].sum():kind='triangle'
    else:raise PixelError(name+': malformed marker')
    need(kind not in marks,name+': extra '+kind+' marker')
    centre=(lo+hi-1)/2;ds=sorted((np.linalg.norm(centre-np.array(cxy)),i) for i,cxy in enumerate(cs))
    need(ds[0][0]<65 and ds[1][0]-ds[0][0]>20,name+': ambiguous marker attachment')
    marks[kind]=nodes[ds[0][1]]
   else:raise PixelError(name+': extra or fragmented symbol '+str(c['box']))
 need(set(marks)=={'triangle','square'},name+': missing marker')
 need(set(edges)==set(nodes) and set(edges.values())==set(nodes),name+': graph not complete directed cycles')
 need(marks['triangle']!=marks['square'],name+': collocated markers unsupported')
 return {'arrows':edges,**marks}, {'glyphs':glyphs,'edges':edge_evidence,'nodes':len(nodes)}

OPS=[[800,480,970,560],[800,915,970,995],[800,1340,970,1425],[805,1780,1220,1870]]
READOUTS=[[1190,740,1350,785],[1200,1170,1330,1220],[1200,1605,1330,1650]]
DOWN=[[1255,700,1285,740],[1255,1130,1285,1170],[1255,1560,1285,1605],[1255,1900,1285,2010]]
NUMBERS=[[130,355,160,390],[130,790,160,825],[130,1220,160,1260]]
def submask(mask,box):
 x,y,r,b=box;return mask[y:b,x:r]
def simple_arrow(m,horizontal=True):
 cs=components(m);need(len(cs)==1,'missing/fragmented transition or extraction arrow')
 p=cs[0]['pixels'];a,b=p[:,0],p[:,1]
 if not horizontal:a,b=b,a
 need(a.max()-a.min()>20,'arrow too short')
 centre=np.median(b);lo=abs(b[a<a.min()+8]-centre).max();hi=abs(b[a>a.max()-16]-centre).max()
 need(lo<3 and hi>=3,'missing or reversed arrowhead')
 # Components establish uninterrupted ink; reject non-arrow extras.
 need(abs(b-centre).max()<10,'malformed arrow')
 return cs[0]['box']
def operation(m):
 cs=components(m);diamonds=[];arrows=[]
 for c in cs:
  x,y,r,b=c['box'];w,h=r-x,b-y
  if w>80 and h<=20:arrows.append(c)
  elif 27<=w<=36 and 29<=h<=39:
   crop=m[y:b,x:r];white=components(~crop)
   need(any(z['box'][0]>0 and z['box'][1]>0 and z['box'][2]<w and z['box'][3]<h for z in white),'open/broken diamond')
   need(.12<c['size']/(w*h)<.3,'filled or malformed diamond')
   diamonds.append(c)
  else:raise PixelError('extra/fragmented operation symbol '+str(c['box']))
 need(len(arrows)==1 and len(diamonds)>0,'missing operation arrow or count')
 c=arrows[0];a,b,d,e=c['box'];simple_arrow(m[b:e,a:d])
 return len(diamonds)
def readword(m):
 cs=sorted(components(m),key=lambda c:c['box'][0]);need(len(cs)>0,'missing readout')
 chars=[]
 for c in cs:
  x,y,r,b=c['box'];char,h,_=ocr(m[y:b,x:r],'readout');need(h>=19,'small readout');chars.append(char)
 return ''.join(chars)
def parse(image_dir):
 paths=list(Path(image_dir).glob('*.png'));need(len(paths)==1,'expected one public PNG page')
 im=Image.open(paths[0]);need(im.mode in ('RGB','RGBA') and im.size==(1700,2193),'invalid image geometry or mode')
 need(not any(k in im.info for k in ('exif','comment','text')),'unexpected PNG metadata')
 arr=np.array(im.convert('RGB'));need(np.max(arr,2).max()<=255,'invalid pixels');mask=arr.mean(2)<128
 data={'examples':[]};evidence={'graphs':{}};graphs={}
 for name,box in REGIONS.items():graphs[name],evidence['graphs'][name]=graph(mask,box,name)
 ops=[operation(submask(mask,b)) for b in OPS]
 for i in range(3):
  number=ocr(submask(mask,NUMBERS[i]),'number')[0];need(number==str(i+1),'invalid example sequence')
  inp=graphs[f'example_{i+1}_input'];out=graphs[f'example_{i+1}_output'];need(set(inp['arrows'])==set(out['arrows']),'changed node identities in example')
  data['examples'].append({'input':inp,'output':out,'operations':ops[i],'readout':readword(submask(mask,READOUTS[i]))})
 for b in DOWN:simple_arrow(submask(mask,b),False)
 qbox=[1230,1800,1310,1890];q=submask(mask,qbox);cs=components(q);border=[c for c in cs if c['box'][2]-c['box'][0]>50];need(len(border)==1,'missing question box')
 c=border[0];x,y,r,b=c['box'];need(55<=r-x<=62 and 55<=b-y<=62,'bad question box')
 outside=q.copy();outside[y:b,x:r]=False;need(not outside.any(),'extra ink beside unknown box')
 interior=q[y+5:b-5,x+5:r-5];need(ocr(interior,'question')[0]=='?','missing unknown')
 whites=components(~q);need(any(z['box'][0]>x and z['box'][1]>y and z['box'][2]<r and z['box'][3]<b for z in whites),'open question box')
 blanksbox=[1000,2025,1540,2055];blanks=components(submask(mask,blanksbox));need(blanks,'missing answer area')
 need(all(45<=c['box'][2]-c['box'][0]<=65 and 2<=c['box'][3]-c['box'][1]<=4 for c in blanks),'malformed answer blank')
 data['target']={'input':graphs['target_input'],'operations':ops[3],'answer_length':len(blanks)}
 # Scan the entire semantic page, including whitespace outside sampling windows.
 covered=np.zeros(mask.shape,bool)
 for box in list(REGIONS.values())+OPS+READOUTS+DOWN+NUMBERS+[qbox,blanksbox]:
  x,y,r,b=box;covered[y:b,x:r]=True
 stray=mask.copy();stray[:330]=False;stray[covered]=False
 need(not stray.any(),'unexpected semantic ink outside recognized regions')
 evidence['operation_counts']=ops;evidence['answer_blanks']=len(blanks);evidence['min_glyph_height_px']=min(g['height'] for x in evidence['graphs'].values() for g in x['glyphs'])
 return data,evidence
