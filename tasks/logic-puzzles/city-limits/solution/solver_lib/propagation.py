"""Candidate-domain propagation, a second solver for cross-checking the main search.
Uses complete connected shapes, mandatory cell supports, source/receiver/lookup
supports, incoming/outgoing permutation propagation, and short-cycle rejection.
"""
import time

def solve_propagation(g, limit=None, time_limit=None, strict_walls=True):
 roots=dict(zip(g['ids'],g['seeds']));dirs=dict(zip(g['ids'],g['directions']));walls={frozenset(e) for e in g['walls']}
 adj={c:[d for d in range(36) if (abs(c//6-d//6)+abs(c%6-d%6)==1) and frozenset((c,d)) not in walls] for c in range(36)}
 rootmask=sum(1<<r for r in roots.values());shapes={};started=time.monotonic();first=None;exhaustive=True;reason='completed'
 for i,r in roots.items():
  cur={1<<r};out=[]
  for a in range(1,11):
   out.extend((m,a) for m in cur);nxt=set()
   if a<10:
    for m in cur:
     frontier=set()
     for c in range(36):
      if m>>c&1:frontier.update(adj[c])
     for c in frontier:
      if not (m>>c&1) and not(rootmask>>c&1):
       mm=m|1<<c
       if strict_walls and any(all(mm>>v&1 for v in e) for e in walls):continue
       nxt.add(mm)
   cur=nxt
  shapes[i]=out
 class Stopped(Exception):pass
 C=shapes
 cellbits={};areas={}
 for i in roots:
  cellbits[i]=[0]*36;areas[i]={a:0 for a in range(1,11)}
  for n,(m,a) in enumerate(C[i]):
   bit=1<<n;areas[i][a]|=bit
   for c in range(36):
    if m>>c&1:cellbits[i][c]|=bit
 # precompute (i,a,dest,t): origins with size a excluding destination; t lookup size
 routes={i:[] for i in roots}
 for i,r in roots.items():
  for d in range(1,6):
   dest=r+dirs[i]*d
   if not 0<=dest<36 or dirs[i] in [-1,1] and dest//6!=r//6:continue
   for a in range(1,11):
    cand=areas[i][a]&~cellbits[i][dest]
    if not cand:continue
    ts=[t for t in [a-d,a+d] if 1<=t<=10]
    routes[i].append((a,dest,ts,cand))

 nodes=0;solutions=[]
 def prop(dom,edges):
  while True:
   old=dom.copy();oldedges=edges.copy()
   sizes={i:[a for a in range(1,11) if dom[i]&areas[i][a]] for i in roots}
   if sum(min(s) for s in sizes.values())>36 or sum(max(s) for s in sizes.values())<36:return
   # force mandatory cells and unique supports
   for cell in range(36):
    sup=[i for i in roots if dom[i]&cellbits[i][cell]]
    if not sup:return
    forced=[i for i in sup if dom[i]&~cellbits[i][cell]==0]
    if len(forced)>1:return
    if forced:
     for j in sup:
      if j!=forced[0]:dom[j]&=~cellbits[j][cell]
    elif len(sup)==1:
     i=sup[0];dom[i]&=cellbits[i][cell]
   if any(not x for x in dom.values()):return
   # destination jump supports
   for i in roots:
    good=0;newedge=set()
    for a,dest,ts,cand in routes[i]:
     possible=cand&dom[i]
     if not possible:continue
     for j in edges[i]:
      works=False
      for b in sizes[j]:
       if b==i or not dom[j]&areas[j][b]&cellbits[j][dest]:continue
       if b==j:
        if b not in ts:continue
       elif not any(t in sizes[b] for t in ts):continue
       works=True;break
      if works:
       good|=possible;newedge.add(j)
    dom[i]&=good;edges[i]=newedge
    if not dom[i] or not newedge:return
   # permutation constraints
   forced={i:next(iter(es)) for i,es in edges.items() if len(es)==1}
   if len(set(forced.values()))!=len(forced):return
   for i,j in forced.items():
    for k in roots:
     if k!=i:edges[k]=edges[k]-{j}
   for j in roots:
    incoming=[i for i in roots if j in edges[i]]
    if not incoming:return
    if len(incoming)==1:edges[incoming[0]]={j}
   for st in forced:
    seen=set();p=st
    while p in forced and p not in seen:seen.add(p);p=forced[p]
    if p in seen and len(seen)<10:return
   if dom==old and edges==oldedges:return dom,edges

 def solve(dom,edges):
  nonlocal nodes,first
  nodes+=1
  if nodes%100==0 and time_limit is not None and time.monotonic()-started>time_limit:raise Stopped('time_limit')
  result=prop(dom.copy(),{i:set(es) for i,es in edges.items()})
  if not result:return
  dom,edges=result
  if all(x.bit_count()==1 for x in dom.values()):
   sol={i:C[i][x.bit_length()-1] for i,x in dom.items()}
   if sum(a for m,a in sol.values())!=36:return
   # enumerate Hamilton cycles
   def tour(path):
    nonlocal first
    i=path[-1]
    if len(path)==10:
     if 1 in edges[i]:
      order=path+[1];letters=''
      from model import place_letters
      allocated=place_letters(g,[[v for v in range(36) if sol[i][0]>>v&1] for i in roots])
      for i,j in zip(order,order[1:]):
       d=abs(sol[i][1]-sol[sol[j][1]][1]);dest=roots[i]+dirs[i]*d
       if not sol[j][0]>>dest&1:return
       letters+=allocated[dest]
      solutions.append((sol,order,letters))
      if first is None:first={'seconds':time.monotonic()-started,'nodes':nodes,'answer':letters}
      if limit and len(solutions)>=limit:raise Stopped('solution_limit')
     return
    for j in edges[i]:
     if j not in path:tour(path+[j])
   tour([1]);return
  i=min((i for i in roots if dom[i].bit_count()>1),key=lambda i:dom[i].bit_count())
  opts=dom[i]
  while opts:
   bit=opts&-opts;opts^=bit
   m,a=C[i][bit.bit_length()-1];new=dom.copy();new[i]=bit
   for j in roots:
    if j==i:continue
    bad=0
    for cell in range(36):
     if m>>cell&1:bad|=cellbits[j][cell]
    new[j]&=~bad
   if all(new.values()):solve(new,edges)
 try:
  solve({i:(1<<len(C[i]))-1 for i in roots},{i:set(roots)-{i} for i in roots})
 except Stopped as e:exhaustive=False;reason=str(e)
 models=[dict(regions=[tuple(sol[i]) for i in roots],order=[i-1 for i in order[:-1]]) for sol,order,letters in solutions]
 stats=dict(route='public-trial fixed-point domain propagation',exhaustive=exhaustive,reason=reason,nodes=nodes,solution_count=len(solutions),first_solution=first,seconds=time.monotonic()-started,candidate_regions=sum(len(c) for c in C.values()),option_counts=[len(c) for c in C.values()],strict_walls=strict_walls)
 return models,stats
