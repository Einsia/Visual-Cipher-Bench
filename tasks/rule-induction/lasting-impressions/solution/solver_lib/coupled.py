"""Joint inference of composition rules and unknown capital impressions.
No answer or word list is used. All four unary Boolean maps are permitted.
"""
import itertools,time
import numpy as np
from model import PERMS,FONT,flat,FUNCTIONS
from joint_model import constraints,ASSIGN,FT,FNS
from alphabet import LABELS,GLYPHS

def compile_constraints(obs,targets,geoms):
 cs=constraints(obs,geoms)
 for ti,e in enumerate(targets):
  before=flat(e['before']);seq=e['symbols']
  for dest in range(25):
   ids=[];pos=dest
   for s in reversed(seq):ids.append(25*s+pos);pos=PERMS[geoms[s]][pos]
   variables=sorted(set(ids));indices=[variables.index(i) for i in ids]
   a=ASSIGN[len(variables)];v=np.full(len(a),before[pos],dtype=np.uint8)
   for k in reversed(indices):v=FT[a[:,k],v]
   ai,li=np.nonzero(v[:,None]==GLYPHS[:,dest][None,:])
   table=np.column_stack((a[ai],li)).astype(np.uint8)
   cs.append((variables+[50+ti],table))
 return cs

def solve_joint(obs,targets,geoms,limit=2,blocked=(),node_limit=100000,fnmask=15):
 start=time.perf_counter();cs=compile_constraints(obs,targets,geoms)
 # Precompute bit masks in tables (function domain 4; capital domain <=63).
 cs=[(ids,np.left_shift(np.uint64(1),a.astype(np.uint64))) for ids,a in cs]
 nodes=visits=0;solutions=[];blocked=list(blocked);aborted=False
 init=[fnmask]*50+[sum(1<<j for j,c in enumerate(LABELS) if c in t.get('letter_candidates',LABELS)) for t in targets]
 def propagate(dom):
  nonlocal visits
  again=True
  while again:
   again=False
   for ids,table in cs:
    visits+=1
    ok=np.all((table & np.array([dom[i] for i in ids],dtype=np.uint64))!=0,axis=1)
    if not ok.any():return False
    masks=np.bitwise_or.reduce(table[ok],axis=0)
    for v,m in zip(ids,masks):
     m=int(m)
     if dom[v]!=m:dom[v]=m;again=True
   for forbid in blocked:
    unresolved=[];excluded=False
    for k,w in enumerate(forbid):
     d=dom[50+k];bit=sum(1<<j for j,c in enumerate(LABELS) if c==LABELS[w])
     if not(d&bit):excluded=True;break
     if d & ~bit:unresolved.append((50+k,bit))
    if excluded:continue
    if not unresolved:return False
    if len(unresolved)==1:
     i,bit=unresolved[0];dom[i]&=~bit;again=True
  return True
 def search(dom):
  nonlocal nodes,aborted
  nodes+=1
  if nodes>node_limit:aborted=True;return
  if not propagate(dom):return
  undec=[i for i,d in enumerate(dom) if d.bit_count()>1]
  if not undec:return [d.bit_length()-1 for d in dom]
  i=min(undec,key=lambda i:(dom[i].bit_count(),i<50,i))
  bits=dom[i]
  while bits:
   b=bits&-bits;bits-=b;d=dom[:];d[i]=b
   sol=search(d)
   if sol is not None:return sol
   if aborted:return
 while len(solutions)<limit:
  sol=search(init[:])
  if sol is None:break
  solutions.append(sol);blocked.append(tuple(sol[50:]))
 return {'geoms':list(geoms),'solutions':solutions,'nodes':nodes,'constraint_visits':visits,'aborted':aborted,'exhausted':len(solutions)<limit and not aborted,'seconds':time.perf_counter()-start}
