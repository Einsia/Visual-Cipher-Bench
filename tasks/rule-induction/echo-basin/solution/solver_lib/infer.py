import numpy as np
import time
from itertools import product
from .coupled import *

def undo_candidate(r,driver,order,kinds,signs,transport,domain):
 axes=(order,1-order);c=driver.copy();history=[]
 def shift(a,ax,n,sg):
  if domain==5:return shifts(a,ax,n,sg)
  out=a.copy()
  for i in range(7):
   if ax==0:out[i,:]=np.roll(a[i,:],int(n[i])*sg)
   else:out[:,i]=np.roll(a[:,i],int(n[i])*sg)
  return out
 for ax,kind,sg in zip(axes,kinds,signs):
  n=tally(c,kind,ax);history.append((ax,n,sg))
  if transport:c=shift(c,ax,n,sg)
 out=r.copy()
 for ax,n,sg in history[::-1]:out=shift(out,ax,n,-sg)
 return out

def infer(worked):
 start=time.perf_counter();obs=[];incoming=[]
 for st in worked:
  p,s,q,r=map(dec,[st[x] for x in ['plate_before','stamp_before','plate_after','stamp_after']])
  ks=[k for k in range(4) if np.array_equal((p+rot(s,k))%3,q)]
  incoming.append(ks)
  if len(ks)!=1:raise ValueError('incoming orientation not unique')
  obs.append((p,s,rot(s,ks[0]),q,r))
 drivers=[]
 for source,kind,sg in product(['P','S'],['ring','square','occupied'],[1,-1]):
  kk=[]
  for p,s,t,q,r in obs:
   a=p if source=='P' else s;kk.append(int(tally(a,kind,0).sum())*sg%4)
  if kk==[x[0] for x in incoming]:drivers.append([source,kind,sg])
 models=[];tested=0;celltests=0
 for source,order,kinds,signs,transport,domain in product(['P','T','Q'],range(2),product(['ring','square','occupied'],repeat=2),product([1,-1],repeat=2),[False,True],[5,7]):
  tested+=1;table={};ok=True
  for p,s,t,q,r in obs:
   d=undo_candidate(r,{'P':p,'T':t,'Q':q}[source],order,kinds,signs,transport,domain)
   for a,b,v in zip(p.flat,t.flat,d.flat):
    celltests+=1;key=(int(a),int(b));v=int(v)
    if key in table and table[key]!=v:ok=False;break
    table[key]=v
   if not ok:break
  if ok:models.append({'source':source,'order':order,'kinds':list(kinds),'signs':list(signs),'transport':transport,'domain':domain,'table':[[table.get((a,b)) for b in range(3)] for a in range(3)]})
 return {'incoming_orientations':incoming,'incoming_drivers':drivers,'models':models,'candidates':tested,'cell_comparisons':celltests,'seconds':time.perf_counter()-start}
