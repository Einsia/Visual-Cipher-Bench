"""Pixel checks for diagram conventions."""
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

def canonical(a):
 # Invert the publicly visible quarter-turn of the upright scan rack.
 return np.rot90(a,-1)[:,50:1750]

def arrow_endpoint(a,left,right,y,aa,bs):
 # Follow a long shaft to a measured B height, including an orthogonal tip return.
 # All lane/turn positions are recovered from ink.
 ai=[i for i,x in enumerate(aa) if abs(x-left)<=3]
 if len(ai)!=1:return None
 bi=[i for i,x in enumerate(bs) if abs(x-right)<=3]
 if len(bi)==1:return ai[0],bi[0],{'a':aa[ai[0]],'b':right,'y':y}
 matches=[]
 for j,z in enumerate(bs):
  if not 8<z-right<64:continue
  rows=[]
  for tip_y in range(max(0,y-64),min(a.shape[0]-7,y+65)):
   if abs(tip_y-y)<8:continue
   try:
    check_path(a,right,y,right,tip_y)
    check_path(a,right,tip_y,z-8,tip_y)
   except ValueError:continue
   head=a[tip_y-6:tip_y+7,z-10:z+2]<180
   if head.sum()>=30 and head[:,8:11].any():rows.append(tip_y)
  if rows:
   tip_y=int(round(np.mean(rows)))
   # Refine the tip with the same solid-row criterion as a straight arrow.
   spans=[r for r in runs(a[tip_y]<160) if r[0]<=right+2 and abs(r[-1]-z)<=3]
   if len(spans)==1:
    matches.append((ai[0],j,{'a':aa[ai[0]],'b':int(spans[0][-1]),'y':y,'turn':right,'tip_y':tip_y}))
 if len(matches)>1:raise ValueError('Ambiguous routed arrow endpoint')
 return matches[0] if matches else None

def solid_stem(a,x,bottom,end):
 # Infer routing from pixels.
 b=a<180
 try:
  return [check_path(a,x,bottom,x,end)],[]
 except ValueError:
  pass
 spans=runs(b[bottom+6:bottom+15].all(axis=0))
 candidates=[int(round(r.mean())) for r in spans if len(r)<=4]
 for shifted in sorted(candidates,key=lambda z:abs(z-x)):
  if not 3<abs(shifted-x)<64:continue
  try:entry=check_path(a,x,bottom,shifted,bottom)
  except ValueError:continue
  turns=[]
  for y in range(bottom+20,end-9):
   try:
    check_path(a,shifted,bottom,shifted,y)
    check_path(a,shifted,y,x,y)
    check_path(a,x,y,x,end)
   except ValueError:continue
   turns.append(y)
  if turns:
   turn=int(round(np.mean(turns)))
   return [entry,check_path(a,shifted,bottom,shifted,turn),check_path(a,shifted,turn,x,turn),check_path(a,x,turn,x,end)],[turn]
 raise ValueError('No connected solid stem/dogleg '+str((x,bottom,end)))

def main_structure(a,frames,aa,bs,arrows,native):
 at,ab,bt,bb=frames;n=len(aa);checks=[];turn_rows=[]
 for ar in arrows:
  x,z,y=ar['a'],ar['b'],ar['y']
  tip_y=ar.get('tip_y',y)
  if 'turn' in ar:
   turn=ar['turn']
   checks.extend([check_path(a,x+2,y,turn,y),check_path(a,turn,y,turn,tip_y),check_path(a,turn,tip_y,z-8,tip_y)])
  else:checks.append(check_path(a,x+2,y,z-8,y))
  route,turns=solid_stem(a,z,bb+30,tip_y+7);checks.extend(route);turn_rows.extend(turns)
  # Small dashed registration boxes use a fixed layout; centers still come from A pixels.
  near,far=bb+50,bb+66
  for u,v in [((x-6,near),(x+6,near)),((x+6,near),(x+6,far)),((x+6,far),(x-6,far)),((x-6,far),(x-6,near))]:
   checks.append(check_path(a,*u,*v,True))
  checks.append(check_path(a,x,far,x,y+7,True))
  # A rightward arrow head must taper towards its endpoint.
  head=(a[tip_y-6:tip_y+7,z-10:z+2]<180)
  if head.sum()<30 or not head[:,8:11].any():raise ValueError('Missing arrow head')
 # All tabs, including dashed ghost tabs, have both sides and a bottom.
 for bottom,centers,dashed in [(ab,aa,True),(bb,bs,False)]:
  for x in centers:
   for dx in [-14,14]:checks.append(check_path(a,x+dx,bottom+3,x+dx,bottom+29,dashed))
   checks.append(check_path(a,x-13,bottom+30,x+13,bottom+30,dashed))
 # Additional registration marks outside known tab positions must not be ignored.
 for bottom,centers in [(ab,aa),(bb,aa+bs)]:
  band=(a[bottom+4:bottom+28]<180).copy();band[8:13]=False;band[:,:136]=False;band[:,1564:]=False
  allowed=np.zeros(band.shape[1],bool)
  for x in centers:allowed[x-17:x+18]=True
  if np.count_nonzero(band[:,~allowed])>12:raise ValueError('Extra registration ink outside recovered tabs')
 # Every arrow-lane row containing a long solid run must have a recovered arrow.
 y0=bb+45;y1=max(q['y'] for q in arrows)+20
 for y in range(y0,y1):
  rr=[r for r in runs(a[y]<180) if len(r)>25]
  if rr and not any(abs(y-lane)<=6 for q in arrows for lane in [q['y'],q.get('tip_y',q['y'])]) and not any(abs(y-turn)<=2 for turn in turn_rows):raise ValueError('Extra arrow or horizontal guide')
 # Eight physical record slots are detected in the separate native column.
 slots=[]
 for y in range(400,1500):
  rr=[r for r in runs(native[y,1850:2110]<80) if 100<len(r)<160]
  if rr and (not slots or y>slots[-1][-1]+1):slots.append([])
  if rr:slots[-1].append(y)
 if len(slots)!=n:raise ValueError('Record slot count differs from carriers')
 return {'connections':checks,'solid_dogleg_rows':turn_rows,'independent_a_tabs':len(aa),'answer_slots':len(slots),'answer_slot_rows':[int(np.mean(q)) for q in slots]}

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
 if len(files)!=1:raise ValueError('Need one calibration page')
 native=np.asarray(Image.open(files[0]).convert('L'));a=canonical(native)
 # Diagram-lane and output regions are format conventions.
 shaft=[r for r in runs((a[949:952]<160).any(axis=0)) if len(r)>40]
 if len(shaft)!=3:raise ValueError('Expected three calibration travel arrows')
 centers=[int((r[0]+r[-1])/2) for r in shaft]
 ranks=[int(read_glyph(a,(x-20,970,x+20,1005),string.digits)) for x in centers]
 lengths=[int(r[-1]-r[0]) for r in shaft]
 out_ranks=[int(read_glyph(native,(x-20,545,x+20,580),string.digits)) for x in [1260,1370,1480]]
 out=[read_glyph(native,(x-40,455,x+40,515),string.ascii_uppercase) for x in [1260,1370,1480]]
 if sorted(ranks)!=[1,2,3] or out_ranks!=[1,2,3]:raise ValueError('Incomplete calibration ranks')
 descending=all(lengths[ranks.index(i)]>lengths[ranks.index(i+1)] for i in [1,2])
 ascending=all(lengths[ranks.index(i)]<lengths[ranks.index(i+1)] for i in [1,2])
 if not(descending or ascending):raise ValueError('No strict calibration order')
 return {'ranks':ranks,'output_ranks':out_ranks,'output_letters':out,'lengths':lengths,'descending':descending}
