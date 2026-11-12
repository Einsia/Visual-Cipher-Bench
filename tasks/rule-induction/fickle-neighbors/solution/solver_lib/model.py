from itertools import product
from collections import Counter
import time
DIRS=[(-1,0),(0,1),(1,0),(0,-1)]
BASE={'turn':0,'stride':1,'axis':0,'anchor':0,'policy':2,'mark':1,'rides':False,'wrap':False,'order':0,'rotation':'align','rotate_scope':'column','controller':'source','sense':1,'rotation_timing':'after'}
# policy 0 right,1 left,2 white-right/grey-left,3 opposite,4 arrow-sign,5 opposite-arrow-sign.
def unpack(b):
 n=b['size'];a=[None]*(n*n)
 for t in b['cells']:a[t['r']*n+t['c']]=(t['letter'],'NESW'.index(t['dir']),t['visited'],t['r']*n+t['c'])
 return a,b['token'][0]*n+b['token'][1],n

def pack(a,p,n):return {'size':n,'token':list(divmod(p,n)),'cells':[{'r':i//n,'c':i%n,'letter':t[0],'dir':'NESW'[t[1]],'visited':t[2]} for i,t in enumerate(a) if t]}
def normal(b):return b['size'],tuple(b['token']),tuple(sorted((t['r'],t['c'],t['letter'],t['dir'],t['visited']) for t in b['cells']))
def run(board,pa=None,limit=256):
 pa={**BASE,**(pa or {})};a,p,n=unpack(board);initial=a[:];trace=[];frames=[pack(a,p,n)];seen=set()
 for k in range(limit):
  if a[p] is None:
   final=pack(a,p,n);return {'status':'stop','answer':''.join(t[0] for t in a if t and t[2]),'final':final,'trace':trace,'frames':frames,'initial':initial,'flat':a}
  key=(tuple(a),p)
  if key in seen:return {'status':'cycle','trace':trace}
  seen.add(key);t=a[p];d=(t[1]+pa['turn'])%4;dr,dc=DIRS[d];r,c=divmod(p,n);rr=r+dr*pa['stride'];cc=c+dc*pa['stride']
  if pa['wrap']:rr%=n;cc%=n
  elif not(0<=rr<n and 0<=cc<n):return {'status':'outside','trace':trace}
  q=rr*n+cc;source=p;old=t[2]
  mark=[True,not old,False,old][pa['mark']]
  shift=[1,-1,1 if not old else -1,-1 if not old else 1,1 if d in (0,1) else -1,-1 if d in (0,1) else 1][pa['policy']]
  # order 1: shift then flip at old departure coordinate; order 2: early stop before shifting.
  if pa['order']!=1:a[source]=(t[0],t[1],mark,t[3])
  p=q
  if pa['order']==2 and a[q] is None:return {'status':'early','trace':trace}
  ar,ac=divmod(source if pa['anchor']==0 else q,n)
  ids=[ar*n+j for j in range(n)] if pa['axis']==0 else [j*n+ac for j in range(n)]
  oldrow=[a[i] for i in ids]
  for j,i in enumerate(ids):a[i]=oldrow[(j-shift)%n]
  # The transported controller aligns its arrow to the saved departing direction.
  rot=0;ctrl=source if pa['controller']=='source' else q;cr,cc0=divmod(ctrl,n)
  ctrlcard=a[ctrl]
  if pa['rotation']=='align' and ctrlcard:rot=(d-ctrlcard[1])*pa['sense']%4
  elif isinstance(pa['rotation'],int):rot=pa['rotation']%4
  if pa['rotate_scope']=='column':rotids=[j*n+c for j in range(n)]
  elif pa['rotate_scope']=='row':rotids=[r*n+j for j in range(n)]
  elif pa['rotate_scope']=='controller':rotids=[ctrl]
  else:rotids=list(range(n*n))
  for idx in rotids:
   if a[idx]:v=a[idx];a[idx]=(v[0],(v[1]+rot)%4,v[2],v[3])
  if pa['rides'] and p in ids:p=ids[(ids.index(p)+shift)%n]
  if pa['order']==1 and a[source]:
   v=a[source];a[source]=(v[0],v[1],[True,not v[2],False,v[2]][pa['mark']],v[3])
  trace.append({'source':list(divmod(source,n)),'destination':list(divmod(q,n)),'letter':t[0],'identity':t[3],'old_grey':old,'new_grey':mark,'row_shift':shift,'direction':'NESW'[d],'rotation':rot,'controller':ctrl,'controller_present':ctrlcard is not None,'controller_before_dir':None if ctrlcard is None else 'NESW'[ctrlcard[1]],'rotated_column':c})
  frames.append(pack(a,p,n))
 return {'status':'limit','trace':trace}
def family():
 # Convention-level compass/transport variants crossed with relational rotation hypotheses.
 names=['turn','stride','axis','anchor','policy','mark','rides','wrap','order']
 for v in product(range(4),(1,2),(0,1),(0,1),range(6),(0,1),(False,),(False,True),(0,)):
  core=dict(zip(names,v))
  for rot in (0,1,2,3,'align'):
   if isinstance(rot,int):
    for scope in ('column','row','controller','all'):yield {**BASE,**core,'rotation':rot,'rotate_scope':scope}
   else:
    for scope,controller,sense in product(('column','row','controller','all'),('source','destination'),(1,-1)):
     yield {**BASE,**core,'rotation':rot,'rotate_scope':scope,'controller':controller,'sense':sense}
def fit(spec):
 begin=time.perf_counter();counts=[0]*len(spec['examples']);survivors=[];total=0
 for pa in family():
  total+=1
  for i,ex in enumerate(spec['examples']):
   o=run(ex['before'],pa)
   if o['status']!='stop' or normal(o['final'])!=normal(ex['after']):break
   counts[i]+=1
  else:survivors.append(pa)
 outputs=sorted({run(spec['target'],p).get('answer','<failure>') for p in survivors})
 return {'tested':total,'survivors_after_each':counts,'survivors':survivors,'outputs':outputs,'seconds':time.perf_counter()-begin}
def independent(board):
 # Separate identity-position representation; update arrow dictionaries by actual positions.
 start=time.perf_counter();n=board['size'];pos={t['r']*n+t['c']:(t['r'],t['c']) for t in board['cells']};letters={t['r']*n+t['c']:t['letter'] for t in board['cells']};directions={t['r']*n+t['c']:'NESW'.index(t['dir']) for t in board['cells']};grey={t['r']*n+t['c']:t['visited'] for t in board['cells']};r,c=board['token'];trail=[]
 for step in range(256):
  hits=[k for k,v in pos.items() if v==(r,c)]
  if not hits:break
  k=hits[0];d=directions[k];old=grey[k];grey[k]=not old;dr,dc=DIRS[d];rr,cc=r+dr,c+dc
  if not(0<=rr<n and 0<=cc<n):return {'status':'outside'}
  delta=-1 if old else 1
  pos={key:(row,(col+delta)%n) if row==r else (row,col) for key,(row,col) in pos.items()}
  control=[key for key,v in pos.items() if v==(r,c)]
  rotation=(d-directions[control[0]])%4 if control else 0
  for key,(row,col) in pos.items():
   if col==c:directions[key]=(directions[key]+rotation)%4
  trail.append(letters[k]);r,c=rr,cc
 else:return {'status':'limit'}
 ordered=sorted(pos,key=lambda k:pos[k]);answer=''.join(letters[k] for k in ordered if grey[k]);return {'status':'stop','answer':answer,'steps':len(trail),'chronological':''.join(trail),'seconds':time.perf_counter()-start}

def readouts(result):
 a=result['flat'];n=result['final']['size'];out={}
 for axis in (0,1):
  for rev1 in (False,True):
   for rev2 in (False,True):
    rows=list(range(n))[::(-1 if rev1 else 1)];cols=list(range(n))[::(-1 if rev2 else 1)]
    ids=[i*n+j if axis==0 else j*n+i for i in rows for j in cols]
    out[f'axis{axis}_outer{int(rev1)}_inner{int(rev2)}']=''.join(a[i][0] for i in ids if a[i] and a[i][2])
 marks={t[3] for t in a if t and t[2]};out['initial_order']=''.join(t[0] for t in result['initial'] if t and t[3] in marks)
 out['chronology']=''.join(t['letter'] for t in result['trace']);seen=set();first=[]
 for t in result['trace']:
  if t['identity'] not in seen:seen.add(t['identity']);first.append(t['letter'])
 out['first_visit']=''.join(first);out['reverse_first_visit']=''.join(first)[::-1]
 return out
