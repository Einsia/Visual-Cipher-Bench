"""Exact acyclic finite languages and lexical transductions, standard library only."""
from functools import lru_cache
import time,json,sys
class Lang:
 def __init__(self):
  self.nodes=[(False,()),(True,())];self.index={v:i for i,v in enumerate(self.nodes)}
 def node(self,final,edges):
  key=(bool(final),tuple(sorted((c,n) for c,n in edges if n)))
  if key not in self.index:self.index[key]=len(self.nodes);self.nodes.append(key)
  return self.index[key]
 @lru_cache(None)
 def union(self,a,b):
  if not a:return b
  if not b or a==b:return a
  da=dict(self.nodes[a][1]);db=dict(self.nodes[b][1]);es=[]
  for c in da.keys()|db.keys():es.append((c,self.union(da.get(c,0),db.get(c,0))))
  return self.node(self.nodes[a][0] or self.nodes[b][0],es)
 def prefix(self,s,n):
  if not n:return 0
  for c in reversed(s):n=self.node(False,[(c,n)])
  return n
 def literal(self,s):return self.prefix(s,1)
 def many(self,ss):
  trie={}
  for s in ss:
   t=trie
   for c in s:t=t.setdefault(c,{})
   t['']=True
  def rec(t):return self.node('' in t,[(c,rec(u)) for c,u in t.items() if c])
  return rec(trie)
 def compact(self,r):
  n=Lang()
  @lru_cache(None)
  def cp(k):return n.node(self.nodes[k][0],[(c,cp(j)) for c,j in self.nodes[k][1]])
  rr=cp(r);self.union.cache_clear();return n,rr
 def count(self,r):
  @lru_cache(None)
  def f(k):return int(self.nodes[k][0])+sum(f(j) for c,j in self.nodes[k][1])
  return f(r)
 def words(self,r):
  if self.nodes[r][0]:yield ''
  for c,j in self.nodes[r][1]:
   for w in self.words(j):yield c+w
 def intersect(self,r,t,other):
  @lru_cache(None)
  def f(a,b):
   es=[];db=dict(other.nodes[b][1])
   for c,j in self.nodes[a][1]:
    if c in db:es.append((c,f(j,db[c])))
   return self.node(self.nodes[a][0] and other.nodes[b][0],es)
  return f(r,t)
 def rewrite(self,r,a,b):
  L=max(len(a),len(b));names=[a,b]
  @lru_cache(None)
  def rec(k,tail,pending,dist):
   final,es=self.nodes[k];out=self.literal(pending) if final else 0
   for c,j in es:
    raw=tail+c;buf=pending+c;d=min(L,dist+1)
    hits=[w for w in names if raw.endswith(w)]
    if len(hits)>1:continue
    if hits:
     w=hits[0]
     if d<len(w):continue
     emit=buf[:-len(w)]+(b if w==a else a);buf='';d=0
    elif len(buf)>=L:emit,buf=buf[0],buf[1:]
    else:emit=''
    q=rec(j,raw[-(L-1):] if L>1 else '',buf,d)
    out=self.union(out,self.prefix(emit,q))
   return out
  q=rec(r,'','',L);rec.cache_clear();return q
 def loose_preimage(self,r,a,b):
  # Tokenized inverse is a superset; a forward rewrite plus target intersection
  # below removes spurious copies and overlaps. No valid preimage is discarded.
  @lru_cache(None)
  def f(k):
   final,edges=self.nodes[k];out=1 if final else 0
   for c,j in edges:out=self.union(out,self.prefix(c,f(j)))
   for src,dst in ((a,b),(b,a)):
    j=k
    for c in src:
     j=dict(self.nodes[j][1]).get(c,0)
     if not j:break
    if j:out=self.union(out,self.prefix(dst,f(j)))
   return out
  return f(r)
 def transduce(self,r,trie):
  # Each complete lexical entry produces its output; concatenation permits all segmentations.
  @lru_cache(None)
  def T(k):return scan(k,0)
  @lru_cache(None)
  def scan(k,v):
   end,edges=self.nodes[k];children,outs=trie[v]
   result=1 if end and v==0 else 0
   if outs:
    tail=T(k)
    for s in outs:result=self.union(result,self.prefix(s,tail))
   for c,j in edges:
    if c in children:result=self.union(result,scan(j,children[c]))
   return result
  q=T(r);T.cache_clear();scan.cache_clear();return q

def make_trie(pairs):
 nodes=[({},set())]
 for a,b in pairs:
  v=0
  for c in a:
   if c not in nodes[v][0]:nodes[v][0][c]=len(nodes);nodes.append(({},set()))
   v=nodes[v][0][c]
  nodes[v][1].add(b)
 return nodes

