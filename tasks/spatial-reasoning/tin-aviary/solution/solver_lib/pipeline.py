"""Pixel-only reconstruction of extruded grid solids, seams and lettering.

All mesh vertices, face memberships, cuts and letter positions are measured
at runtime. No authored scene, solution, or cached measurements are loaded.
"""
import os
os.environ["OPENBLAS_NUM_THREADS"]="1"
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
def normalized(a):return np.array(Image.fromarray(cropmask(a).astype('uint8')*255).resize((32,44),Image.Resampling.BILINEAR))>100
T={}
for ch in '0123456789':
 im=Image.new('L',(140,140));ImageDraw.Draw(im).text((5,0),ch,font=FONT,fill=255);T[ch]=normalized(np.array(im)>100)

def digits(a):
 result=[]
 for p in components(a<100):
  lo=p.min(0);hi=p.max(0);w,h=hi-lo+1
  if 13<h<33 and 5<w<30:
   b=np.zeros((h,w),bool);b[p[:,1]-lo[1],p[:,0]-lo[0]]=1;b=normalized(b)
   scores=[((b&t).sum()/(b|t).sum(),ch)for ch,t in T.items()];score,ch=max(scores)
   if score>.68:result.append((ch,p.mean(0),score))
 return result
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
      rank=explained+len(fids)*2-error*4+20*visibility_score(a,M,shift,fids)
      candidates.append((rank,fids,M,shift,(sx,sy),error,explained))
 candidates.sort(key=lambda c:-c[0]);return candidates,ps
def visibility_score(a,M,t,ids=None):
    metric=np.array([[unit,0,0],[0,unit,0],[signs[0]*shear[0],signs[1]*shear[1],depth]])
    W=V@metric;C=np.linalg.solve(metric,M);look=-np.cross(C[:,0],C[:,1]);look/=np.linalg.norm(look)
    polygons=quads+side_quads if ids is None else [faces[i] for i in ids]
    ee=surface_edges if ids is None else sorted(set(tuple(sorted((u,v))) for f in polygons for u,v in zip(f,f[1:]+f[:1])))
    ends=np.array(ee);ts=np.linspace(.12,.88,17)
    points=(W[ends[:,0],None]*(1-ts)[None,:,None]+W[ends[:,1],None]*ts[None,:,None]).reshape(-1,3)
    pp=(V[ends[:,0],None]*(1-ts)[None,:,None]+V[ends[:,1],None]*ts[None,:,None]).reshape(-1,3)@M+t
    shown=np.ones(len(points),bool)
    for f in polygons:
        p=W[f];o=p[0];u=p[1]-o;u/=np.linalg.norm(u);n=np.cross(p[1]-o,p[2]-o);n/=np.linalg.norm(n);v=np.cross(n,u);den=n@look
        if abs(den)<1e-7:continue
        distance=(o-points)@n/den;hit=points+distance[:,None]*look
        q=np.c_[(hit-o)@u,(hit-o)@v];poly=np.c_[(p-o)@u,(p-o)@v]
        cross=np.array([(bb[0]-aa[0])*(q[:,1]-aa[1])-(bb[1]-aa[1])*(q[:,0]-aa[0])for aa,bb in zip(poly,np.roll(poly,-1,axis=0))])
        inside=(cross.min(0)>-1e-6)|(cross.max(0)<1e-6)
        shown&=~((distance>1e-5)&inside)
    xy=np.rint(pp).astype(int);valid=(xy[:,0]>3)&(xy[:,0]<a.shape[1]-4)&(xy[:,1]>3)&(xy[:,1]<a.shape[0]-4)
    xy=xy[valid];shown=shown[valid]
    if not len(xy):return 0.
    dark=np.min([a[xy[:,1]+dy,xy[:,0]+dx]for dx,dy in itertools.product(range(-2,3),repeat=2)],axis=0)<55
    return float(np.mean(dark==shown))

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
     scores += [max(sample(a,pred[q[0]],pred[q[2]]),sample(a,pred[q[1]],pred[q[3]])) for q in side_quads]
    rank=sum(scores)+12*visibility_score(a,M,shift)
    if best is None or rank>best[0]:
     best=(rank,M,shift)
    

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
   if .1<along<.9 and perp<4 and abs((h-g)@d)/(dist*np.linalg.norm(d))<.25:ans.add(ei)
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
 pp=V@M+t;front=facefront(ids,M);detected_lines=lines(a)
 for i in ids:
  if front[i]*sign<0:continue
  src=pp[faces[i]];dest=(net[i]-lo)*scale+20
  A=np.linalg.lstsq(np.c_[dest,np.ones(len(dest))],src,rcond=None)[0]
  trans=Image.fromarray(a).transform(canvas.size,Image.Transform.AFFINE,tuple(A.T.ravel()),Image.Resampling.BICUBIC,fillcolor=255)
  mask=Image.new('L',canvas.size);dr=ImageDraw.Draw(mask);dr.polygon([tuple(v)for v in dest],fill=255)
  # Remove the geometrical outline, preserving the interior lettering.
  # Mask all drawn structural lines in the source image, except their interiors.
  clean=Image.fromarray(a.copy());dd=ImageDraw.Draw(clean)
  used=set(tuple(sorted((u,v)))for fidx in ids for u,v in zip(faces[fidx],faces[fidx][1:]+faces[fidx][:1]))
  for u,v in used:dd.line([tuple(pp[u]),tuple(pp[v])],fill=255,width=8)
  # Re-mask detected lines to remove subpixel residuals from the affine fit.
  for n,r,e,count in detected_lines:
   if any(max(abs(pp[u]@n-r),abs(pp[v]@n-r))<5 for u,v in used):
    ee=e+(e-e[::-1])/np.linalg.norm(e[0]-e[1])*5
    dd.line([tuple(ee[0]),tuple(ee[1])],fill=255,width=7)
  trans=clean.transform(canvas.size,Image.Transform.AFFINE,tuple(A.T.ravel()),Image.Resampling.BICUBIC,fillcolor=255)
  canvas.paste(trans,(0,0),mask)
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


def read_dimensions(im,regions):
    """Find enclosed dimension outlines; read their adjacent numeric labels."""
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
    if len(info)<3:raise ValueError('Cannot identify the three dimension outlines')
    _,box,a,p=info[0]
    ylevels=[];xlevels=[]
    for y in np.unique(p[:,1]):
        xx=p[p[:,1]==y,0];xlevels.extend([xx.min(),xx.max()+1])
    for x in np.unique(p[:,0]):
        yy=p[p[:,0]==x,1];ylevels.extend([yy.min(),yy.max()+1])
    xs=cluster_levels(xlevels);ys=cluster_levels(ylevels)
    mask=np.zeros(a.shape,bool);mask[p[:,1],p[:,0]]=True
    cellgrid=np.array([[mask[int((y+yy)/2),int((x+xx)/2)]for x,xx in zip(xs,xs[1:])]for y,yy in zip(ys,ys[1:])])
    # Canonical orientation: fullest top row, then rightmost cells first.
    cellgrid=max((np.rot90(cellgrid,k)for k in range(4)),key=lambda g:(int(g[0].sum()),tuple(g[:,::-1].ravel())))
    def annotations(box,p):
        l,t,r,b=box;expanded=im.crop((l-90,t-90,r+90,b+90));ds=digits(np.array(expanded))
        lo=p.min(0)+90;hi=p.max(0)+90
        return ds,lo,hi
    ds,lo,hi=annotations(box,p)
    endnums=[int(c)for c,pt,s in ds if (pt[0]<lo[0] and lo[1]<pt[1]<hi[1])or(pt[1]>hi[1] and lo[0]<pt[0]<hi[0])]
    if not endnums or len(set(endnums))!=1:raise ValueError('End dimensions are not a uniform readable grid')
    unit=float(endnums[0]);depths=[];offsets=[]
    for _,box,a,p in sorted(info[1:],key=lambda entry:entry[1][0]):
        ds,lo,hi=annotations(box,p)
        h=[int(c)for c,pt,s in ds if pt[0]<lo[0] and lo[1]<pt[1]<hi[1]]
        sh=[int(c)for c,pt,s in ds if lo[1]-100<pt[1]<lo[1] and (lo[0]+hi[0])/2<pt[0]<hi[0]+15]
        if len(h)!=1 or len(sh)!=1:raise ValueError('Cannot read extrusion dimensions')
        depths.extend(h);offsets.extend(sh)
    if len(set(depths))!=1:raise ValueError('Side dimensions disagree')
    depth=float(depths[0]);shear=np.array(offsets,dtype=float)
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
    surface_edges=sorted(set(tuple(sorted((u,v)))for f in quads+side_quads for u,v in zip(f,f[1:]+f[:1])))
    set_diagonals([0]*len(side_quads))
    log(f'Pixels: {len(cells)} end cells; unit={unit:g}, depth={depth:g}, side offsets={offsets}')


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
    a=np.array(im);pcs=[p for p in components(a<100)if len(p)>45]
    if len(pcs)<3:raise ValueError('No reconstructed letter strokes')
    pts=np.concatenate(pcs);cen=pts.mean(0);_,_,vh=np.linalg.svd(pts-cen,full_matrices=False);t=vh[0];t*=np.sign(t[0]);n=np.array([-t[1],t[0]])
    base=math.atan2(t[1],t[0])
    # Find the narrowest robust ink band. PCA alone is biased by uneven
    # letters and by the material arrow away from the reading row.
    scores=[]
    for aa in base+np.deg2rad(np.arange(-15,15.01,.2)):
        nn=np.array([-math.sin(aa),math.cos(aa)])
        low,high=np.percentile(pts@nn,[1,99]);scores.append((high-low,aa))
    angle=math.degrees(min(scores)[1]);results=[]
    for flip in [0,180]:
        rot=im.rotate(angle+flip,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=255)
        a=np.array(rot);row=(a<100).sum(1);rr=runs(row>5)
        if not rr:continue
        y0,y1=max(rr,key=lambda r:row[r[0]:r[1]].sum());a=a[max(0,y0-3):y1+3]
        col=(a<100).sum(0);rs=runs(col>1);merged=[]
        for l,r in rs:
            if merged and l-merged[-1][1]<a.shape[0]*.10:merged[-1]=(merged[-1][0],r)
            else:merged.append((l,r))
        word=[];quality=[]
        for l,r in merged:
            b=cropmask(a[:,l:r]<100);scores=[]
            if b.sum()<80:continue
            for ch in string.ascii_uppercase:
                tt=letter_template(ch);res=np.array(Image.fromarray(tt).resize((b.shape[1],b.shape[0]),Image.Resampling.NEAREST))
                score=(b&res).sum()/(b.sum()+.35*res.sum())
                scores.append((float(score),ch))
            scores.sort(reverse=True);word.append(scores[0][1]);quality.append(scores[0][0])
        if word:results.append((float(np.mean(quality)),''.join(word),Image.fromarray(a)))
    if not results:raise ValueError('Letter recognition failed')
    return max(results,key=lambda r:r[0])


def solve_directory(directory,debug_dir=None):
    global B,signs
    pages=[]
    for path in sorted(Path(directory).glob('*.png')):
        im=Image.open(path).convert('L')
        if im.size!=(2400,1800):im=im.resize((2400,1800),Image.Resampling.LANCZOS)
        pages.append((path,im,[]))
    if len(pages)!=3:raise ValueError('Three workshop sheets are required')
    target=pages[2][1]
    regions=[(box,np.array(target.crop(box))) for box in [(100,1400,700,1780),(760,1400,1450,1780),(1550,1400,2250,1780)]]
    views=[]
    for k in range(4):
        x=90+1140*(k%2);y=280+515*(k//2)
        box=(x+90,y+25,x+1030,y+475)
        views.append((box,np.array(target.crop(box))))
    read_dimensions(target,regions)
    # Fit both possible diagonals from line support, before interpreting seams.
    # Determine the signed extrusion from the measured projections.
    metric_options=[]
    for sg in itertools.product([-1,1],repeat=2):
        signs=sg
        candidate,_=targetfit(views[0][1])
        if candidate is not None:metric_options.append((candidate[0],sg,candidate))
    if not metric_options:raise ValueError('Cannot infer signed extrusion')
    _,signs,first=max(metric_options,key=lambda v:(round(v[0],3),v[1][0]))
    B=np.array([[unit,0,0],[0,unit,0],[signs[0]*shear[0],signs[1]*shear[1],depth]])
    log(f'Projection-derived shear signs: {signs}')
    _,M,t=first;pp=V@M+t;a=views[0][1]
    votes=np.array([[sample(a,pp[q[k]],pp[q[k+2]])for k in [0,1]]for q in side_quads])
    set_diagonals(votes.argmax(1))
    fits=[]
    for vi,(box,a) in enumerate(views):
        best=first if vi==0 else targetfit(a,known_diagonals=True)[0]
        log(f'Target view {vi+1}: projection and visibility score {None if best is None else round(best[0],3)}')
        if best is None or best[0]<len(edges)*.9:raise ValueError('Target projection cannot be recovered')
        _,M,t=best;fits.append((a,M,t))
    cutset=set().union(*(cuts(a,M,t)for a,M,t in fits))
    net=unfold(cutset)
    if len(net)!=len(faces) or len(edges)-len(cutset)!=len(faces)-1:
        raise ValueError('Recognized seams do not form a spanning hinge tree')
    log(f'Pixels: {len(faces)} faces, {len(cutset)} cuts; connected unfolded surface')
    # Layout windows contain only drawings. All geometry is fitted from their pixels.
    diagrams=[];im=pages[1][1]
    for i in range(4):
        x=90+570*i
        for k in range(2):
            y=320+680*k
            box=(x+5,y+95,x+535,y+625)
            diagrams.append((np.array(box[:2]),np.array(im.crop(box))))
    matches=[]
    for k,(lo,a)in enumerate(diagrams):
        cs,ps=match(a);byfaces={}
        for c in cs:
            if c[4]!=signs:continue
            key=tuple(c[1])
            if key not in byfaces:byfaces[key]=(c,ps,a)
        matches.append(byfaces)
        log(f'Piece view {k+1}: {len(byfaces)} geometric candidates')
    # Opposite orthographic views share the same projected vertex set after
    # horizontal reflection. Recover a weak view from the companion's fitted
    # geometry, then independently demand line support in the weak raster.
    for i in range(0,len(matches),2):
        for k,j in [(i,i+1),(i+1,i)]:
            if matches[k]:continue
            a=diagrams[k][1];actual_ps=vertices(lines(a))
            for key,(c,ps,other) in matches[j].items():
                rank,ids,M,t,sg,err,count=c
                MM=M*np.array([-1.,1.]);tt=np.array([a.shape[1]-t[0],t[1]])
                pred=V@MM+tt
                used=set(tuple(sorted((u,v)))for fi in ids for u,v in zip(faces[fi],faces[fi][1:]+faces[fi][:1]))
                support=[sample(a,pred[u],pred[v]) for u,v in used]
                if min(support)<.60 or np.mean(support)<.85:continue
                mirrored=ps*np.array([-1.,1.])+[a.shape[1],0]
                matches[k][key]=((rank,ids,MM,tt,sg,err,count),mirrored,a)
            log(f'Complementary view {k+1}: {len(matches[k])} pixel-verified candidates')
    paired=[]
    for i in range(0,len(matches),2):
        common=matches[i].keys()&matches[i+1].keys()
        paired.append([(key,matches[i][key],matches[i+1][key])for key in common])
    assemblies=[]
    def cover(i,used,chosen):
        if i==len(paired):
            if len(used)==len(faces):assemblies.append(chosen)
            return
        for option in paired[i]:
            key=option[0]
            if not used.intersection(key):cover(i+1,used|set(key),chosen+[option])
    cover(0,set(),[])
    if len(assemblies)!=1:raise ValueError(f'Rigid-piece covering is ambiguous ({len(assemblies)} possibilities)')
    pp=np.concatenate(list(net.values()));lo=pp.min(0);hi=pp.max(0);scale=90
    results=[]
    for side in [-1,1]:
        canvas=Image.new('L',tuple(((hi-lo)*scale+40).astype(int)),255)
        for ids,view1,view2 in assemblies[0]:
            for c,ps,a in [view1,view2]:
                M,t=refine(c,ps);make_texture(ids,M,t,a,net,canvas,lo,scale,side)
        for oriented in [canvas,canvas.transpose(Image.Transpose.FLIP_LEFT_RIGHT)]:
            try:results.append(recognize(oriented))
            except (ValueError,IndexError):pass
    if not results:raise ValueError('No readable reconstructed lettering')
    score,word,readout=max(results,key=lambda r:r[0])
    if debug_dir is not None:
        destination=Path(debug_dir);destination.mkdir(parents=True,exist_ok=True)
        try:readout.save(destination/'reconstructed_readout.png')
        except PermissionError:pass
    log('Readout candidates: '+str([(round(q,3),w) for q,w,_ in results]))
    if score<.55:raise ValueError(f'Reconstructed lettering has low confidence ({score:.3f})')
    log(f'Unique assembly; alphabet template confidence {score:.3f}')
    return word
