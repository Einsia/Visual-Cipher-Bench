"""Read the page layout from pixels, including unlettered moving cards.

Letterless cards are read as letterless; their spatial correspondence is
inferred by the operator search. Geometry constants locate regions, never supply data.
"""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
class PixelError(ValueError):pass

def normalize(mask):
 yy,xx=np.where(mask)
 if len(xx)<3:raise PixelError('missing letter ink')
 crop=mask[yy.min():yy.max()+1,xx.min():xx.max()+1]
 return np.array(Image.fromarray(crop.astype('uint8')*255).resize((32,32),Image.Resampling.NEAREST))>0

def read(path):
 im=Image.open(path).convert('RGB');a=np.asarray(im)
 if im.size!=(1700,2193):raise PixelError('unexpected page dimensions')
 if np.mean(np.max(a,axis=2)-np.min(a,axis=2)>8)>.002:raise PixelError('unexpected colored data')
 g=a.mean(axis=2);ink=g<125;lineink=g<200;tmp=np.load(P/'glyphs.npz');letters=tmp['letters'];alphabet=tmp['alphabet'];ocr=[]
 def segment(x1,y1,x2,y2,required=.94):
  count=int(max(abs(x2-x1),abs(y2-y1)))+1;xs=np.rint(np.linspace(x1,x2,count)).astype(int);ys=np.rint(np.linspace(y1,y2,count)).astype(int)
  hits=[np.any(lineink[max(0,y-1):y+2,max(0,x-1):x+2]) for x,y in zip(xs,ys)]
  if np.mean(hits)<required:raise PixelError('broken structural line '+str((x1,y1,x2,y2)))
 def rect(x,y,w,h):
  for v in ((x,y,x+w,y),(x,y+h,x+w,y+h),(x,y,x,y+h),(x+w,y,x+w,y+h)):segment(*v)
 def circle(x,y):
  # Solid rings score near 1, dashed source rings have angular gaps.
  vals=[]
  for t in np.linspace(0,2*math.pi,72,endpoint=False):
   xx=int(round(x+9*math.cos(t)));yy=int(round(y+9*math.sin(t)));vals.append(bool(np.any(ink[yy-1:yy+2,xx-1:xx+2])))
  return np.mean(vals)
 def letter(x,y):
  crop=ink[y+25:y+63,x+21:x+54]
  if np.count_nonzero(crop)<3:return ''
  v=normalize(crop);errs=np.mean(letters!=v,axis=(1,2));order=np.argsort(errs)
  if errs[order[0]]>.19 or errs[order[1]]-errs[order[0]]<.015:raise PixelError('ambiguous glyph '+str((x,y,errs[order[:3]].tolist())))
  ch=str(alphabet[order[0]]);ocr.append({'box':[x+21,y+25,x+54,y+63],'letter':ch,'error':float(errs[order[0]]),'margin':float(errs[order[1]]-errs[order[0]])});return ch
 def arrow(cx,cy):
  x,y=int(round(cx)),int(round(cy));crop=ink[y-17:y+18,x-17:x+18];yy,xx=np.where(crop)
  if len(xx)<35:raise PixelError('missing arrow')
  # Arrowhead has more ink than the plain tail; third moments emphasize the endpoints.
  mx=np.sum((xx-(xx.min()+xx.max())/2)**3);my=np.sum((yy-(yy.min()+yy.max())/2)**3)
  if abs(mx)>abs(my):d='E' if mx>0 else 'W'
  else:d='S' if my>0 else 'N'
  if max(abs(mx),abs(my))<500:raise PixelError('ambiguous arrow')
  return d
 def board(x,y,n,c):
  rect(x,y,n*c,n*c)
  for i in range(1,n):segment(x+i*c,y,x+i*c,y+n*c);segment(x,y+i*c,x+n*c,y+i*c)
  cells=[];rings=[]
  for r in range(n):
   for col in range(n):
    xx=round(x+col*c);yy=round(y+r*c)
    border_score=np.mean(ink[yy+8:yy+c-7,xx+7:xx+10])
    # A real inner card has all four borders; an empty square never does.
    if border_score>.24:
     rect(xx+8,yy+8,c-16,c-16)
     v=bool(np.median(g[yy+10:yy+c-10,xx+10:xx+c-10])<235)
     cells.append({'r':r,'c':col,'letter':letter(xx,yy),'dir':arrow(xx+c*.52,yy+c-30),'visited':v})
    elif np.mean(g[yy+10:yy+c-10,xx+10:xx+c-10]<235)>.16:raise PixelError('unframed or damaged cell content')
    rings.append((circle(xx+c-28,yy+28),r,col))
  rings.sort(reverse=True)
  if rings[0][0]<.90 or rings[1][0]>.88:raise PixelError('missing or multiple solid visitor circles '+str(rings[:3]))
  return {'size':n,'token':[rings[0][1],rings[0][2]],'cells':cells}
 examples=[]
 for x1,x2,y,n,c,ay in [(260,1000,396,4,110,885),(292.5,1032.5,968,3,125,1392)]:
  before=board(x1,y,n,c);after=board(x2,y,n,c)
  segment(790,y+n*c/2,895,y+n*c/2)
  output=''
  for x in (1210,1230):
   v=normalize(ink[ay-27:ay+2,x-10:x+10]);errs=np.mean(letters!=v,axis=(1,2));j=int(np.argmin(errs))
   if errs[j]>.19:raise PixelError('unrecognized example output')
   output+=str(alphabet[j])
  examples.append({'before':before,'after':after,'output':output})
 target=board(610,1475,4,120)
 spec={'examples':examples,'target':target}
 from structure import check
 structure=check(path,spec)
 return spec,{'image_size':list(im.size),'data_glyphs_read':len(ocr)+4,'ocr':ocr,'boards_read':5,'unlettered_cards':sum(not t['letter'] for e in examples for side in ('before','after') for t in e[side]['cells']),'blank_slots':0,'answer_length_source':'computed from the marked letters','structure':structure}
