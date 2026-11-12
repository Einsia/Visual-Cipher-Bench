"""Equivalent Boolean encoding of the pixel-derived finite-domain model."""
class CNF:
 def __init__(self):self.n=0;self.cs=[]
 def var(self):v=self.n*2;self.n+=1;return v
 def clause(self,*ls):self.cs.append(ls)
 def one(self,ls):
  self.clause(*ls)
  for j,x in enumerate(ls):
   for y in ls[:j]:self.clause(x^1,y^1)
 def eq(self,a,b,cond):
  for x,y in zip(a,b):self.clause(cond^1,x^1,y);self.clause(cond^1,y^1,x)
 def table(self,vs,rows):
  selectors=[self.var() for row in rows];self.clause(*selectors)
  for c,row in zip(selectors,rows):
   for v,k in zip(vs,row):self.clause(c^1,v[k])
  for j,v in enumerate(vs):
   for k,x in enumerate(v):self.clause(x^1,*[c for c,row in zip(selectors,rows) if row[j]==k])
 def text(self,sec):return f'{self.n} {len(self.cs)} {sec}\n'+'\n'.join(str(len(c))+' '+' '.join(map(str,c)) for c in self.cs)+'\n'
def build(s):
 n=s.n;c=CNF();xs=[[c.var() for k in range(n)] for v in s.d]
 for row in xs:c.one(row)
 for typ,vs,ex in s.cs:
  v=[xs[i] for i in vs]
  if typ=='perm':
   for k in range(n):c.one([row[k] for row in v])
  elif typ=='table':c.table(v,ex)
  elif typ=='element':
   ix,o,*arr=v
   for k in range(n):c.eq(o,arr[k],ix[k])
  elif typ=='badge':
   selectors=[c.var() for gs in ex];c.clause(*selectors)
   for sel,gs in zip(selectors,ex):
    for g in gs:
     for j in g[1:]:c.eq(v[g[0]],v[j],sel)
  elif typ=='cards':
   selectors=[]
   for x in range(n):
    for y in range(x,n):
     if x==y and x!=0:continue
     sel=c.var();selectors.append(sel)
     if x==y:c.eq(v[-2],v[-1],sel)
     else:
      c.clause(sel^1,v[-2][x],v[-2][y]);c.clause(sel^1,v[-1][x],v[-1][y])
      c.clause(sel^1,v[-2][x]^1,v[-1][x]^1);c.clause(sel^1,v[-2][y]^1,v[-1][y]^1)
     perm=list(range(n));perm[x],perm[y]=perm[y],perm[x]
     for j in range(n):c.eq(v[j],[v[n+j][perm[k]] for k in range(n)],sel)
   c.clause(*selectors)
 return c,xs
