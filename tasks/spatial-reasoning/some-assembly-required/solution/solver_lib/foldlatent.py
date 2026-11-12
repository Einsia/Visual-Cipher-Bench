"""Recover unmarked fold positions as well as angles by finite lattice closure.

Input: planar unit tiles, their adjacency, and allowable angles. No design data.
Enumerates face placements, enforces tree compatibility and reversed boundary
edge support, then exhausts remaining assignments. No first-solution shortcut.
"""
import collections
import math
from foldfast import rot, _sub, _add, _mv, _mm


def fold(faces, links, options, box=None, max_solutions=1024, node_limit=2000000):
    n=len(faces)
    graph=collections.defaultdict(list)
    for k,(a,b,e) in enumerate(links):
        graph[a].append((b,e,k));graph[b].append((a,e,k))
    def tree(r):
        order=[r];seen={r};dist={r:0};edges=[]
        for a in order:
            for b,e,k in graph[a]:
                if b not in seen:
                    seen.add(b);order.append(b);dist[b]=dist[a]+1;edges.append((a,b,e,k))
        return max(dist.values()),sum(dist.values()),order,edges
    roots=[i for i,f in enumerate(faces) if len(f)==4 and abs(math.dist(f[0],f[1])-1)<1e-4 and abs(math.dist(f[1],f[2])-1)<1e-4]
    _,_,order,ordered=min((tree(r) for r in roots),key=lambda x:x[:2])
    root=order[0]
    ox,oy=faces[root][0];dx=faces[root][1][0]-ox;dy=faces[root][1][1]-oy
    ll=math.hypot(dx,dy);c,s=dx/ll,dy/ll
    tr2=lambda p:(c*(p[0]-ox)+s*(p[1]-oy),-s*(p[0]-ox)+c*(p[1]-oy))
    faces=[[tr2(p) for p in f] for f in faces]
    ordered=[(a,b,(tr2(e[0]),tr2(e[1])),k) for a,b,e,k in ordered]
    key=lambda p:tuple(round(v,4) for v in p)
    ekey=lambda a,b:(key(a),key(b))
    joined=collections.defaultdict(set)
    for a,b,e,k in ordered:
        joined[a].add(frozenset((key(e[0]),key(e[1]))));joined[b].add(frozenset((key(e[0]),key(e[1]))))
    free=[]
    for i,f in enumerate(faces):
        free.append([j for j in range(len(f)) if frozenset((key(f[j]),key(f[(j+1)%len(f)]))) not in joined[i]])
    I=((1.,0,0),(0,1.,0),(0,0,1.))
    maps=[[] for _ in faces];polys=[[] for _ in faces];boundary=[[] for _ in faces];centers=[[] for _ in faces]
    boxs=sorted(box) if box else None
    rootp=[key((x,y,0.)) for x,y in faces[root]]
    def add(i,R,t):
        p=[_add(_mv(R,(x,y,0)),t) for x,y in faces[i]]
        if any(abs(v-round(v))>1e-4 for a in p for v in a):return None
        p=tuple(key(a) for a in p)
        if boxs:
            allp=list(p)+rootp
            ext=sorted(max(a[k] for a in allp)-min(a[k] for a in allp) for k in range(3))
            if any(a>b+1e-4 for a,b in zip(ext,boxs)):return None
        return p
    def append(i,R,t,p):
        maps[i].append((R,t));polys[i].append(p)
        boundary[i].append(tuple(ekey(p[j],p[(j+1)%len(p)]) for j in free[i]))
        centers[i].append(key(tuple(sum(c)/len(p) for c in zip(*p))))
    append(root,I,(0.,0.,0.),tuple(rootp))
    supports={}
    for a,b,(A,B),k in ordered:
        A3=(*A,0.);B3=(*B,0.)
        cb=tuple(sum(v)/len(faces[b]) for v in zip(*faces[b]))+(0.,)
        d=_sub(B3,A3);w=_sub(cb,A3);side=1 if d[0]*w[1]-d[1]*w[0]>0 else -1
        candidates=[]
        for ang in options[k]:
            R=rot(tuple(v*side for v in d),-math.radians(180-ang))
            candidates.append((R,_sub(A3,_mv(R,A3))))
        index={};ab=[set() for _ in maps[a]];ba=[]
        for ai,(Ra,ta) in enumerate(maps[a]):
            for Rl,tl in candidates:
                R=_mm(Ra,Rl);t=_add(_mv(Ra,tl),ta);p=add(b,R,t)
                if p is None:continue
                if p not in index:
                    index[p]=len(maps[b]);append(b,R,t,p);ba.append(set())
                bi=index[p];ab[ai].add(bi);ba[bi].add(ai)
        if len(maps[b])>200000:raise RuntimeError('face-domain cap reached; uniqueness unproved')
        supports[a,b]=ab;supports[b,a]=ba
        if not maps[b]:return [],0
    initial=[set(range(len(p))) for p in polys]
    nodes=0;solutions=[]
    def propagate(dom):
        while True:
            before=sum(map(len,dom))
            for (a,b),ss in supports.items():
                dom[a]={i for i in dom[a] if ss[i]&dom[b]}
                if not dom[a]:return False
            active=collections.defaultdict(set)
            for a in range(n):
                for i in dom[a]:
                    for e in boundary[a][i]:active[e].add(a)
            for a in range(n):
                dom[a]={i for i in dom[a] if all(active.get((e[1],e[0]),set())-{a} for e in boundary[a][i])}
                if not dom[a]:return False
            singles={a:centers[a][next(iter(d))] for a,d in enumerate(dom) if len(d)==1}
            for a in range(n):
                occupied={v for b,v in singles.items() if b!=a}
                dom[a]={i for i in dom[a] if centers[a][i] not in occupied}
                if not dom[a]:return False
            if before==sum(map(len,dom)):return True
    def rec(dom):
        nonlocal nodes
        nodes+=1
        if nodes>node_limit or len(solutions)>=max_solutions:raise RuntimeError('closure search cap reached; uniqueness unproved')
        if not propagate(dom):return
        pending=[a for a in range(n) if len(dom[a])>1]
        if pending:
            a=min(pending,key=lambda a:len(dom[a]))
            for i in sorted(dom[a]):
                nxt=[d.copy() for d in dom];nxt[a]={i};rec(nxt)
            return
        ps={a:polys[a][next(iter(dom[a]))] for a in range(n)}
        edges=collections.Counter((p[j],p[(j+1)%len(p)]) for p in ps.values() for j in range(len(p)))
        if any(v!=1 or edges[(b,a)]!=1 for (a,b),v in edges.items()):return
        if boxs:
            pp=[p for f in ps.values() for p in f]
            ext=sorted(max(a[k] for a in pp)-min(a[k] for a in pp) for k in range(3))
            if any(a>b+1e-4 for a,b in zip(ext,boxs)):return
        vol=0.
        for p in ps.values():
            for j in range(1,len(p)-1):
                a,b,c=p[0],p[j],p[j+1]
                vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        if vol>1e-6:solutions.append(ps)
    rec(initial)
    return solutions,nodes
