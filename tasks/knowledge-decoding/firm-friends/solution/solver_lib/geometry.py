"""Derive variable-length word domains from observed lines, never intended slots."""

def cells(e):
    return [(e['x']+k*e['dx'],e['y']+k*e['dy']) for k in range(e['length'])]

def derive(occupied,edges,target):
    occupied=set(map(tuple,occupied));tc=set(cells(target));across=[]
    # Vertical separators are intact: their grey runs are the across entries.
    for x,y in sorted(occupied,key=lambda p:(p[1],p[0])):
        if edges.get(('v',x,y))!=2:continue
        run=[(x,y)];xx=x
        while edges.get(('v',xx+1,y))==1:
            xx+=1
            if (xx,y) not in occupied:raise ValueError('Across entry exits silhouette')
            run.append((xx,y))
        if len(run)>1 and set(run)!=tc:
            across.append(dict(x=x,y=y,dx=1,dy=0,length=len(run)))
    # Every grey target cell needs a down entry: the target is not a picture word.
    # The across runs are mandatory (visible grey continuations). With one source
    # per word, their count plus the target width exhausts the source inventory.
    ac={p for e in across for p in cells(e)}
    cols=sorted({x for x,y in tc})
    entries=[{'id':i,'direction':'right','variants':[e]} for i,e in enumerate(across)]
    required=occupied-ac
    if any(x not in cols for x,y in required):raise ValueError('Uncoverable cells outside target columns')
    for x in cols:
        ys=sorted(y for xx,y in occupied if xx==x)
        req={p for p in required if p[0]==x}|{p for p in tc if p[0]==x}
        continued=[y for (axis,xx,y),kind in edges.items() if axis=='h' and xx==x and kind==1]
        variants=[]
        for a in ys:
            for b in ys:
                if b<=a:continue
                run={(x,y) for y in range(a,b+1)}
                if not run<=occupied or not req<=run:continue
                if any(edges.get(('h',x,y))==2 for y in range(a+1,b+1)):continue
                if any(not a<y<=b for y in continued):continue
                variants.append(dict(x=x,y=a,dx=0,dy=1,length=b-a+1))
        if not variants:raise ValueError('No possible down segment for column '+str(x))
        entries.append({'id':len(entries),'direction':'down','variants':variants})
    return entries

def restore(entries,occupied):
    """Reconstruct every internal horizontal stop/continuation from a filling."""
    occupied=set(map(tuple,occupied));linked=set()
    for e in entries:
        if e['dy']:
            linked.update((e['x'],y) for y in range(e['y']+1,e['y']+e['length']))
    return [[x,y,1 if (x,y) in linked else 2] for x,y in sorted(occupied) if (x,y-1) in occupied]


def segments_conflict(a,b,c,d):
    """Closed straight segments intersect; input endpoints are pixel coordinates."""
    def orient(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    def on(p,q,r):return min(p[0],q[0])<=r[0]<=max(p[0],q[0]) and min(p[1],q[1])<=r[1]<=max(p[1],q[1])
    u,v,w,z=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    if u*v<0 and w*z<0:return True
    return (u==0 and on(a,b,c)) or (v==0 and on(a,b,d)) or (w==0 and on(c,d,a)) or (z==0 and on(c,d,b))

def pair_conflict(m,o,p):
    if not m.get('noncrossing_pairs'):return False
    if {o['source_i'],o['source_j']}&{p['source_i'],p['source_j']}:return True
    return segments_conflict(*(m['sources'][q[k]]['circle'] for q in (o,p) for k in ('source_i','source_j')))

def noncrossing_matchings(sources):
    """Enumerate every perfect straight-segment matching from observed points.

    No pair names, orientations, circular order or intended solution is assumed.
    This works for any distinct arrangement; on this convex twelve-point bank
    it derives 132 alternatives, which are all searched.
    """
    points=[s['circle'] for s in sources];out=[]
    def visit(left,chosen):
        if not left:out.append(tuple(chosen));return
        a=min(left)
        for b in sorted(left-{a}):
            if any(segments_conflict(points[a],points[b],points[c],points[d]) for c,d in chosen):continue
            visit(left-{a,b},chosen+[(a,b)])
    visit(set(range(len(points))),[])
    return out
