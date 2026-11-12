"""Pure Pillow/numpy geometry and glyph recognition; no page coordinates."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from .vision import components, normalize

DATA=Path(__file__).resolve().parent

def bands(values):
    a=np.asarray(values,dtype=bool)
    d=np.diff(np.pad(a.astype(np.int8),(1,1)))
    return list(zip(np.flatnonzero(d==1),np.flatnonzero(d==-1)))

def dashed_boxes(m):
    candidates=[]
    for y,row in enumerate(m):
        rr=bands(row); groups=[]; group=[]
        for a,b in rr:
            if b-a>12:
                if group: groups.append(group)
                group=[]; continue
            if group and a-group[-1][1]>9:
                groups.append(group); group=[]
            group.append((a,b))
        if group: groups.append(group)
        for g in groups:
            if len(g)>=9 and g[-1][1]-g[0][0]>100:
                candidates.append((g[0][0],y,g[-1][1]))
    horizontals=[]
    for a,y,b in candidates:
        if any(abs(a-x)<5 and abs(b-z)<5 and abs(y-yy)<4 for x,yy,z in horizontals): continue
        horizontals.append((a,y,b))
    boxes=[]
    for a,y,b in horizontals:
        for c,z,d in horizontals:
            if 45<z-y<160 and abs(a-c)<6 and abs(b-d)<6:
                # A dashed border must also have ink on both vertical sides.
                l=m[y:z+1,max(0,a-3):a+4].any(1).mean()
                r=m[y:z+1,b-4:b+3].any(1).mean()
                if min(l,r)>.45:
                    box=(min(a,c),y,max(b,d),z+1)
                    if not any(sum(abs(t-u) for t,u in zip(box,old))<12 for old in boxes): boxes.append(box)
    return sorted(boxes,key=lambda b:(b[1],b[0]))

def long_lines(m,minimum):
    lines=[]
    for y,row in enumerate(m):
        for a,b in bands(row):
            if b-a>=minimum: lines.append((a,y,b))
    # Multiple pixels of the same stroke become one line.
    result=[]
    for a,y,b in lines:
        if any(abs(a-x)<5 and abs(b-z)<5 and abs(y-yy)<5 for x,yy,z in result): continue
        result.append((a,y,b))
    return result

def frames(m):
    hh=long_lines(m,250); result=[]
    for a,y,b in hh:
        for c,z,d in hh:
            if z-y<100 or abs(a-c)>5 or abs(b-d)>5: continue
            if m[y:z+1,a:a+5].any(1).mean()>.97 and m[y:z+1,b-5:b].any(1).mean()>.97:
                result.append((a,y,b,z+1))
    return result

def crop_component(m,c):
    x,y,r,b=c['bbox']; out=np.zeros((b-y,r-x),bool)
    for yy,a,z in c['runs']: out[yy-y,a-x:z-x]=True
    return out

def canonical(m,size=(40,48)):
    yy,xx=np.where(m)
    if len(xx)==0: return np.zeros(size[::-1],bool)
    m=m[yy.min():yy.max()+1,xx.min():xx.max()+1]
    return np.array(Image.fromarray(np.uint8(m)*255).resize(size,Image.Resampling.BILINEAR))>120

def glyph_templates():
    font=ImageFont.truetype(str(DATA/'DejaVuSans.ttf'),60)
    result={}
    for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?':
        im=Image.new('L',(100,100)); ImageDraw.Draw(im).text((10,5),char,font=font,fill=255)
        result[char]=canonical(np.array(im)>120)
    return result

def read_text(m,box,templates):
    x,y,r,b=box; patch=m[y:b,x:r]
    # Projection joins disconnected dots to their letter.
    chars=[]
    for a,z in bands(patch.any(0)):
        p=patch[:,a:z]; yy=np.flatnonzero(p.any(1))
        if not len(yy): continue
        p=p[yy[0]:yy[-1]+1]
        norm=canonical(p)
        scores=sorted((np.mean(norm!=t),ch) for ch,t in templates.items())
        if scores[0][0]>.30: raise ValueError(f'Unrecognized glyph, mismatch {scores[0][0]:.3f}')
        chars.append(scores[0][1])
    result=''.join(chars)
    return result.replace('I','l') if any(ch.islower() for ch in result) else result

def entities(m,boxes):
    templates=glyph_templates(); entities=[]; remaining=m.copy()
    for b in boxes:
        x,y,r,z=b; inner=(x+8,y+8,r-8,z-8)
        label=read_text(m,inner,templates)
        if label!='?' and not label.isalpha(): raise ValueError('Unreadable box')
        entities.append({'kind':'box','bbox':b,'word':None if label=='?' else label.lower()})
        remaining[max(0,y-2):z+2,max(0,x-2):r+2]=False
    cc=components(remaining)
    # Icons are compact, large connected components. No position is used.
    icons=[]
    for c in cc:
        x,y,r,b=c['bbox']; w=r-x; h=b-y
        if 65<w<190 and 65<h<190 and c['area']>1000:
            icons.append(c)
    for c in icons:
        patch=crop_component(remaining,c)
        choices=[]
        for path in sorted((DATA/'icons').glob('*.png')):
            template=np.array(Image.open(path).convert('L'))<128
            choices.append((np.mean(canonical(patch,(96,96))!=canonical(template,(96,96))),path.stem))
        if not choices: raise ValueError('No generic icon templates installed')
        score,label=min(choices)
        if score>.19: raise ValueError(f'Unrecognized object, mismatch {score:.3f}')
        aliases=json.loads((DATA/'icons'/'labels.json').read_text())
        entities.append({'kind':'icon','bbox':c['bbox'],'word':label,'alternatives':aliases[label]})
        x,y,r,b=c['bbox']; remaining[y:b,x:r]=False
    # Group small components into text lines, then words, without fixed locations.
    cc=components(remaining); glyphs=[]
    for c in cc:
        x,y,r,b=c['bbox']; w=r-x; h=b-y
        if 2<=w<=65 and 2<=h<=65 and c['area']>=4: glyphs.append(c)
    # Baseline overlap clusters separate header text from diagram labels.
    rows=[]
    for c in sorted(glyphs,key=lambda c:c['bbox'][1]):
        x,y,r,b=c['bbox']
        match=None
        for row in rows:
            yy=min(t['bbox'][1] for t in row); bb=max(t['bbox'][3] for t in row)
            if min(bb,b)-max(yy,y)>min(bb-yy,b-y)*.45: match=row; break
        if match is None: rows.append([c])
        else: match.append(c)
    top=min(b[1] for b in boxes)
    for row in rows:
        row.sort(key=lambda c:c['bbox'][0]); groups=[]
        for c in row:
            if not groups or c['bbox'][0]-groups[-1][-1]['bbox'][2]>13: groups.append([c])
            else: groups[-1].append(c)
        for g in groups:
            x=min(c['bbox'][0] for c in g); y=min(c['bbox'][1] for c in g)
            r=max(c['bbox'][2] for c in g); b=max(c['bbox'][3] for c in g)
            if y<top-35 or b-y<16: continue
            try: word=read_text(m,(x,y,r,b),templates)
            except ValueError: continue
            if word=='?' or (word.isalpha() and len(word)>=2):
                entities.append({'kind':'text','bbox':(x,y,r,b),'word':None if word=='?' else word.lower()})
                remaining[y:b,x:r]=False
    return entities,remaining

def erode(m):
    p=np.pad(m,1)
    return np.logical_and.reduce([p[dy:dy+m.shape[0],dx:dx+m.shape[1]] for dy in range(3) for dx in range(3)])

def arrow_seeds(m,top):
    core=erode(erode(m)); core[:max(0,top-60)]=False
    return [c for c in components(core) if 2<=c['area']<=100]

def skeletonize(m):
    """Zhang-Suen thinning, retaining line junctions and endpoints."""
    a=np.pad(m.copy(),1)
    while True:
        changed=False
        for phase in (0,1):
            p=[a[:-2,1:-1],a[:-2,2:],a[1:-1,2:],a[2:,2:],a[2:,1:-1],a[2:,:-2],a[1:-1,:-2],a[:-2,:-2]]
            n=sum(x.astype(np.uint8) for x in p)
            transitions=sum((~p[i]&p[(i+1)%8]).astype(np.uint8) for i in range(8))
            kill=a[1:-1,1:-1]&(n>=2)&(n<=6)&(transitions==1)
            if phase==0: kill&=~(p[0]&p[2]&p[4])&~(p[2]&p[4]&p[6])
            else: kill&=~(p[0]&p[2]&p[6])&~(p[0]&p[4]&p[6])
            if kill.any(): changed=True; a[1:-1,1:-1][kill]=False
        if not changed: break
    return a[1:-1,1:-1]

def shaft_direction(m,center):
    angles=np.arange(0,2*np.pi,np.pi/360)
    vv=np.stack([np.cos(angles),np.sin(angles)],1)
    radii=np.arange(12,42)
    pts=center[None,None,:]+vv[:,None,:]*radii[None,:,None]
    xx=np.rint(pts[:,:,0]).astype(int); yy=np.rint(pts[:,:,1]).astype(int)
    # 3-pixel samples tolerate quantization and subpixel line placement.
    pp=np.pad(m,2)
    scores=np.zeros(xx.shape,float)
    for dy,dx in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]:
        scores=np.maximum(scores,pp[yy+2+dy,xx+2+dx])
    rates=scores.mean(1)
    # Refine using a line's foreground pixels, to avoid angle quantization drift.
    v=vv[np.argmax(rates)]
    xx0,yy0=np.meshgrid(np.arange(int(center[0])-42,int(center[0])+43),np.arange(int(center[1])-42,int(center[1])+43))
    points=np.stack([xx0.ravel(),yy0.ravel()],1)
    delta=points-center
    t=delta@v; s=delta@np.array([-v[1],v[0]])
    good=(t>14)&(t<40)&(abs(s)<3)&m[points[:,1],points[:,0]]
    chosen=points[good]
    if len(chosen)<8: raise ValueError('Arrow shaft cannot be traced')
    cov=np.cov(chosen.T); vals,vecs=np.linalg.eigh(cov); fitted=vecs[:,-1]
    if fitted@v<0: fitted=-fitted
    return fitted

def trace_shaft(skel,center,v,frame_boxes=()):
    """Follow the shaft; continue straight at crossings, turn at real elbows."""
    yy,xx=np.where(skel)
    points=np.stack([xx,yy],1)
    delta=points-center; t=delta@v; s=delta@np.array([-v[1],v[0]])
    choices=np.where((t>12)&(t<48)&(abs(s)<4))[0]
    if not len(choices): raise ValueError('Missing arrow shaft skeleton')
    start=points[choices[np.argmin(abs(t[choices]-20)+abs(s[choices])*2)]]
    # Work at 8-pixel steps, which bypasses small pixel clusters at junctions.
    current=start.astype(float); previous=center; path=[center.copy(),current.copy()]
    visited=set()
    for iteration in range(1000):
        x,y=np.rint(current).astype(int); key=(x,y)
        if key in visited:
            raise ValueError(f'Cyclic line trace {path[-16:]}')
        visited.add(key)
        xmin=max(0,x-25); xmax=min(skel.shape[1],x+26)
        ymin=max(0,y-25); ymax=min(skel.shape[0],y+26)
        by,bx=np.where(skel[ymin:ymax,xmin:xmax]); candidates=np.stack([bx+xmin,by+ymin],1)
        # Stay on the connected stroke: nearby parallel arrows are not junctions.
        available={tuple(p) for p in candidates}
        start_key=tuple(np.rint(current).astype(int)); reachable={start_key}; queue=[start_key]
        while queue:
            qx,qy=queue.pop()
            for ox,oy in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                q=(qx+ox,qy+oy)
                if q in available and q not in reachable: reachable.add(q); queue.append(q)
        connected=np.array([tuple(p) in reachable for p in candidates])
        dd=candidates-current; rr=np.linalg.norm(dd,axis=1)
        direction=current-previous; direction/=np.linalg.norm(direction)
        cosine=(dd@direction)/np.maximum(rr,1)
        bridge=np.zeros(len(candidates),bool)
        for a,b,c,d in frame_boxes:
            near=(a-24<x<c+24 and (abs(y-b)<24 or abs(y-d)<24)) or (b-24<y<d+24 and (abs(x-a)<24 or abs(x-c)<24))
            if near: bridge|=(cosine>.985)&(rr>=8)
        valid=(rr>=6)&(rr<=24)&(cosine>-.15)&(connected|bridge)
        if not valid.any():
            valid=(rr>=1)&(rr<=6)&(cosine>.35)&connected
            if not valid.any(): return current,path
            # Endpoint, return furthest pixel in the continuation direction.
            vv=np.where(valid)[0]; end=candidates[vv[np.argmax(rr[vv])]]
            return end,path+[end]
        ids=np.where(valid)[0]
        chosen=ids[np.argmax(cosine[ids]-.002*abs(rr[ids]-12))]
        previous=current; current=candidates[chosen].astype(float); path.append(current.copy())
    raise ValueError('Line trace too long')

def box_distance(point,box):
    x,y=point; a,b,c,d=box
    return float(np.hypot(max(a-x,0,x-c),max(b-y,0,y-d)))

def arrows(m,entities,frame_boxes,top):
    clean=m.copy()
    for a,b,c,d in frame_boxes:
        clean[max(0,b-2):b+6,a:c]=False
        clean[d-3:d+5,a:c]=False
        clean[b:d,max(0,a-2):a+6]=False
        clean[b:d,c-5:c+3]=False
    sk=skeletonize(clean)
    result=[]
    for c in arrow_seeds(m,top):
        if c['area']<15: continue
        x,y,r,b=c['bbox']; center=np.array([(x+r-1)/2,(y+b-1)/2])
        v=shaft_direction(clean,center)
        tip=center-v*11
        # Thick border/line intersections can survive erosion too. They lack
        # an adjacent destination and must not be mistaken for arrowheads.
        near_border=any((a-5<=center[0]<=c+5 and min(abs(center[1]-b),abs(center[1]-d))<6) or
                        (b-5<=center[1]<=d+5 and min(abs(center[0]-a),abs(center[0]-c))<6)
                        for a,b,c,d in frame_boxes)
        if near_border and min(box_distance(tip,e['bbox']) for e in entities)>45:
            continue
        endpoint,path=trace_shaft(sk,center,v,frame_boxes)
        targets=sorted((box_distance(tip,e['bbox']),i) for i,e in enumerate(entities))
        # A frame-output arrow may end at an unrecognized standalone question mark.
        td,ti=targets[0]
        sources=sorted((box_distance(endpoint,e['bbox']),i) for i,e in enumerate(entities))
        sd,si=sources[0]
        frame_source=None
        for fi,f in enumerate(frame_boxes):
            a,b,c,d=f; ex,ey=endpoint
            if a-5<=ex<=c+5 and abs(ey-d)<15: frame_source=fi
        result.append({'source':si if sd<45 else None,'target':ti if td<45 else None,
                       'frame':frame_source,'tip':tip.tolist(),'end':endpoint.tolist(),
                       'distances':[sd,td],'path':[p.tolist() for p in path]})
    return result
