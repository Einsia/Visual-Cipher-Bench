"""Pixel-only reconstruction of extruded grid solids, seams and lettering.

All mesh vertices, face memberships, cuts and letter positions are measured
at runtime. No authored scene, solution, or cached measurements are loaded.
"""
import itertools
import math
import string
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = Path(__file__).parent

def log(message):
    print(message, file=sys.stderr, flush=True)

def components(mask):
 h,w=mask.shape; seen=mask.copy(); out=[]
 for y,x in zip(*np.nonzero(mask)):
  if not seen[y,x]:continue
  stack=[(int(x),int(y))];seen[y,x]=False;pts=[]
  while stack:
   xx,yy=stack.pop();pts.append((xx,yy))
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    nx,ny=xx+dx,yy+dy
    if 0<=nx<w and 0<=ny<h and seen[ny,nx]:seen[ny,nx]=False;stack.append((nx,ny))
  if len(pts)>20:out.append(np.array(pts))
 return out

def lines(a):
 ys,xs=np.where(a<210);p=np.stack([xs,ys],1).astype(float)
 ts=np.arange(0,np.pi,np.pi/720);ns=np.stack([np.cos(ts),np.sin(ts)],1)
 rmax=int(np.hypot(*a.shape))+5
 hist=np.array([np.bincount(np.rint(p@n).astype(int)+rmax,minlength=2*rmax+1) for n in ns])
 found=[]
 for it in range(30):
  ti,ri=np.unravel_index(hist.argmax(),hist.shape);n=ns[ti];rho=ri-rmax
  if hist[ti,ri]<25:break
  near=p[np.abs(p@n-rho)<2.3];t=np.array([-n[1],n[0]]);v=near@t
  order=np.argsort(v);v=v[order];near=near[order]
  breaks=np.where(np.diff(v)>12)[0]+1
  groups=np.split(near,breaks)
  for g in groups:
   if len(g)<35 or np.ptp(g@t)<45:continue
   cen=g.mean(0);_,_,vh=np.linalg.svd(g-cen,full_matrices=False);tt=vh[0];nn=np.array([-tt[1],tt[0]]);rr=cen@nn
   if any(abs(nn@l[0])>.999 and abs(rr-(1 if nn@l[0]>0 else -1)*l[1])<4 for l in found):continue
   vv=g@tt;ends=cen+np.outer(np.array([vv.min(),vv.max()])-cen@tt,tt)
   found.append((nn,rr,ends,len(g)))
  p=p[np.abs(p@n-rho)>3.5]
  hist=np.array([np.bincount(np.rint(p@n).astype(int)+rmax,minlength=2*rmax+1) for n in ns])
 return found

def vertices(ls):
 ps=[]
 for i,j in itertools.combinations(range(len(ls)),2):
  n,r,e,c=ls[i];m,s,f,d=ls[j]
  if abs(np.linalg.det([n,m]))<.15:continue
  p=np.linalg.solve([n,m],[r,s])
  if any(min(np.linalg.norm(p-v,axis=1))<30 for v in [e,f]) and all(np.linalg.norm(p-v[0])+np.linalg.norm(p-v[1])<np.linalg.norm(v[0]-v[1])+60 for v in [e,f]):ps.append(p)
 clusters=[]
 for p in ps:
  for cl in clusters:
   if np.linalg.norm(p-np.mean(cl,0))<5:cl.append(p);break
  else:clusters.append([p])
 return np.array([np.mean(cl,0) for cl in clusters])

FONT=ImageFont.truetype(str(ASSETS / 'DejaVuSans.ttf'),100)
def cropmask(a):
 y,x=np.where(a);return a[y.min():y.max()+1,x.min():x.max()+1]

def sample(a,p,q):
 pp=p+np.linspace(.06,.94,60)[:,None]*(q-p);x,y=np.rint(pp).astype(int).T
 if min(x)<3 or min(y)<3 or max(x)>=a.shape[1]-3 or max(y)>=a.shape[0]-3:return 0
 vals=[a[y+dy,x+dx]for dx,dy in itertools.product(range(-2,3),repeat=2)]
 return np.mean(np.min(vals,axis=0)<220)

def match(a):
 ls=lines(a);ps=vertices(ls)
 candidates=[];seen=set()
 for oi,ai,bi in itertools.permutations(range(len(ps)),3):
  o=ps[oi];av=ps[ai]-o;bv=ps[bi]-o
  if min(np.linalg.norm(av),np.linalg.norm(bv))<50:continue
  if abs(np.linalg.det([av,bv]))<2500:continue
  if min(np.linalg.norm(ps-(o+av+bv),axis=1))>8:continue
  # Each detected end square can occupy any cell of either end.
  for q in quads:
   base=V[q[0]];z=base[2];deltas=V-V[q[0]]
   dd=((ps[:,None,:]-o-deltas[:nend,:2]@np.array([av,bv]))/(1 if z==0 else -1)).reshape(-1,2)
   sx,sy=signs
   cc=(dd-sx*shear[0]*av/unit-sy*shear[1]*bv/unit)/depth
   gg=np.outer(av/unit,av/unit)+np.outer(bv/unit,bv/unit)+cc[:,:,None]*cc[:,None,:]
   tr=gg[:,0,0]+gg[:,1,1]
   errors=np.linalg.norm(gg-np.eye(2)[None]*tr[:,None,None]/2,axis=(1,2))/tr
   for ii in np.where(errors<.065)[0]:
      d=dd[ii];error=errors[ii]
      M=np.array([av,bv,d]);shift=o-base@M
      pp=V@M+shift
      dist=np.min(np.linalg.norm(pp[:,None]-ps,axis=2),axis=1)
      count=(dist<6).sum()
      if count<6:continue
      key=tuple(np.rint(np.r_[M.flatten(),shift]/3).astype(int))+(sx,sy)
      if key in seen:continue
      seen.add(key)
      es=np.array([sample(a,pp[u],pp[v]) for u,v in edges]);sc={e:s for e,s in zip(edges,es)}
      fs=[min(sc[tuple(sorted((u,v)))]for u,v in zip(f,f[1:]+f[:1]))for f in faces]
      fids=[i for i,s in enumerate(fs)if s>.78]
      if len(fids)<3:continue
      validvs=set(v for i in fids for v in faces[i])
      explained=sum(np.min(np.linalg.norm(ps[:,None]-pp[list(validvs)],axis=2),axis=1)<6)
      rank=explained+len(fids)*2-error*4
      candidates.append((rank,fids,M,shift,(sx,sy),error,explained))
 candidates.sort(key=lambda c:-c[0]);return candidates,ps
def targetfit(a, known_diagonals=False):
 ls=lines(a);ps=vertices(ls);N=len(ps);best=None

 origins=[]
 for oi in range(N):
  for ai in range(N):
   for bi in range(N):
    av=ps[ai]-ps[oi];bv=ps[bi]-ps[oi]
    if min(np.linalg.norm(av),np.linalg.norm(bv))<45 or abs(np.linalg.det([av,bv]))<2500:continue
    err=min(np.linalg.norm(ps-(ps[oi]+av+bv),axis=1))
    if err<5:origins.append((err,oi,ai,bi))
 origins.sort()
 tried=set()
 for _,oi,ai,bi in origins:
  o=ps[oi];av=ps[ai]-o;bv=ps[bi]-o
  for base in V[origins3d]:
   z=base[2];deltas=V[:nend,:2]-base[:2]
   dd=((ps[:,None,:]-o-deltas@np.array([av,bv]))/(1 if z==0 else -1)).reshape(-1,2)
   cc=(dd-signs[0]*shear[0]*av/unit-signs[1]*shear[1]*bv/unit)/depth
   gg=np.outer(av/unit,av/unit)+np.outer(bv/unit,bv/unit)+cc[:,:,None]*cc[:,None,:]
   tr=gg[:,0,0]+gg[:,1,1]
   er=np.linalg.norm(gg-np.eye(2)[None]*tr[:,None,None]/2,axis=(1,2))/tr
   dd=dd[er<.07]
   if len(dd)==0:continue
   PP=(V[:,:2]-base[:2])@np.array([av,bv])+o
   pp=PP[None]+(V[:,2]-z)[None,:,None]*dd[:,None,:]
   dst=np.min(np.linalg.norm(pp[:,:,None]-ps[None,None],axis=3),axis=2)
   counts=(dst<6).sum(axis=1)
   for idx in np.where(counts>=len(V)-4)[0]:
    M=np.array([av,bv,dd[idx]]);shift=o-base@M
    C=np.array([av/unit,bv/unit,(dd[idx]-signs[0]*shear[0]*av/unit-signs[1]*shear[1]*bv/unit)/depth]);G=C.T@C
    error=np.linalg.norm(G-np.eye(2)*np.trace(G)/2)/np.trace(G)
    if error>.07:continue
    key=tuple(np.rint(np.r_[M.ravel(),shift]/4).astype(int))
    if key in tried:continue
    tried.add(key)
    # Refine by least squares on the vertex matches, excluding outliers.
    for it in range(3):
     pred=V@M+shift;dist=np.linalg.norm(pred[:,None]-ps,axis=2);js=dist.argmin(1);valid=dist.min(1)<8
     X=np.c_[V,np.ones(len(V))];fit=np.linalg.lstsq(X[valid],ps[js[valid]],rcond=None)[0];M=fit[:3];shift=fit[3]
    C=np.array([M[0]/unit,M[1]/unit,(M[2]-signs[0]*shear[0]*M[0]/unit-signs[1]*shear[1]*M[1]/unit)/depth]);G=C.T@C
    error=np.linalg.norm(G-np.eye(2)*np.trace(G)/2)/np.trace(G)
    if error>.07:continue
    pred=V@M+shift
    if known_diagonals:
     scores=[sample(a,pred[u],pred[v])for u,v in edges]
    else:
     scores=[sample(a,pred[u],pred[v])for u,v in surface_edges]
     # Coplanar face boundaries are intentionally absent from the target.
    rank=sum(scores)
    if best is None or rank>best[0]:
     best=(rank,M,shift)
    if rank>len(surface_edges)-.4 and not known_diagonals:return best,ps

 return best,ps
def affine_targetfit(a):
 ls=lines(a);ps=vertices(ls);N=len(ps);best=None

 origins=[]
 for oi in range(N):
  for ai in range(N):
   for bi in range(N):
    av=ps[ai]-ps[oi];bv=ps[bi]-ps[oi]
    if min(np.linalg.norm(av),np.linalg.norm(bv))<45 or abs(np.linalg.det([av,bv]))<2500:continue
    err=min(np.linalg.norm(ps-(ps[oi]+av+bv),axis=1))
    if err<5:origins.append((err,oi,ai,bi))
 origins.sort()
 tried=set()
 for _,oi,ai,bi in origins:
  o=ps[oi];av=ps[ai]-o;bv=ps[bi]-o
  for base in V[origins3d]:
   z=base[2];deltas=V[:nend,:2]-base[:2]
   dd=((ps[:,None,:]-o-deltas@np.array([av,bv]))/(1 if z==0 else -1)).reshape(-1,2)
   if len(dd)==0:continue
   PP=(V[:,:2]-base[:2])@np.array([av,bv])+o
   pp=PP[None]+(V[:,2]-z)[None,:,None]*dd[:,None,:]
   dst=np.min(np.linalg.norm(pp[:,:,None]-ps[None,None],axis=3),axis=2)
   counts=(dst<6).sum(axis=1)
   for idx in np.where(counts>=len(V)-4)[0]:
    projected=pp[idx]
    pair=np.linalg.norm(projected[:,None]-projected[None],axis=2)+np.eye(len(V))*1e6
    if pair.min()<15:continue
    M=np.array([av,bv,dd[idx]]);shift=o-base@M
    key=tuple(np.rint(np.r_[M.ravel(),shift]/4).astype(int))
    if key in tried:continue
    tried.add(key)
    # Refine by least squares on the vertex matches, excluding outliers.
    for it in range(3):
     pred=V@M+shift;dist=np.linalg.norm(pred[:,None]-ps,axis=2);js=dist.argmin(1);valid=dist.min(1)<8
     X=np.c_[V,np.ones(len(V))];fit=np.linalg.lstsq(X[valid],ps[js[valid]],rcond=None)[0];M=fit[:3];shift=fit[3]
    pred=V@M+shift
    pair=np.linalg.norm(pred[:,None]-pred[None],axis=2)+np.eye(len(V))*1e6
    if pair.min()<15:continue
    scores=[sample(a,pred[u],pred[v])for u,v in surface_edges]
    rank=sum(scores)
    if best is None or rank>best[0]:
     best=(rank,M,shift)
    if rank>len(surface_edges)-.4:return best,ps

 return best,ps
def cuts(a,M,t):
 pp=V@M+t;cs=components(a>150);holes=[]
 for c in cs:
  lo=c.min(0);hi=c.max(0);dim=hi-lo
  if 20<len(c)<160 and min(dim)>3 and max(dim)<17:holes.append(c.mean(0))
 ans=set()
 for h,g in itertools.combinations(holes,2):
  dist=np.linalg.norm(h-g)
  if dist<8 or dist>16:continue
  mid=(h+g)/2
  for ei,(u,v) in enumerate(edges):
   d=pp[v]-pp[u];along=(mid-pp[u])@d/(d@d);perp=abs(np.linalg.det([mid-pp[u],d]))/np.linalg.norm(d)
   if .02<along<.98 and perp<3 and abs((h-g)@d)/(dist*np.linalg.norm(d))<.25:ans.add(ei)
 return ans

def unfold(cutset):
 W=V@B
 adj={i:[] for i in range(len(faces))}
 for ei,(u,v) in enumerate(edges):
  ff=[i for i,f in enumerate(faces) if u in f and v in f]
  assert len(ff)==2
  if ei not in cutset:
   i,j=ff;adj[i].append((j,u,v));adj[j].append((i,u,v))
 net={0:W[faces[0],:2]};queue=[0]
 while queue:
  i=queue.pop(0)
  for j,u,v in adj[i]:
   if j in net:continue
   a=net[i][faces[i].index(u)];b=net[i][faces[i].index(v)];d=(b-a)/np.linalg.norm(b-a);ort=np.array([-d[1],d[0]])
   if (net[i].mean(0)-a)@ort>0:ort=-ort
   p=W[v]-W[u];p=p/np.linalg.norm(p)
   out=[]
   for w in faces[j]:
    dd=W[w]-W[u];x=dd@p;h=np.sqrt(max(0,dd@dd-x*x));out.append(a+x*d+h*ort)
   net[j]=np.array(out);queue.append(j)
 return net
def refine(c,ps):
 rank,ids,M,t,shear,err,count=c
 vv=sorted(set(v for i in ids for v in faces[i]));X=np.c_[V[vv],np.ones(len(vv))]
 for it in range(3):
  pp=V[vv]@M+t;dist=np.linalg.norm(pp[:,None]-ps,axis=2);js=dist.argmin(1);valid=dist.min(1)<8
  fit=np.linalg.lstsq(X[valid],ps[js[valid]],rcond=None)[0];M=fit[:3];t=fit[3]
 return M,t

def facefront(ids,M):
 W=V@B
 C=np.linalg.solve(B,M)
 view=np.cross(C[:,0],C[:,1]);scores={}
 for i in ids:
  f=faces[i];n=np.cross(W[f[1]]-W[f[0]],W[f[2]]-W[f[1]])
  if i<ncap:n=-n
  scores[i]=n@view
 return scores

def make_texture(ids,M,t,a,net,canvas,lo,scale,sign):
 # A projected front face can still be partly hidden by another panel of the
 # same rigid piece. Only transport genuinely visible pixels; cap ink makes
 # this distinction essential. This is a camera-depth test, not an ink label.
 pp=V@M+t;front=facefront(ids,M);W=V@B
 C=np.linalg.solve(B,M);look=np.cross(C[:,0],C[:,1])*sign
 look/=np.linalg.norm(look)
 h,w=a.shape;yy,xx=np.mgrid[:h,:w];grid=np.stack([xx,yy,np.ones_like(xx)],axis=-1)
 depths=np.full((h,w),-np.inf);owner=np.full((h,w),-1,dtype=int)
 for i in ids:
  src=pp[faces[i]];poly=W[faces[i]]
  if abs(np.linalg.det(np.c_[src[:3],np.ones(3)]))<1e-5:continue
  inverse=np.linalg.lstsq(np.c_[src,np.ones(len(src))],poly,rcond=None)[0]
  depth=(grid@inverse)@look
  mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([tuple(v)for v in src],fill=255)
  active=(np.array(mask)>0)&(depth>depths+1e-5)
  depths[active]=depth[active];owner[active]=i
 clean=Image.fromarray(a.copy());dd=ImageDraw.Draw(clean)
 used=set(tuple(sorted((u,v)))for fidx in ids for u,v in zip(faces[fidx],faces[fidx][1:]+faces[fidx][:1]))
 for u,v in used:dd.line([tuple(pp[u]),tuple(pp[v])],fill=255,width=5)
 for n,r,e,count in lines(a):
  if any(max(abs(pp[u]@n-r),abs(pp[v]@n-r))<4 for u,v in used):
   ee=e+(e-e[::-1])/np.linalg.norm(e[0]-e[1])*3
   dd.line([tuple(ee[0]),tuple(ee[1])],fill=255,width=5)
 for i in ids:
  src=pp[faces[i]];dest=(net[i]-lo)*scale+20
  A=np.linalg.lstsq(np.c_[dest,np.ones(len(dest))],src,rcond=None)[0]
  affine=tuple(A.T.ravel())
  trans=clean.transform(canvas.size,Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC,fillcolor=255)
  visible=Image.fromarray((owner==i).astype('uint8')*255)
  visible=visible.transform(canvas.size,Image.Transform.AFFINE,affine,Image.Resampling.NEAREST,fillcolor=0)
  mask=Image.new('L',canvas.size);ImageDraw.Draw(mask).polygon([tuple(v)for v in dest],fill=255)
  mask=Image.fromarray(np.minimum(np.array(mask),np.array(visible)))
  merged=Image.fromarray(np.minimum(np.array(canvas),np.array(trans)))
  canvas.paste(merged,(0,0),mask)
 return canvas


def enclosed(a):
    result=[]
    for p in components(a>190):
        lo=p.min(0);hi=p.max(0)
        if len(p)>1000 and all(lo>0) and hi[0]<a.shape[1]-1 and hi[1]<a.shape[0]-1:
            result.append(p)
    return max(result,key=len) if result else None


def groups(im):
    a=np.array(im)
    dil=Image.fromarray((a<120).astype('uint8')*255).filter(ImageFilter.MaxFilter(21))
    result=[]
    for p in components(np.array(dil)>0):
        lo=p.min(0);hi=p.max(0)
        if min(hi-lo)>130:
            box=tuple(map(int,(*lo-5,*hi+6)))
            result.append((box,np.array(im.crop(box))))
    return result


def cluster_levels(values,tol=8):
    clusters=[]
    for x in sorted(values):
        if clusters and x-np.mean(clusters[-1])<tol:clusters[-1].append(x)
        else:clusters.append([x])
    return [float(np.mean(c))for c in clusters]


def read_end_outline(im,regions):
    """Recover the sole unlabelled end outline and its equal square-cell structure."""
    global unit,depth,shear,B,V,quads,faces,edges,nend,ncap,origins3d,side_quads,surface_edges,signs
    info=[]
    for box,a in regions:
        p=enclosed(a)
        if p is None:continue
        ys=np.unique(p[:,1]);left=[];right=[]
        for y in ys:
            xx=p[p[:,1]==y,0];left.append(xx.min());right.append(xx.max()+1)
        info.append((len(set(left))+len(set(right)),box,a,p))
    info.sort(key=lambda v:v[0])
    if len(info)!=1:raise ValueError('Cannot identify the sole end outline')
    _,box,a,p=info[0]
    ylevels=[];xlevels=[]
    for y in np.unique(p[:,1]):
        xx=p[p[:,1]==y,0];xlevels.extend([xx.min(),xx.max()+1])
    for x in np.unique(p[:,0]):
        yy=p[p[:,0]==x,1];ylevels.extend([yy.min(),yy.max()+1])
    corner=vertices(lines(a))
    xs=cluster_levels(corner[:,0]);ys=cluster_levels(corner[:,1])
    mask=np.zeros(a.shape,bool);mask[p[:,1],p[:,0]]=True
    cellgrid=np.array([[mask[int((y+yy)/2),int((x+xx)/2)]for x,xx in zip(xs,xs[1:])]for y,yy in zip(ys,ys[1:])])
    # Canonical orientation: fullest top row, then rightmost cells first.
    cellgrid=max((np.rot90(cellgrid,k)for k in range(4)),key=lambda g:(int(g[0].sum()),tuple(g[:,::-1].ravel())))
    # Only the end outline survives. Extrusion height and offsets are NOT
    # available here and must be jointly reconstructed from the spatial views.
    unit=1.0;depth=1.0;shear=np.zeros(2)
    cells=[(x,y)for y,row in enumerate(cellgrid)for x,v in enumerate(row)if v]
    coords=sorted(set((x+dx,y+dy)for x,y in cells for dx,dy in [(0,0),(1,0),(1,1),(0,1)]),key=lambda p:(p[1],p[0]))
    index={p:i for i,p in enumerate(coords)};nend=len(coords)
    V=np.array([(x,y,z)for z in [0,1]for x,y in coords],float)
    cap=[[index[x,y],index[x+1,y],index[x+1,y+1],index[x,y+1]]for x,y in cells]
    quads=cap+[[v+nend for v in q]for q in cap];ncap=len(cap)
    boundary=set()
    for f in cap:
        for u,v in zip(f,f[1:]+f[:1]):
            if (v,u)in boundary:boundary.remove((v,u))
            else:boundary.add((u,v))
    cycle=[];u=min(u for u,v in boundary)
    while len(cycle)<len(boundary):
        cycle.append(u);u=next(v for uu,v in boundary if uu==u)
    side_quads=[[u,v,v+nend,u+nend]for u,v in zip(cycle,cycle[1:]+cycle[:1])]
    origins3d=[q[0]for q in quads]
    signs=None
    B=None
    surface_edges=sorted(set(tuple(sorted((u,v)))for f in side_quads for u,v in zip(f,f[1:]+f[:1])))
    set_diagonals([0]*len(side_quads))
    log(f'Pixels: {len(cells)} square end cells; extrusion metric unknown')


def set_diagonals(choices):
    global faces,edges
    faces=[list(q)for q in quads]
    for q,ch in zip(side_quads,choices):
        if ch:q=q[1:]+q[:1]
        u,v,w,z=q;faces.extend([[u,v,w],[u,w,z]])
    edges=sorted(set(tuple(sorted((u,v)))for f in faces for u,v in zip(f,f[1:]+f[:1])))


def letter_template(ch):
    im=Image.new('L',(150,150));ImageDraw.Draw(im).text((5,0),ch,font=FONT,fill=255)
    return cropmask(np.array(im)>100)


def runs(v):
    b=np.r_[False,v,False].astype(int)
    return list(zip(np.where(np.diff(b)==1)[0],np.where(np.diff(b)==-1)[0]))


def recognize(im):
    # Suppress thin structural remnants, keeping the much thicker printed ink.
    ink=Image.fromarray((np.array(im)<100).astype('uint8')*255).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
    im=Image.fromarray(255-np.array(ink));a=np.array(im);pcs=[p for p in components(a<100)if len(p)>45]
    if len(pcs)<3:raise ValueError('No reconstructed letter strokes')
    pts=np.concatenate(pcs);cen=pts.mean(0);_,_,vh=np.linalg.svd(pts-cen,full_matrices=False);t=vh[0];t*=np.sign(t[0]);n=np.array([-t[1],t[0]])
    for k in range(4):
        dis=pts@n;use=abs(dis-np.median(dis))<60;cov=np.cov(pts[use].T);_,v=np.linalg.eigh(cov);t=v[:,-1];t*=np.sign(t[0]);n=np.array([-t[1],t[0]])
    angle=math.degrees(math.atan2(t[1],t[0]));results=[]
    for flip in [float(z)-angle for z in range(0,360,5)]:
        rot=im.rotate(angle+flip,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=255)
        a=np.array(rot);row=(a<100).sum(1);rr=runs(row>5)
        if not rr:continue
        # Keep every text row, deriving their order from the upright raster.
        # Thin isolated arrow/edge remnants are excluded by height and ink mass.
        rr=[(y0,y1)for y0,y1 in rr if y1-y0>15 and row[y0:y1].sum()>row.sum()*.10
            and np.ptp(np.where((a[y0:y1]<100).any(axis=0))[0])>1.5*(y1-y0)]
        word=[];quality=[];readrows=[]
        for y0,y1 in rr:
            band=a[max(0,y0-3):y1+3]
            col=(band<100).sum(0);rs=runs(col>1);merged=[]
            for l,r in rs:
                if merged and l-merged[-1][1]<band.shape[0]*.08:merged[-1]=(merged[-1][0],r)
                else:merged.append((l,r))
            for l,r in merged:
                b=cropmask(band[:,l:r]<100);scores=[]
                if b.sum()<80:continue
                for ch in string.ascii_uppercase:
                    tt=letter_template(ch);res=np.array(Image.fromarray(tt).resize((b.shape[1],b.shape[0]),Image.Resampling.NEAREST))
                    score=(b&res).sum()/(b.sum()+.35*res.sum())
                    aspect=(b.shape[1]/b.shape[0])/(tt.shape[1]/tt.shape[0])
                    score-=.10*abs(math.log(aspect))
                    score-=.12*max(0,.80-b.shape[0]/band.shape[0])
                    scores.append((float(score),ch))
                scores.sort(reverse=True);word.append(scores[0][1]);quality.append(scores[0][0])
            readrows.append(band)
        if word:
            readout=a[max(0,rr[0][0]-3):rr[-1][1]+3]
            results.append((float(np.mean(quality)),''.join(word),Image.fromarray(readout)))
    if not results:raise ValueError('Letter recognition failed')
    return max(results,key=lambda r:r[0])


def metric_symmetries(W):
    dist=np.linalg.norm(W[:,None]-W[None],axis=2)
    anchors=next(ids for ids in itertools.combinations(range(len(W)),4) if abs(np.linalg.det(np.c_[W[list(ids)],np.ones(4)]))>.1)
    out=[]
    for ids in itertools.permutations(range(len(W)),4):
        if np.max(abs(dist[np.ix_(anchors,anchors)]-dist[np.ix_(ids,ids)]))>.02:continue
        ds=np.linalg.norm(dist[:,anchors][:,None,:]-dist[:,ids][None,:,:],axis=2)
        perm=ds.argmin(1)
        if ds.min(1).max()>.03 or len(set(perm))!=len(W):continue
        if not any(np.array_equal(perm,z)for z in out):out.append(perm)
    return out


METRIC_EVIDENCE={}
def infer_spatial_metric(fits):
    """Calibrate orthographic cameras from square end faces; triangulate extrusion.

    Each projected orthonormal end basis fixes the camera scale (largest
    singular value) and its normal projection up to sign. Across views the
    common extrusion is a*x + b*y + h*normal. Solve those equations jointly,
    including unlabelled-view coordinate symmetries and depth-sign choices.
    """
    global depth,shear,signs,B,METRIC_EVIDENCE
    permutations=metric_symmetries(V)
    options=[]
    for a,M,t in fits:
        choices=[]
        for perm in permutations:
            pp=(V@M+t)[perm]
            fit=np.linalg.lstsq(np.c_[V,np.ones(len(V))],pp,rcond=None)[0]
            m=fit[:3];axes=m[:2];scale=np.linalg.svd(axes,compute_uv=False)[0]
            ev,vec=np.linalg.eigh(scale*scale*np.eye(2)-axes@axes.T)
            zz=vec[:,-1]*np.sqrt(max(0,ev[-1]))
            u=np.r_[axes[0],zz[0]]/scale;v=np.r_[axes[1],zz[1]]/scale
            normal=np.cross(u,v)[:2]
            for sign in [-1,1]:choices.append((np.array([axes[0]/scale,axes[1]/scale,sign*normal]).T,m[2]/scale))
        options.append(choices)
    candidates=[]
    # Fix the first view's arbitrary coordinates. Enumerate all relative choices.
    for ix in itertools.product(range(len(options[0])),repeat=len(fits)-1):
        chosen=[options[0][0]]+[opts[i]for opts,i in zip(options[1:],ix)]
        X=np.vstack([a for a,b in chosen]);y=np.concatenate([b for a,b in chosen])
        metric=np.linalg.lstsq(X,y,rcond=None)[0]
        residual=float(np.linalg.norm(X@metric-y))
        if abs(metric[2])>.1:candidates.append((residual,metric,ix))
    residual,metric,indices=min(candidates,key=lambda x:x[0])
    if residual>.045:raise ValueError('Multi-view orthographic calibration is inconsistent')
    depth=abs(float(metric[2]));shear=abs(metric[:2]);signs=tuple(int(v)for v in np.sign(metric[:2]))
    B=np.array([[unit,0,0],[0,unit,0],[metric[0],metric[1],depth]])
    METRIC_EVIDENCE={'source':'four spatial target views and square end geometry; no side silhouettes or numeric dimensions',
                     'relative_camera_choices':list(indices),'equation_residual':residual,'metric':metric.tolist(),
                     'camera_hypotheses_tested':len(candidates)}
    log(f'Multi-view calibration: offsets={metric[:2]}, height={depth:.6f}, residual={residual:.6f}')


def solve_directory(directory, evidence_directory=None):
    global B,signs
    pages=[]
    for path in sorted(Path(directory).glob('*.png')):
        im=Image.open(path).convert('L')
        # A common working resolution controls raster tolerances, never locations.
        if im.width!=1700:im=im.resize((1700,round(im.height*1700/im.width)),Image.Resampling.LANCZOS)
        pages.append((path,im,groups(im)))
    if not pages:raise ValueError('Input directory contains no PNG images')
    target_candidates=[p for p in pages if len(p[2])==5]
    if len(target_candidates)!=1:raise ValueError('Cannot identify target/end-outline page')
    _,target,regions=target_candidates[0]
    regions.sort(key=lambda r:-(r[0][2]-r[0][0])*(r[0][3]-r[0][1]))
    views=sorted(regions[:4],key=lambda r:(round(r[0][1]/100),r[0][0]))
    read_end_outline(target,regions[4:])
    affine_fits=[]
    for box,a in views:
        fit,_=affine_targetfit(a)
        if fit is None or fit[0]<len(surface_edges)*.88:raise ValueError('Cannot reconstruct target lattice without a metric')
        affine_fits.append((a,fit[1],fit[2]))
    infer_spatial_metric(affine_fits)
    fits=[]
    for box,a in views:
        best=targetfit(a)[0]
        if best is None or best[0]<len(surface_edges)*.88:raise ValueError('Target physical creases cannot be recovered')
        fits.append((a,best[1],best[2]))
    # Both diagonal choices are hypotheses. Recover the partition jointly from
    # source-piece faces and observed cut seams; never read missing target lines.
    global faces,edges
    faces=[list(q) for q in quads]
    for q in side_quads:
        for k in (0,1):
            r=q[k:]+q[:k];u,v,w,z=r;faces.extend([[u,v,w],[u,w,z]])
    edges=sorted(set(tuple(sorted((u,v)))for f in faces for u,v in zip(f,f[1:]+f[:1])))
    symmetries=metric_symmetries(V@B)
    cut_options=[]
    for a,M,t in fits:
        options=[]
        for perm in symmetries:
            pp=(V@M+t)[perm]
            fit=np.linalg.lstsq(np.c_[V,np.ones(len(V))],pp,rcond=None)[0]
            options.append({edges[i] for i in cuts(a,fit[:3],fit[3])})
        cut_options.append(options)
    log(f'Pixels: {len(symmetries)} shell coordinate symmetries; cuts require joint view registration')
    # Rigid piece silhouettes are the large, continuous dark components.
    choices=[]
    for path,im,_ in pages:
        if im is target:continue
        a=np.array(im);boxes=[]
        for p in components(a<100):
            lo=p.min(0);hi=p.max(0)
            if min(hi-lo)>65 and len(p)/np.prod(hi-lo)<.25:boxes.append((lo,hi))
        # A circular magnification inset is wide and short, and lacks long edges.
        diagrams=[]
        for lo,hi in boxes:
            crop=np.array(im.crop(tuple(map(int,(*lo-8,*hi+9)))))
            ls=lines(crop)
            if len(ls)>=8:diagrams.append((lo,crop))
        if len(diagrams)>=6 and len(diagrams)%2==0:choices.append(diagrams)
    if len(choices)!=1:raise ValueError('Cannot identify paired rigid piece views')
    diagrams=sorted(choices[0],key=lambda r:(round(r[0][1]/100),r[0][0]))
    matches=[]
    for k,(lo,a)in enumerate(diagrams):
        cs,ps=match(a);byfaces={}
        for c in cs:
            if c[4]!=signs:continue
            key=tuple(c[1])
            if key not in byfaces:byfaces[key]=(c,ps,a)
        matches.append(byfaces)
        log(f'Piece view {k+1}: {len(byfaces)} geometric candidates')
    # No source IDs or view-pair labels are printed. A pair is a hypothesis
    # only when the two independent cameras recover exactly the same rigid
    # set of panels. Solve view pairing and shell coverage together.
    pair_options={}
    for i,j in itertools.combinations(range(len(matches)),2):
        common=matches[i].keys()&matches[j].keys()
        pair_options[i,j]=[(key,matches[i][key],matches[j][key])for key in common]
    log(f"Unlabelled view pairs: {sum(bool(v)for v in pair_options.values())} possible pairs")
    paired=[pair_options[k]for k in sorted(pair_options)]
    assemblies=[]
    def admissible(used):
        for k in range(len(side_quads)):
            fs=used.intersection(range(len(quads)+4*k,len(quads)+4*k+4))
            if len({(f-len(quads))%4//2 for f in fs})>1:return False
        return True
    def cover(remaining,used,chosen):
        if not remaining:
            if len(used)==len(quads)+2*len(side_quads):assemblies.append(chosen)
            return
        i=min(remaining)
        for j in sorted(remaining-{i}):
            for option in pair_options[i,j]:
                key=option[0];next_used=used|set(key)
                if not used.intersection(key) and admissible(next_used):
                    cover(remaining-{i,j},next_used,chosen+[option])
    cover(set(range(len(matches))),set(),[])
    log(f'Joint view-pair and panel-cover hypotheses: {len(assemblies)}')
    hypothesis_faces=faces
    states=[]
    for assembly in assemblies:
        used=sorted(set(i for ids,_,_ in assembly for i in ids))
        old_to_new={old:i for i,old in enumerate(used)}
        faces=[hypothesis_faces[i] for i in used]
        edges=sorted(set(tuple(sorted((u,v)))for f in faces for u,v in zip(f,f[1:]+f[:1])))
        chosen=[([old_to_new[i] for i in ids],v1,v2) for ids,v1,v2 in assembly]
        for indices in itertools.product(range(len(symmetries)),repeat=len(fits)):
            cut_edges=set().union(*(opts[i] for opts,i in zip(cut_options,indices)))
            if not cut_edges<=set(edges) or len(edges)-len(cut_edges)!=len(faces)-1:continue
            cutset={i for i,e in enumerate(edges) if e in cut_edges}
            net=unfold(cutset)
            if len(net)!=len(faces):continue
            states.append((faces.copy(),edges.copy(),chosen,cut_edges,net,indices))
    if not states:raise ValueError('No joint assembly, view registration and connected unfolding')
    # Quotient coordinate conventions by the metric automorphisms of the shell.
    signatures=set()
    for ff,ee,chosen,cc,net,indices in states:
        variants=[]
        for perm in symmetries:
            panels=tuple(sorted(tuple(sorted(tuple(sorted(int(perm[v])for v in ff[i])) for i in ids))for ids,_,_ in chosen))
            seams=tuple(sorted(tuple(sorted(int(perm[v])for v in e))for e in cc))
            variants.append((panels,seams))
        signatures.add(min(variants))
    view_index={id(a):i for i,(lo,a) in enumerate(diagrams)}
    inferred_pairings={tuple(sorted(tuple(sorted((view_index[id(v1[2])],view_index[id(v2[2])])) )for ids,v1,v2 in state[2]))for state in states}
    if len(inferred_pairings)!=1:raise ValueError('Source-view pairing is not unique')
    if len(signatures)!=1:raise ValueError(f'Joint spatial inference has {len(signatures)} inequivalent solutions')
    results=[]
    for state_index,(faces,edges,chosen,cut_edges,net,indices) in enumerate(states):
        pp=np.concatenate(list(net.values()));lo=pp.min(0);hi=pp.max(0);scale=180/unit
        for side in [-1,1]:
            canvas=Image.new('L',tuple(((hi-lo)*scale+40).astype(int)),255)
            for ids,view1,view2 in chosen:
                for c,ps,a in [view1,view2]:
                    c=(c[0],ids,*c[2:]);M,t=refine(c,ps);make_texture(ids,M,t,a,net,canvas,lo,scale,side)
            if evidence_directory is not None:
                debug=Path(evidence_directory);debug.mkdir(parents=True,exist_ok=True)
                canvas.save(debug/f'canvas_{state_index}_{side}.png')
            for oriented in [canvas,canvas.transpose(Image.Transpose.FLIP_LEFT_RIGHT)]:
                try:
                    score,word,readout=recognize(oriented)
                    results.append((score,word,readout,state_index))
                except (ValueError,IndexError):pass
    if not results:raise ValueError('No readable reconstructed lettering')
    score,word,readout,state_index=max(results,key=lambda r:r[0])
    if evidence_directory is not None:
        debug=Path(evidence_directory);debug.mkdir(parents=True,exist_ok=True)
        readout.save(debug/'best_readout.png')
        (debug/'recognition_candidates.txt').write_text(str(sorted([(r[0],r[1])for r in results],reverse=True)))
    if score<.55:raise ValueError(f'Reconstructed lettering has low confidence ({score:.3f})')
    plausible={r[1]for r in results if r[0]>=max(.55,score-.025)}
    if len(plausible)!=1:raise ValueError(f'Letter readout is ambiguous: {sorted(plausible)}')
    log(f'Joint reconstruction: {len(states)} coordinate representatives, {len(signatures)} spatial orbit')
    if evidence_directory is not None:
        import json,hashlib
        out=Path(evidence_directory);out.mkdir(parents=True,exist_ok=True)
        readout.save(out/'reconstructed_readout.png')
        ff,ee,chosen,cc,net,indices=states[state_index]
        evidence={'input_png_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest()for path,_,_ in pages},
                  'metric_reconstruction':METRIC_EVIDENCE,
                  'normalized_metric':{'unit':unit,'depth':depth,'offsets':shear.tolist(),'signs':list(signs)},
                  'hypothesis_panel_count':len(hypothesis_faces),'unlabelled_view_pair_candidate_counts':{str(k):len(v)for k,v in pair_options.items()},
                  'view_pairing_inferred':True,'inferred_view_pairs':list(next(iter(inferred_pairings))),
                  'coordinate_representatives':len(states),'spatial_orbits':len(signatures),
                  'faces':ff,'cuts':sorted(cc),'hinges':len(ee)-len(cc),'registered_views':list(indices),
                  'generic_A_Z_readings':[{'confidence':r[0],'word':r[1]}for r in results],
                  'answer':word,'confidence':score,'reads_author_scene':False}
        (out/'pixel_reconstruction.json').write_text(json.dumps(evidence,indent=2)+'\n')
    log(f'Unique assembly; alphabet template confidence {score:.3f}')
    return word
