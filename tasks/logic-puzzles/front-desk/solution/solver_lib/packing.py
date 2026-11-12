from itertools import permutations, product
import time

def feasible(n,edges):
 adj=[[] for _ in range(n)]
 for a,b,d in edges:adj[b].append((a,d));adj[a].append((b,-d))
 seen={};groups=[]
 for w in range(n):
  if w in seen:continue
  stack=[w];seen[w]=0;comp=[]
  while stack:
   u=stack.pop();comp.append(u)
   for v,d in adj[u]:
    vv=seen[u]+d
    if v in seen:
     if seen[v]!=vv:return False
    else:seen[v]=vv;stack.append(v)
  if len(comp)>1:
   pp=[seen[u] for u in comp]
   if len(set(pp))!=len(pp) or max(pp)-min(pp)>=n:return False
   low=min(pp);mask=sum(1<<(i-low) for i in pp);span=max(pp)-low
   groups.append([mask<<k for k in range(n-span)])
 groups.sort(key=len)
 def pack(i,used):
  if i==len(groups):return True
  return any(not used&m and pack(i+1,used|m) for m in groups[i])
 return pack(0,0)

def terminal_rows(n,clues):
 groups={}
 for a,b,tw,dw,sg in clues:groups.setdefault(tw,[]).append((a,b,dw,sg))
 relevant=sorted(set(c[3] for c in clues));cache={};out=[]
 for row in permutations(range(n)):
  key=tuple(row[i] for i in relevant)
  valid=cache.get(key)
  if valid is None:
   valid=all(any(feasible(n,[(a,b,sign*(row[dw]+1)) for (a,b,dw,sg),sign in zip(group,signs)]) for signs in product(*[(sg,) if sg else (-1,1) for a,b,dw,sg in group])) for group in groups.values());cache[key]=valid
  if valid:out.append(row)
 return out
