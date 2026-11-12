"""Build the constraint network exclusively from recovered pixel conditions."""
from itertools import permutations
from .packing import terminal_rows

class Solver:
 def __init__(self,n): self.n=n;self.d=[];self.cs=[]
 def var(self,k=None):
  v=len(self.d);self.d.append((1<<(k or self.n))-1);return v
 def add(self,typ,vs,extra=None): self.cs.append((typ,vs,extra))
 def table(self,vs,rows): self.add('table',vs,list(rows))
 def element(self,ix,vs,o): self.add('element',[ix,o]+vs)
 def perm(self,vs): self.add('perm',vs)

def model(names,prog,clues):
 n=len(names);s=Solver(n);s.anchor=[]
 P=[[s.var() for _ in names] for t in range(n+1)];B=[[s.var() for _ in names] for t in range(n+1)]
 for row in P+B:s.perm(row)
 for t,(a,b) in enumerate(prog,1):
  if a==b:
   for old,new in zip(P[t-1]+B[t-1],P[t]+B[t]):s.table([old,new],[(i,i) for i in range(n)])
   continue
  cases=[]
  for ca in range(n):
   for cb in range(n):
    if ca==cb:continue
    parent=list(range(3*n))
    def find(x):
     while parent[x]!=x:x=parent[x]
     return x
    def union(x,y):parent[find(x)]=find(y)
    for w in range(n):union(n+w,cb if w==ca else ca if w==cb else w)
    union(2*n+ca,a);union(2*n+cb,b)
    groups={}
    for j in range(3*n):groups.setdefault(find(j),[]).append(j)
    if any(len({j//n for j in gg})<len(gg) for gg in groups.values()):continue
    cases.append(list(groups.values()))
  s.add('badge',B[t-1]+B[t]+P[t],cases)
  x,y=s.var(),s.var()
  s.element(B[t-1][a],[P[k][a] for k in range(1,n+1)],x)
  s.element(B[t-1][b],[P[k][b] for k in range(1,n+1)],y)
  s.add('cards',P[t-1]+P[t]+[x,y])
 groups={}
 for c in clues:groups.setdefault(c[2],[]).append(c)
 for tw,cc in groups.items():
  ws=sorted(set(w for c in cc for w in c[:2]));ds=sorted(set(c[3] for c in cc));rows=set()
  for perm in permutations(range(n)):
   distances={};ok=True
   for a,b,_,dw,sg in cc:
    val=sg*(perm[a]-perm[b])-1
    if not 0<=val<n or (dw in distances and distances[dw]!=val):ok=False;break
    distances[dw]=val
   if ok and len(set(distances.values()))==len(distances):rows.add(tuple(perm[w] for w in ws)+tuple(distances[w] for w in ds))
  selected=[]
  for w in ws:
   v=s.var();s.element(B[-1][tw],[P[k][w] for k in range(1,n+1)],v);selected.append(v)
  s.table(selected+[B[-1][w] for w in ds],sorted(rows))
  if len(cc)>2:s.anchor=selected+[B[-1][tw]]+[B[-1][w] for w in ds]

 rows=terminal_rows(n,clues);s.table(B[-1],rows)
 s.core=[v for row in P+B for v in row];s.final=B[-1]
 return s,P,B
