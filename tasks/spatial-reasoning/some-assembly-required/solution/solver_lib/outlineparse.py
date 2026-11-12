"""Recover unruled mixed-grid paper from PNG silhouettes and mark containment.
No stored net geometry or glyph-centre lattice is used.
"""
import math, collections
import numpy as np
from PIL import Image, ImageDraw
import pixparse as P
from panels import fill_holes


def contour(mask):
    # Clockwise boundary of a union of pixels, including concavities.
    e={}
    z=np.pad(mask,1)
    for dy,dx,aa,bb in [(-1,0,(0,0),(1,0)),(0,1,(1,0),(1,1)),(1,0,(1,1),(0,1)),(0,-1,(0,1),(0,0))]:
        yy,xx=np.nonzero(mask & ~z[1+dy:1+dy+mask.shape[0],1+dx:1+dx+mask.shape[1]])
        for y,x in zip(yy,xx):e[(x+aa[0],y+aa[1])]=(x+bb[0],y+bb[1])
    start=min(e,key=lambda p:(p[1],p[0]));out=[start];p=e[start]
    while p!=start:
        out.append(p);p=e[p]
        if len(out)>len(e):raise ValueError('broken silhouette boundary')
    q=np.asarray(out,float)
    def rdp(q):
        if len(q)<=2:return q
        d=q[-1]-q[0];dist=np.abs(d[0]*(q[:,1]-q[0,1])-d[1]*(q[:,0]-q[0,0]))/max(1,np.linalg.norm(d))
        i=int(dist.argmax())
        if dist[i]<=2.2:return q[[0,-1]]
        return np.vstack((rdp(q[:i+1])[:-1],rdp(q[i:])))
    j=int(np.linalg.norm(q-q[0],axis=1).argmax())
    return np.vstack((rdp(q[:j+1])[:-1],rdp(np.vstack((q[j:],q[:1])))[:-1]))


def outline(gray,box,unit):
    x0,y0,x1,y1=box[:4]
    ink=gray[y0:y1+1,x0:x1+1]<200
    labs,n=P.label(ink,8);st=P.comp_stats(labs,n)
    k=max(st,key=lambda k:st[k]['n'])
    mask=fill_holes(labs==k)
    q=contour(mask)+[x0,y0]
    # Rounded stroke joins can leave tiny RDP segments. Remove them first.
    while True:
        ds=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        if ds.min()>unit*.3:break
        j=int(ds.argmin());q=np.delete(q,(j+1)%len(q),axis=0)
    dirs=[];lengths=[]
    for a,b in zip(q,np.roll(q,-1,axis=0)):
        d=b-a;t=round(math.atan2(d[1],d[0])/(math.pi/4))*math.pi/4
        dirs.append([math.cos(t),math.sin(t)]);lengths.append(np.linalg.norm(d)/unit)
    choices=sorted(set(a+b*math.sqrt(2) for a in range(9) for b in range(9) if 0<a+b<=8))
    lens=[min(choices,key=lambda x:abs(x-l)) for l in lengths]
    exact=np.vstack(([0.,0.],np.cumsum(np.array(dirs)*np.array(lens)[:,None],axis=0)))
    if np.linalg.norm(exact[-1])>1e-4:raise ValueError('silhouette edge lengths do not close')
    exact=exact[:-1];origin=np.mean(q-unit*exact,axis=0)
    residual=np.linalg.norm(q-(origin+unit*exact),axis=1)
    if max(residual)>8:raise ValueError('silhouette not on unit/wedge lattice: '+str((np.round(residual,1).tolist(),np.round(lengths,3).tolist(),lens)))
    return exact,origin,dict(corners=len(q),max_boundary_residual_px=round(float(max(residual)),3))


def inside(points,poly,margin=0):
    points=np.asarray(points);poly=np.asarray(poly)
    x,y=points[:,0],points[:,1];ok=np.zeros(len(points),bool)
    near=np.zeros(len(points),bool)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        d=b-a;t=np.clip(((points-a)*d).sum(1)/(d@d),0,1)
        near|=np.linalg.norm(points-a-t[:,None]*d,axis=1)<=margin
        ok^=((a[1]>y)!=(b[1]>y)) & (x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1]+1e-30)+a[0])
    return ok|near


def glyph_groups(gray,box):
    x0,y0,x1,y1=box[:4];ink=gray[y0:y1+1,x0:x1+1]<150
    lab,n=P.label(ink,8);st=P.comp_stats(lab,n)
    # The enclosing outline is the largest connected ink component.
    rim=max(st,key=lambda k:st[k]['n']);ink[lab==rim]=False
    # Group a glyph with its foot; this contains no assumptions about cell centres.
    grown=P.dilate(ink,4);ll,nn=P.label(grown,8);ss=P.comp_stats(ll,nn)
    groups=[]
    for k,v in ss.items():
        yy,xx=np.nonzero(ink & (ll==k))
        if len(xx)<20:continue
        groups.append(np.array(P.convex_hull(list(zip(xx+x0,yy+y0)))))
    return groups


def candidates(poly,groups):
    """Lattice frames seeded by actual boundary corners, at 0/45 degrees.
    A quadrilateral encloses one whole mark; triangles enclose none. Mark positions
    only reject cuts through ink, and never supply vertex or face-centre coordinates.
    """
    allc={}
    visited=set()
    for angle in (0,45):
        t=math.radians(angle);B=np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])
        uv=poly@B
        # Along a straight boundary, omitted vertices can be separated by any
        # nonnegative sum of primitive unit and sqrt(2) edge lengths.
        seeds=list(uv)
        for a,b in zip(uv,np.roll(uv,-1,axis=0)):
            delta=b-a;length=np.linalg.norm(delta)
            for i in range(int(length)+1):
                for j in range(int(length/math.sqrt(2))+1):
                    distance=i+j*math.sqrt(2)
                    if 1e-5<distance<length-1e-5:seeds.append(a+delta*distance/length)
        for sx,sy in [(1,1),(1,math.sqrt(2)),(math.sqrt(2),1)]:
            step=np.array([sx,sy]);origins={tuple(np.round(np.mod(p,step),5)) for p in seeds}
            # Floating point modulo 1 at an exact integer must be zero.
            origins={tuple(0 if abs(p[k]-step[k])<1e-4 else p[k] for k in range(2)) for p in origins}
            for o in origins:
                o=np.array(o);lo=np.floor((uv.min(0)-o)/step).astype(int);hi=np.ceil((uv.max(0)-o)/step).astype(int)
                for x in range(lo[0],hi[0]):
                    for y in range(lo[1],hi[1]):
                        base=o+step*[x,y]
                        shapes=[[(0,0),(1,0),(1,1),(0,1)]]
                        if sx==sy==1:shapes += [[(0,0),(1,0),(0,1)],[(0,0),(1,0),(1,1)],[(1,0),(1,1),(0,1)],[(0,0),(1,1),(0,1)]]
                        for sh in shapes:
                            q=(base+step*np.array(sh))@B.T
                            key=tuple(sorted(tuple(np.round(p,4)) for p in q))
                            if key in visited:continue
                            visited.add(key)
                            # Cover both boundary and interior samples: no bridging concavities.
                            samples=np.array([a*(1-z)+b*z for a,b in zip(q,np.roll(q,-1,axis=0)) for z in np.linspace(0,1,9)]+[q.mean(0)])
                            if not inside(samples,poly,1e-4).all():continue
                            enclosed=[];bad=False
                            for gi,g in enumerate(groups):
                                hits=inside(g,q,1e-5)
                                if hits.any():
                                    if not hits.all():bad=True;break
                                    enclosed.append(gi)
                            if bad or len(enclosed)!=(0 if len(q)==3 else 1):continue
                            # A real mark must be separated from the implicit crease, too.
                            if enclosed:
                                g=groups[enclosed[0]]
                                for a,b in zip(q,np.roll(q,-1,axis=0)):
                                    d=b-a
                                    dist=np.abs(d[0]*(g[:,1]-a[1])-d[1]*(g[:,0]-a[0]))/np.linalg.norm(d)
                                    if dist.min()<.065:bad=True;break
                            if bad:continue
                            allc[key]=(q,enclosed)
    return list(allc.values())


def overlap(a,b):
    for p in (a,b):
        for v,w in zip(p,np.roll(p,-1,axis=0)):
            d=w-v;n=np.array([-d[1],d[0]])
            aa=a@n;bb=b@n
            if min(aa.max(),bb.max())-max(aa.min(),bb.min())<1e-4:return False
    return True


def tessellations(poly,cs,cap=10000):
    """Exhaust all nonoverlapping complete covers, independent of character identities.
    Interior witness constraints accelerate search; analytic area and SAT decide coverage.
    """
    qs=[q for q,_ in cs];areas=[abs(P._poly_area(q)) for q in qs]
    target=abs(P._poly_area(poly))
    points=[]
    for q in qs:
        points.append(q.mean(0)+np.array([.006231,.009717]))
    points=np.array(points)
    # Exclude any witness landing on an implicit edge; then coverage is exactly once.
    keep=np.ones(len(points),bool)
    for q in qs:
        for a,b in zip(q,np.roll(q,-1,axis=0)):
            d=b-a;t=((points-a)*d).sum(1)/(d@d)
            dist=np.abs(d[0]*(points[:,1]-a[1])-d[1]*(points[:,0]-a[0]))/np.linalg.norm(d)
            keep&=~((dist<1e-4)&(t>=0)&(t<=1))
    points=points[keep & inside(points,poly)]
    cm=[inside(points,q) for q in qs]
    covers=[sum(1<<int(i) for i in np.flatnonzero(m)) for m in cm]
    if any(not x for x in covers):raise ValueError('candidate has no interior witness')
    owners=[sum(1<<i for i,m in enumerate(cm) if m[j]) for j in range(len(points))]
    bad=[]
    for i,q in enumerate(qs):
        bad.append(sum(1<<j for j,r in enumerate(qs) if overlap(q,r)))
    results=[];seen=set();nodes=0
    def bits(b):
        while b:
            one=b&-b;yield one.bit_length()-1;b-=one
    def dfs(avail,covered,chosen,area):
        nonlocal nodes
        nodes+=1
        if nodes>1000000:raise RuntimeError('tessellation search cap reached')
        if area>target+1e-3:return
        todo=[(mask&avail).bit_count() for j,mask in enumerate(owners) if not covered>>j&1]
        if not todo:
            if abs(area-target)<1e-3:
                key=tuple(sorted(chosen))
                if key not in seen:results.append(key);seen.add(key)
                if len(results)>=cap:raise RuntimeError('tessellation solution cap reached')
            return
        if min(todo)==0:return
        j=min((j for j in range(len(owners)) if not covered>>j&1),key=lambda j:(owners[j]&avail).bit_count())
        for i in bits(owners[j]&avail):dfs(avail&~bad[i],covered|covers[i],chosen+[i],area+areas[i])
    dfs((1<<len(cs))-1,0,[],0)
    return [[qs[i] for i in sol] for sol in results],dict(candidates=len(cs),witnesses=len(points),search_nodes=nodes,tessellations=len(results),area=target)


def recover(gray,box,unit):
    q,origin,info=outline(gray,box,unit)
    groups=[(a-origin)/unit for a in glyph_groups(gray,box)]
    cs=candidates(q,groups)
    sols,search=tessellations(q,cs)
    if not sols:raise ValueError('no complete subdivision of unruled paper')
    fs=[[dict(poly_px=(p*unit+origin).tolist(),panel_id=tuple(box[:4])) for p in sol] for sol in sols]
    return fs,dict(info,**search,marks=len(groups))
