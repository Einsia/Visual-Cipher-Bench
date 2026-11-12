"""Pixel checks for diagram conventions; fixed ROIs are not instance answers."""
import string
from pathlib import Path
import numpy as np
from PIL import Image, ImageFont, ImageDraw

def runs(v):
 ids=np.flatnonzero(v)
 return [] if not len(ids) else np.split(ids,np.flatnonzero(np.diff(ids)>1)+1)

def longest_gap(v):
 return max((len(r) for r in runs(~v)),default=0)

def check_path(a,x0,y0,x1,y1,dashed=False):
 b=a<180
 if x0==x1:
  v=b[min(y0,y1):max(y0,y1)+1,x0-1:x0+2].any(axis=1)
 else:
  v=b[y0-1:y0+2,min(x0,x1):max(x0,x1)+1].any(axis=0)
 gap=longest_gap(v)
 if gap>(7 if dashed else 0):raise ValueError('Broken '+('dashed' if dashed else 'solid')+' connection '+str((x0,y0,x1,y1,gap)))
 if v.mean() < (.45 if dashed else 1):raise ValueError('Missing connection')
 return {'box':[min(x0,x1)-1,min(y0,y1)-1,max(x0,x1)+2,max(y0,y1)+2],'max_blank_run':gap,'dashed':dashed}

def main_structure(a,frames,aa,bs,arrows):
 at,ab,bt,bb=frames;n=len(aa);checks=[]
 if arrows:raise ValueError('Correspondence must be inferred, not supplied')
 for bottom,centers,dashed in [(ab,aa,True),(bb,bs,False)]:
  for x in centers:
   for dx in [-14,14]:checks.append(check_path(a,x+dx,bottom+3,x+dx,bottom+29,dashed))
   checks.append(check_path(a,x-13,bottom+30,x+13,bottom+30,dashed))
  band=a[bottom+4:bottom+31]<180
  allowed=np.zeros(band.shape[1],bool)
  for x in centers:allowed[x-17:x+18]=True
  if np.count_nonzero(band[:,~allowed])>12:raise ValueError('Extra registration ink outside recovered tabs')
 candidates=[]
 for y in range(bb+45,a.shape[0]-100):
  rr=[r for r in runs(a[y]<100) if 35<len(r)<200]
  if len(rr)>=3:candidates.append((y,rr))
 if not candidates:raise ValueError('Missing answer slots')
 y,rr=max(candidates,key=lambda z:len(z[1]))
 if len(rr)!=n:raise ValueError('Answer slot count differs from card count')
 # The area between the windows must be empty: no correspondence marks are read.
 if np.any(a[bb+35:y-3]<240):raise ValueError('Unexpected ink between frames and answer slots')
 return {'connections':checks,'answer_slots':len(rr),'answer_slot_y':y,'main_arrows':0,
         'correspondence_area_blank':True,'old_frame_overlay_in_b':False}

def tight(mask):
 yy,xx=np.where(mask)
 if not len(xx):raise ValueError('Missing required example glyph')
 return mask[yy.min():yy.max()+1,xx.min():xx.max()+1]

def norm(mask):
 return np.array(Image.fromarray(tight(mask)).resize((40,52),Image.Resampling.NEAREST),bool)

def read_glyph(a,box,alphabet):
 x0,y0,x1,y1=box;crop=norm(a[y0:y1,x0:x1]<100)
 fonts=[ImageFont.truetype(str(Path(__file__).parent/f),200,layout_engine=ImageFont.Layout.BASIC) for f in ['DejaVuSans-Bold.ttf','DejaVuSans.ttf']]
 scores=[]
 for ch in alphabet:
  sc=[]
  for font in fonts:
   im=Image.new('L',(300,300),255);ImageDraw.Draw(im).text((20,0),ch,font=font,fill=0)
   sc.append(float(np.mean(crop!=norm(np.array(im)<100))))
  scores.append((min(sc),ch))
 scores.sort()
 if scores[0][0]>.16 or scores[1][0]-scores[0][0]<.025:raise ValueError('Illegible/ambiguous example glyph '+str(box)+str(scores[:2]))
 return scores[0][1]

def example_structure(images,question_name):
 files=[p for p in Path(images).glob('*.png') if p.name!=question_name]
 if len(files)!=1:raise ValueError('Need one complete example page')
 a=np.asarray(Image.open(files[0]).convert('L'))
 # Read rank digits and the three ordered output glyphs independently.
 ranks=[int(read_glyph(a,(x-20,969,x+20,1004),string.digits)) for x in [350,820,1250]]
 out_ranks=[int(read_glyph(a,(x-15,1168,x+15,1198),string.digits)) for x in [1083,1168,1253]]
 out=[read_glyph(a,(x-20,1110,x+20,1142),string.ascii_uppercase) for x in [1083,1168,1253]]
 shaft=[r for r in runs((a[953:956]<100).any(axis=0)) if len(r)>40]
 if len(shaft)!=3 or sorted(ranks)!=[1,2,3] or out_ranks!=[1,2,3]:raise ValueError('Incomplete ranking example')
 lengths=[int(r[-1]-r[0]) for r in shaft]
 descending=all(lengths[ranks.index(i)]>lengths[ranks.index(i+1)] for i in [1,2])
 ascending=all(lengths[ranks.index(i)]<lengths[ranks.index(i+1)] for i in [1,2])
 if not(descending or ascending):raise ValueError('Example gives no monotone displacement order')
 # The illustrated union is tested directly, without assuming H.
 left=a[1090:1201,205:315]<80;middle=a[1090:1201,435:545]<80;merged=a[1090:1201,725:835]<80
 if np.count_nonzero((left|middle)!=merged)>40:raise ValueError('Fragment union example is incomplete')
 glyph=read_glyph(a,(725,1090,835,1201),string.ascii_uppercase)
 if glyph!=out[0]:raise ValueError('Merge result disagrees with first output letter')
 # Read the exposed side labels and compare their indicated output rank.
 # The first explanatory letter is beside its rank; the last stays below it.
 # These are visual reading windows, not glyph values or puzzle data.
 side_boxes=[(374,971,414,1004),(1230,1014,1270,1047)]
 side=[read_glyph(a,box,string.ascii_uppercase) for box in side_boxes]
 if out[ranks[0]-1]!=side[0] or out[ranks[2]-1]!=side[1]:raise ValueError('Example output not consistent with its rank labels')
 # The indirect example shows the same composited ink before and after slats.
 union_checks=[]
 for top in [1370,1670]:
  before=a[top+4:top+176,434:726]
  after=a[top+4:top+176,974:1266]
  exposed=~((after>200)&(after<230))
  mismatch=int(np.count_nonzero(((before<80)!=(after<80))&exposed))
  if mismatch>40:raise ValueError('Indirect union example does not preserve exposed ink')
  if np.any(a[top:top+205,136:400]<180):raise ValueError('Unexpected marks in the specimen area')
  union_checks.append({'top':top,'exposed_pixel_mismatch':mismatch})
 return {'indirect_union_checks':union_checks,'separate_source_specimens':False,'ranks':ranks,'output_ranks':out_ranks,'output_letters':out,'lengths':lengths,'descending':descending,'merge_letter':glyph,'side_letters':side,'side_label_boxes':side_boxes}
