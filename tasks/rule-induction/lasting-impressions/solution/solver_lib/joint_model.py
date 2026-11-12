import itertools,time,sys
from pathlib import Path
import numpy as np
from model import PERMS,FONT,flat,matrix,forward,FUNCTIONS
FNS=list(FUNCTIONS)
FT=np.array([FUNCTIONS[n] for n in FNS],dtype=np.uint8)
ASSIGN={n:np.array(list(itertools.product(range(4),repeat=n)),dtype=np.uint8) for n in range(1,6)}

def constraints(observations,geoms):
 cs=[]
 for e in observations:
  before=flat(e['before']);after=flat(e['after']);seq=e['symbols']
  for dest,want in enumerate(after):
   ids=[];pos=dest
   for s in reversed(seq):
    ids.append(25*s+pos);pos=PERMS[geoms[s]][pos]
   variables=sorted(set(ids));indices=[variables.index(i) for i in ids]
   assignments=ASSIGN[len(variables)]
   values=np.full(len(assignments),before[pos],dtype=np.uint8)
   for k in reversed(indices):values=FT[assignments[:,k],values]
   allowed=assignments[values==want]
   cs.append((variables,allowed))
 return cs

def solve(observations,geoms,limit=10000):
 cs=constraints(observations,geoms)
 nodes=0;prop=0;sols=[]
 def rec(domains):
  nonlocal nodes,prop
  nodes+=1
  again=True
  while again:
   again=False
   for ids,table in cs:
    prop+=1
    valid=np.ones(len(table),dtype=bool)
    for j,v in enumerate(ids):valid &= ((1<<table[:,j]) & domains[v])!=0
    if not valid.any():return
    t=table[valid]
    for j,v in enumerate(ids):
     mask=int(np.bitwise_or.reduce(1<<t[:,j]))
     if mask!=domains[v]:domains[v]=mask;again=True
  undec=[i for i,v in enumerate(domains) if v.bit_count()>1]
  if not undec:
   sols.append([v.bit_length()-1 for v in domains]);return
  pick=min(undec,key=lambda i:domains[i].bit_count())
  for value in range(4):
   if domains[pick] & (1<<value):
    d=domains[:];d[pick]=1<<value;rec(d)
    if len(sols)>=limit: return
 rec([15]*50)
 return {'geoms':geoms,'models':sols,'nodes':nodes,'constraint_visits':prop,'truncated':len(sols)>=limit}

def model_from_result(r,values):
 return {s:{'geometry':r['geoms'][i],'functions':[FNS[v] for v in values[25*i:25*(i+1)]]} for i,s in enumerate(('diamond','circle'))}
