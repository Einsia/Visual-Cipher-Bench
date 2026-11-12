import numpy as np
from itertools import product

def rot(a,k):return np.rot90(a,-int(k)%4,axes=(-2,-1))
def enc(a):return ''.join(map(str,np.asarray(a).ravel().tolist()))
def dec(s):return np.array(list(s),dtype=np.int8).reshape(7,7)
def glyph(font,L):
 a=np.zeros((7,7),dtype=np.int8);a[1:6,1:6]=np.array([list(x) for x in font[L]],dtype=np.int8);return a

def shifts(a,axis,amounts,sign=1):
 b=a.copy()
 for i in range(1,6):
  n=amounts[i]
  if axis==0:b[i,1:6]=np.roll(a[i,1:6],int(n)*sign)
  else:b[1:6,i]=np.roll(a[1:6,i],int(n)*sign)
 return b

def tally(a,kind,axis):
 mask=(a==2) if kind=='ring' else (a==1) if kind=='square' else (a!=0)
 return mask.sum(axis=1 if axis==0 else 0)

def shuffle(d,q,order=0,kinds=('ring','square'),signs=(1,1),transport=True):
 axes=(order,1-order);c=q.copy();out=d.copy()
 for axis,kind,sign in zip(axes,kinds,signs):
  n=tally(c,kind,axis);out=shifts(out,axis,n,sign)
  if transport:c=shifts(c,axis,n,sign)
 return out

def unshuffle(r,q):
 nr=tally(q,'ring',0);u=shifts(q,0,nr)
 nc=tally(u,'square',1)
 return shifts(shifts(r,1,nc,-1),0,nr,-1)

def forward(p,s):
 k=int((p==2).sum()%4);t=rot(s,k);q=(p+t)%3
 d=(t-p+(q!=0))%3;r=shuffle(d,q)
 return q,r,k

def backward(q,r):
 d=(unshuffle(r,q)-(q!=0))%3
 p=(2*(q-d))%3;t=(2*(q+d))%3
 k=int((p==2).sum()%4);s=rot(t,-k)
 return p,s,k

def run(p,a,b):
 p=p.copy();rack={'A':a.copy(),'B':b.copy()};steps=[]
 for label in ['A','B','A']:
  s=rack[label].copy();q,r,k=forward(p,s)
  steps.append({'label':label,'plate_before':enc(p),'stamp_before':enc(s),'plate_after':enc(q),'stamp_after':enc(r)})
  p=q;rack[label]=r
 return p,rack,steps
