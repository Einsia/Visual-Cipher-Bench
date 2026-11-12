"""Independent forward-circuit SAT encoding with whole-letter constraints.
Unlike endpoint tuple propagation, it explicitly represents every intermediate bit.
"""
import time
from model import PERMS,flat,FUNCTIONS
from coupled import LABELS,GLYPHS
from joint_model import FNS

def solve_circuit_joint(obs,targets,geoms,limit=2,node_limit=200000):
 start=time.perf_counter();varmap={};clauses=[]
 def var(key):
  if key not in varmap:varmap[key]=len(varmap)+1
  return varmap[key]
 def neg(v):return not v if isinstance(v,bool) else -v
 def clause(*xs):
  if any(x is True for x in xs):return
  ints=set(x for x in xs if x is not False)
  if any(-x in ints for x in ints):return
  p=n=0
  for x in ints:
   if x>0:p|=1<<(x-1)
   else:n|=1<<(-x-1)
  clauses.append((p,n))
 table={(s,i,b):var(('f',s,i,b)) for s in range(2) for i in range(25) for b in range(2)}
 tablemask=(1<<len(varmap))-1
 letters=[[var(('letter',j,k)) for k in range(len(LABELS))] for j in range(len(targets))]
 for ls in letters:
  clause(*ls)
  for i in range(len(ls)):
   for j in range(i):clause(-ls[i],-ls[j])
 for ei,e in enumerate(obs+targets):
  state=[bool(x) for x in flat(e['before'])]
  for k,s in enumerate(e['symbols']):
   out=[]
   for i in range(25):
    a=state[PERMS[geoms[s]][i]];z=var(('state',ei,k,i));f0=table[s,i,0];f1=table[s,i,1]
    clause(a,-f0,z);clause(a,f0,-z);clause(neg(a),-f1,z);clause(neg(a),f1,-z);out.append(z)
   state=out
  if ei<len(obs):
   for i,want in enumerate(flat(e['after'])):clause(state[i] if want else -state[i])
  else:
   for li,lvar in enumerate(letters[ei-len(obs)]):
    for i,want in enumerate(GLYPHS[li]):clause(-lvar,state[i] if want else -state[i])
 nodes=0;visits=0;aborted=False;sols=[]
 def dpll(cs,true,false):
  nonlocal nodes,visits,aborted
  nodes+=1
  if nodes>node_limit:aborted=True;return
  while True:
   remaining=[];up=un=0
   for p,n in cs:
    visits+=1
    if (p&true) or (n&false):continue
    p&=~false;n&=~true;bits=p|n
    if not bits:return
    if bits&(bits-1)==0:up|=p;un|=n
    else:remaining.append((p,n))
   if (up&un) or (up&false) or (un&true):return
   if not(up|un):cs=remaining;break
   true|=up;false|=un;cs=remaining
  if not cs:return true,false
  # Short-clause branching; function-table bits first when present.
  candidates=[(p|n)&tablemask for p,n in cs if (p|n)&tablemask]
  if candidates:
   shortest=min(x.bit_count() for x in candidates);freq={}
   for bits in candidates:
    if bits.bit_count()!=shortest:continue
    while bits:
     bit=bits&-bits;bits-=bit;freq[bit]=freq.get(bit,0)+1
   bit=max(freq,key=freq.get)
  else:
   bits=min((p|n for p,n in cs),key=int.bit_count);bit=bits&-bits
  r=dpll(cs,true|bit,false)
  if r is not None or aborted:return r
  return dpll(cs,true,false|bit)
 while len(sols)<limit:
  r=dpll(clauses,0,0)
  if r is None:break
  true,false=r;fns=[]
  for s in range(2):
   for i in range(25):
    vals=tuple(int(bool(true&(1<<(table[s,i,b]-1)))) for b in range(2))
    fns.append(next(j for j,f in enumerate(FNS) if FUNCTIONS[f]==vals))
  inds=[]
  for ls in letters:
   hit=[i for i,v in enumerate(ls) if true & (1<<(v-1))]
   assert len(hit)==1
   inds.append(hit[0])
  sols.append(fns+inds)
  clause(*[v for ls,i in zip(letters,inds) for j,v in enumerate(ls) if LABELS[j]!=LABELS[i]])
 return {'geoms':list(geoms),'solutions':sols,'nodes':nodes,'clause_visits':visits,'clauses':len(clauses),'variables':len(varmap),'aborted':aborted,'exhausted':len(sols)<limit and not aborted,'seconds':time.perf_counter()-start}
