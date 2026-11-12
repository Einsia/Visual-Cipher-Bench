from overlap import area
def half(p,a,b,inside):
 out=[]
 if not p:return out
 def side(q):return ((b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]))*(1 if inside else -1)
 v=p[-1];sv=side(v)
 for w in p:
  sw=side(w)
  if (sw>=-1e-10)!=(sv>=-1e-10):
   t=sv/(sv-sw);out.append([v[0]+t*(w[0]-v[0]),v[1]+t*(w[1]-v[1])])
  if sw>=-1e-10:out.append(w)
  v=w;sv=sw
 return out

def subtract(p,q):
 if area(q)<1e-10:return [p]
 parts=[]
 for a,b in zip(q,q[1:]+q[:1]):
  if abs(a[0]-b[0])+abs(a[1]-b[1])<1e-10:continue
  out=half(p,a,b,False)
  if area(out)>1e-9:parts.append(out)
  p=half(p,a,b,True)
  if not p:break
 return parts

def union(polys):
 parts=[]
 for index,p in enumerate(polys):
  add=[p]
  for q in polys[:index]:add=[r for a in add for r in subtract(a,q)]
  parts+=add
 return parts

def difference(A,B):
 parts=union(A)
 for q in B:parts=[r for a in parts for r in subtract(a,q)]
 return parts

def delta(A,B):return difference(A,B)+difference(B,A)
