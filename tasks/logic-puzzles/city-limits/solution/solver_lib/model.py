"""Indexed receiving-area region loops; all conditions from the public page."""
import time
from functools import lru_cache

def geometry(data):
 w=data['width'];n=w*data.get('height',w)
 return w,n,[[u for u in range(n) if abs(u//w-v//w)+abs(u%w-v%w)==1] for v in range(n)]
def options(data,method='growth'):
 w,n,adj=geometry(data);roots=set(data['seeds']);labels=set(data['ids']);cap=min(max(labels),n-len(roots)+1);forbid=[0]*n;result=[]
 for a,b in data['walls']:forbid[a]|=1<<b;forbid[b]|=1<<a
 for seed in data['seeds']:
  seen={1<<seed};todo=[1<<seed];out=[]
  while todo:
   m=todo.pop();size=m.bit_count()
   if size in labels:out.append((m,size))
   if size>=cap:continue
   front=set();bits=m
   while bits:
    bit=bits&-bits;bits-=bit;front.update(adj[bit.bit_length()-1])
   for u in front:
    if u in roots or m>>u&1 or m&forbid[u]:continue
    mm=m|1<<u
    if mm not in seen:seen.add(mm);todo.append(mm)
  result.append(sorted(out))
 return result

def landing(data,i,a,lookup_area):
 w=data['width'];n=w*data.get('height',w);s=data['seeds'][i];di=data['directions'][i];dist=abs(a-lookup_area);v=s+di*dist
 return v if dist and 0<=v<n and (abs(di)!=1 or s//w==v//w) else -1

def required_lookup(data):
 ids={v:i for i,v in enumerate(data['ids'])};labels=tuple(ids)
 @lru_cache(None)
 def req(i,a,j,mask,b):
  ref=ids.get(b,-1)
  if ref<0:return -1,0
  values=[a] if ref==i else [b] if ref==j else labels
  bits=0
  for c in values:
   t=landing(data,i,a,c)
   if t>=0 and mask>>t&1:bits|=1<<c
  return ref,bits
 return req

def cycle_orders(data,chosen):
 k=len(chosen);ids={v:i for i,v in enumerate(data['ids'])};graph=[]
 for i,a in enumerate(chosen):
  row=[]
  for j,b in enumerate(chosen):
   if i==j or b[1] not in ids:continue
   t=landing(data,i,a[1],chosen[ids[b[1]]][1])
   if t>=0 and b[0]>>t&1:row.append(j)
  graph.append(row)
 path=[0]
 def walk(v,used):
  if len(path)==k:
   if 0 in graph[v]:yield path[:]
   return
  for j in graph[v]:
   if not used>>j&1:
    path.append(j);yield from walk(j,used|1<<j);path.pop()
 yield from walk(0,1)

def solve_cover(data,opts=None,cycle=True,limit=None,keep=True,propagate=True):
 start=time.perf_counter();w,n,adj=geometry(data);k=len(data['seeds']);full=(1<<n)-1
 if opts is None:opts=options(data)
 generation=time.perf_counter()-start;chosen=[None]*k;models=[];count=0;req=required_lookup(data)
 stats={'nodes':0,'complete_partitions':0,'optimistic_graph_prunes':0,'candidate_regions':sum(map(len,opts)),'option_counts':list(map(len,opts)),'generation_seconds':generation}
 def compatible(i,a,j,b,domains):
  ref,bits=req(i,a[1],j,b[0],b[1]);return ref>=0 and bool(bits&domains[ref])
 def possible(valid,domains):
  graph=[0]*k
  for i in range(k):
   for j in range(k):
    if i==j:continue
    if chosen[i] and chosen[j]:ok=compatible(i,chosen[i],j,chosen[j],domains)
    elif chosen[i]:ok=any(compatible(i,chosen[i],j,b,domains) for b in valid[j])
    elif chosen[j]:ok=any(compatible(i,a,j,chosen[j],domains) for a in valid[i])
    else:ok=True
    if ok:graph[i]|=1<<j
  if any(not row for row in graph):return False
  incoming=0
  for row in graph:incoming|=row
  if incoming!=(1<<k)-1:return False
  for rev in (False,True):
   seen=1;old=0
   while seen!=old:
    old=seen
    for i in range(k):
     if seen>>i&1:
      if not rev:seen|=graph[i]
      else:
       for j in range(k):
        if graph[j]>>i&1:seen|=1<<j
   if seen!=(1<<k)-1:return False
  return True
 def rec(used,depth):
  nonlocal count
  stats['nodes']+=1
  if depth==k:
   if used!=full:return False
   stats['complete_partitions']+=1
   for order in cycle_orders(data,chosen) if cycle else [None]:
    count+=1
    if keep:models.append({'regions':list(chosen),'order':order})
    if limit and count>=limit:return True
   return False
  valid=[[] for _ in range(k)];domains=[0]*k;best=None;minlen=10**9;cover=used;lo=hi=0
  for i,row in enumerate(opts):
   if chosen[i] is not None:domains[i]=1<<chosen[i][1];continue
   v=[o for o in row if not o[0]&used];valid[i]=v
   if not v:return False
   lo+=min(o[1] for o in v);hi+=max(o[1] for o in v)
   for m,a in v:cover|=m;domains[i]|=1<<a
   if len(v)<minlen:best=[(i,o) for o in v];minlen=len(v)
  if cover!=full or not lo<=n-used.bit_count()<=hi:return False
  if cycle and propagate and not possible(valid,domains):stats['optimistic_graph_prunes']+=1;return False
  missing=full^used
  while missing:
   bit=missing&-missing;missing-=bit;cc=[(i,o) for i,row in enumerate(valid) for o in row if o[0]&bit]
   if len(cc)<minlen:best=cc;minlen=len(cc)
  for i,o in best:
   chosen[i]=o
   if rec(used|o[0],depth+1):chosen[i]=None;return True
   chosen[i]=None
  return False
 truncated=rec(0,0);stats.update(solution_count=count,exhaustive=not truncated,seconds=time.perf_counter()-start,route='indexed-area graph with MRV cover',lookup_cache_entries=req.cache_info().currsize)
 return models,stats

def solve_cycle(data,opts=None,limit=None):
 start=time.perf_counter();w,n,adj=geometry(data);k=len(data['seeds']);full=(1<<n)-1
 if opts is None:opts=options(data)
 req=required_lookup(data);domains0=[sum(1<<a for a in set(x[1] for x in row)) for row in opts];start_i=min(range(k),key=lambda i:len(opts[i]));chosen=[None]*k;models=[];path=[start_i];nodes=0;dead=0;complete=0
 @lru_cache(None)
 def successors(i,a):
  out=[]
  for j,row in enumerate(opts):
   if i==j:continue
   for m,b in row:
    ref,bits=req(i,a,j,m,b)
    if bits:out.append((j,m,b,ref,bits))
  return out
 def rec(i,used,covered,domains):
  nonlocal nodes,dead,complete
  nodes+=1
  if used==(1<<k)-1:
   if covered!=full:return False
   complete+=1;j=start_i;m,b=chosen[j];ref,bits=req(i,chosen[i][1],j,m,b)
   if bits&domains[ref]:
    models.append({'regions':list(chosen),'order':list(path)})
    if limit and len(models)>=limit:return True
   return False
  for j,m,b,ref,bits in successors(i,chosen[i][1]):
   if used>>j&1 or covered&m or not (domains[j]>>b&1):continue
   nd=domains[:];nd[j]=1<<b;nd[ref]&=bits
   if not nd[ref]:continue
   nc=covered|m;nu=used|1<<j;cover=nc;lo=hi=0;okay=True
   for r,row in enumerate(opts):
    if nu>>r&1:continue
    av=0;mn=n;mx=0
    for rm,ra in row:
     if rm&nc or not (nd[r]>>ra&1):continue
     cover|=rm;av|=1<<ra;mn=min(mn,ra);mx=max(mx,ra)
    if not av:okay=False;break
    nd[r]&=av;lo+=mn;hi+=mx
   if not okay or cover!=full or not lo<=n-nc.bit_count()<=hi:dead+=1;continue
   chosen[j]=(m,b);path.append(j)
   if rec(j,nu,nc,nd):return True
   path.pop();chosen[j]=None
  return False
 stopped=False
 for m,a in opts[start_i]:
  chosen[start_i]=(m,a);ds=domains0[:];ds[start_i]=1<<a
  if rec(start_i,1<<start_i,m,ds):stopped=True;break
 stats=dict(route='cycle-first with pending third-region area domains',nodes=nodes,domain_cover_prunes=dead,complete_cycles_before_closure=complete,candidate_regions=sum(map(len,opts)),option_counts=list(map(len,opts)),solution_count=len(models),exhaustive=not stopped,seconds=time.perf_counter()-start,start_identity=data['ids'][start_i])
 return models,stats

def place_letters(data, regions):
 """Allocate the observed unsegmented bank using only the solved partition."""
 if 'letter_bank' not in data:
  return list(data['letters'])
 n=data['width']*data.get('height',data['width'])
 cells=[v for i in sorted(range(len(regions)),key=lambda i:data['ids'][i]) for v in sorted(regions[i])]
 if len(data['letter_bank'])!=n or sorted(cells)!=list(range(n)):
  raise ValueError('Letter allocation requires one complete partition and one letter per cell')
 letters=['']*n
 for v,ch in zip(cells,data['letter_bank']):letters[v]=ch
 return letters

def describe(data,model):
 w,n,adj=geometry(data);rs=model['regions'];order=model['order'];k=len(order);idx=order.index(data['start']);order=order[idx:]+order[:idx];ids={v:i for i,v in enumerate(data['ids'])};dest=[None]*k
 for i,j in zip(order,order[1:]+order[:1]):dest[i]=j
 areas=[o[1] for o in rs];look=[ids[areas[dest[i]]] for i in range(k)];lands=[landing(data,i,areas[i],areas[look[i]]) for i in range(k)]
 regions=[[v for v in range(n) if m>>v&1] for m,a in rs]
 letters=place_letters(data,regions)
 return {'regions':regions,'resolved_letters':letters,'areas':areas,'landing_cells':lands,'next_indices':dest,'lookup_indices':look,'lookup_ids':[data['ids'][v] for v in look],'lookup_areas':[areas[v] for v in look],'cycle_indices':order,'cycle_ids':[data['ids'][i] for i in order],'ordered_landing_cells':[lands[i] for i in order],'jumps':[abs(areas[i]-areas[look[i]]) for i in range(k)],'answer':''.join(letters[lands[i]] for i in order)}

def solve_cover_bits(data,opts=None,limit=None):
 """Exact cover with bitset candidate domains; same conservative graph proof."""
 start=time.perf_counter();w,n,adj=geometry(data);k=len(data['ids']);ids={v:i for i,v in enumerate(data['ids'])}
 if opts is None:opts=options(data)
 root_bits=[0]*k;cell_bits=[0]*n;size_bits={a:0 for a in ids};flat=[];labels=list(ids)
 for i,row in enumerate(opts):
  for m,a in row:
   idx=len(flat);bit=1<<idx;flat.append((i,m,a));root_bits[i]|=bit;size_bits[a]|=bit
   x=m
   while x:
    b=x&-x;x-=b;cell_bits[b.bit_length()-1]|=bit
 kill=[]
 for i,m,a in flat:
  rm=0;x=m
  while x:
   b=x&-x;x-=b;rm|=cell_bits[b.bit_length()-1]
  kill.append(rm)
 # For a chosen source area, candidate destinations grouped by lookup identity and lookup value.
 targets={}
 for i in range(k):
  for a in labels:
   row=[]
   for b in labels:
    ref=ids[b]
    for c in labels:
     if ref==i and c!=a:continue
     t=landing(data,i,a,c)
     if t<0:continue
     bits=cell_bits[t]&size_bits[b]&~root_bits[i]
     if c!=b:bits&=~root_bits[ref]
     if bits:row.append((ref,1<<c,bits))
   targets[i,a]=row
 req=required_lookup(data);chosen=[None]*k;models=[];count=0;full=(1<<n)-1;nodes=0;complete=0;pruned=0
 def possible(avail,domains,rootvalid):
  graph=[0]*k
  for i in range(k):
   if chosen[i]:
    destopts=0
    for ref,bit,optsbits in targets[i,chosen[i][1]]:
     if domains[ref]&bit:destopts|=optsbits
    destopts&=avail
    for j in range(k):
     if i==j:continue
     if chosen[j]:
      ref,bits=req(i,chosen[i][1],j,chosen[j][0],chosen[j][1]);ok=bits&domains[ref]
     else:ok=destopts&rootvalid[j]
     if ok:graph[i]|=1<<j
   else:
    for j in range(k):
     if i==j:continue
     if chosen[j]:
      aa=domains[i];ok=False
      while aa:
       bit=aa&-aa;aa-=bit;a=bit.bit_length()-1;ref,bits=req(i,a,j,chosen[j][0],chosen[j][1])
       if bits&domains[ref]:ok=True;break
     else:ok=True
     if ok:graph[i]|=1<<j
  inc=0
  for row in graph:
   if not row:return False
   inc|=row
  if inc!=(1<<k)-1:return False
  for rev in (False,True):
   seen=1;old=0
   while seen!=old:
    old=seen
    for i in range(k):
     if seen>>i&1:
      if not rev:seen|=graph[i]
      else:
       for j in range(k):
        if graph[j]>>i&1:seen|=1<<j
   if seen!=(1<<k)-1:return False
  return True
 def rec(used,avail,depth):
  nonlocal count,nodes,complete,pruned
  nodes+=1
  if depth==k:
   if used!=full:return False
   complete+=1
   for order in cycle_orders(data,chosen):
    count+=1;models.append(dict(regions=list(chosen),order=order))
    if limit and count>=limit:return True
   return False
  domains=[0]*k;rootvalid=[0]*k;best=0;minlen=10**9;lo=hi=0
  for i in range(k):
   if chosen[i]:domains[i]=1<<chosen[i][1];continue
   v=avail&root_bits[i];rootvalid[i]=v
   if not v:return False
   for a,abits in size_bits.items():
    if v&abits:domains[i]|=1<<a
   lo+=(domains[i]&-domains[i]).bit_length()-1;hi+=domains[i].bit_length()-1
   num=v.bit_count()
   if num<minlen:best=v;minlen=num
  missing=n-used.bit_count()
  if not lo<=missing<=hi:return False
  todo=full^used
  while todo:
   bit=todo&-todo;todo-=bit;v=avail&cell_bits[bit.bit_length()-1];num=v.bit_count()
   if not num:return False
   if num<minlen:best=v;minlen=num
  if not possible(avail,domains,rootvalid):pruned+=1;return False
  while best:
   bit=best&-best;best-=bit;idx=bit.bit_length()-1;i,m,a=flat[idx];chosen[i]=(m,a)
   if rec(used|m,avail&~kill[idx],depth+1):return True
   chosen[i]=None
  return False
 stopped=rec(0,(1<<len(flat))-1,0)
 return models,dict(route='bitset candidate cover plus indexed-area graph',nodes=nodes,complete_partitions=complete,optimistic_graph_prunes=pruned,candidate_regions=len(flat),option_counts=list(map(len,opts)),solution_count=count,exhaustive=not stopped,seconds=time.perf_counter()-start)
