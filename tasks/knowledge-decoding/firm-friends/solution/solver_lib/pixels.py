"""Pixel observations from the puzzle PNGs.

The vocabulary contains isolated glyphs and pictograms, with no clue ordering,
grid, pairings or answer. Geometry is recovered from line pixels. Coordinates
only delimit the established page regions and nominal grid pitch.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).parent
VOC = json.loads((ROOT/'visual_vocabulary.json').read_text())
NAMES = json.loads((ROOT/'picture_names.json').read_text())

def require(condition, message):
    if not condition:
        raise ValueError(message)

def components(mask):
    seen = np.zeros_like(mask, dtype=bool)
    result = []
    for yy, xx in zip(*np.where(mask)):
        y,x = int(yy),int(xx)
        if seen[y,x]: continue
        todo=[(y,x)]; seen[y,x]=True; points=[]
        while todo:
            y,x=todo.pop(); points.append((y,x))
            for dy,dx in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
                v,u=y+dy,x+dx
                if 0<=v<mask.shape[0] and 0<=u<mask.shape[1] and mask[v,u] and not seen[v,u]:
                    seen[v,u]=True; todo.append((v,u))
        ys,xs=zip(*points)
        result.append((min(xs),min(ys),max(xs)+1,max(ys)+1,len(points)))
    return result

def tight(mask):
    ys,xs=np.where(mask)
    require(len(xs)>0,'Missing glyph or pictogram')
    box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    return mask[box[1]:box[3],box[0]:box[2]],box

def recognize(mask, vocabulary):
    m,_=tight(mask); scores=[]
    for name,v in vocabulary.items():
        # Normalize bounding-box antialiasing differences only, not semantic size.
        if abs(m.shape[0]-v['height'])>1 or abs(m.shape[1]-v['width'])>1: continue
        t=np.zeros((v['height'],v['width']),bool)
        for x,y in v['dark']: t[y,x]=True
        z=np.array(Image.fromarray(m).resize((v['width'],v['height']),Image.Resampling.NEAREST))
        score=np.logical_xor(z,t).sum()/max(1,np.logical_or(z,t).sum())
        scores.append((float(score),name))
    require(bool(scores),'Unrecognized glyph/pictogram dimensions')
    score,name=min(scores)
    limit=0.28 if vocabulary is VOC['digits'] else (0.05 if vocabulary is VOC['arrows'] else (0.08 if vocabulary is VOC.get('words') else 0.0001))
    require(score<=limit,f'Unrecognized or damaged glyph/pictogram: {name}, error={score:.4f}')
    return name

def label(a,box):
    x,y,r,b=box; mask=a[y:b,x:r]<128
    cc=sorted(components(mask),key=lambda q:q[0]); chars=[]; direction=None
    for l,t,rr,bb,area in cc:
        if area<4: continue
        v=mask[t:bb,l:rr]
        if rr-l>25 or bb-t>25:
            require(direction is None,'Multiple direction marks in one entry label')
            direction=recognize(v,VOC['arrows'])
        else: chars.append(recognize(v,VOC['digits']))
    require(chars and direction,'Incomplete number/direction label')
    return int(''.join(chars)),direction

def segment(a,p,q,threshold=190,radius=2):
    x0,y0=p;x1,y1=q
    n=max(abs(x1-x0),abs(y1-y0))+1
    xs=np.rint(np.linspace(x0,x1,n)).astype(int)
    ys=np.rint(np.linspace(y0,y1,n)).astype(int)
    mask=np.zeros_like(a,dtype=bool)
    for x,y in zip(xs,ys):
        mask[max(0,y-radius):y+radius+1,max(0,x-radius):x+radius+1]=True
    ink=(a<threshold)&mask
    # A connected path in a narrow corridor, not just nearby dots at each step.
    start={(int(y),int(x)) for y,x in zip(*np.where(ink[max(0,y0-radius):y0+radius+1,max(0,x0-radius):x0+radius+1]))}
    todo=[(y+max(0,y0-radius),x+max(0,x0-radius)) for y,x in start];seen=set(todo)
    while todo:
        y,x=todo.pop()
        if abs(x-x1)<=radius and abs(y-y1)<=radius:return True
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)):
            v,u=y+dy,x+dx
            if 0<=v<a.shape[0] and 0<=u<a.shape[1] and ink[v,u] and (v,u) not in seen:
                seen.add((v,u));todo.append((v,u))
    return False

def grid(a):
    from geometry import derive,cells
    ox,oy,pitch=345,940,100
    edges={}
    for orientation in ['h','v']:
        for row in range(8 if orientation=='h' else 7):
            for col in range(10 if orientation=='h' else 11):
                x,y=ox+pitch*col,oy+pitch*row
                if orientation=='h':profile=a[y-2:y+3,x+4:x+97].min(axis=0)
                else:profile=a[y+4:y+97,x-2:x+3].min(axis=1)
                coverage=(profile<190).mean()
                require(coverage==0 or coverage==1,f'Broken boundary {orientation} {col},{row}')
                edges[orientation,col,row]=0 if coverage==0 else (2 if np.median(profile)<70 else 1)
    # Intact vertical boundaries delimit the silhouette even where horizontal
    # boundaries are not drawn.
    occupied={(x,y) for y in range(7) for x in range(10) if edges['v',x,y] and edges['v',x+1,y]}
    grey=[]
    for x,y in sorted(occupied):
        inner=a[oy+100*y+8:oy+100*y+93,ox+100*x+8:ox+100*x+93]
        require(not (inner<128).any(),'Unexpected letter/label in main grid')
        if (inner>=210).all() and (inner<=225).all():grey.append((x,y))
        for yy in (y,y+1):
            if (x,yy-1) not in occupied or (x,yy) not in occupied:
                require(edges['h',x,yy]==2,'Broken exterior silhouette')
    grey.sort()
    require(grey and len({y for x,y in grey})==1,'Missing/ambiguous shaded target')
    require(grey==[(grey[0][0]+k,grey[0][1]) for k in range(len(grey))],'Noncontiguous target')
    target={'x':grey[0][0],'y':grey[0][1],'dx':1,'dy':0,'length':len(grey)}
    entries=derive(occupied,edges,target)
    residual=a[oy:oy+700,ox:ox+1000].copy()
    for col,row in occupied:residual[row*100+3:row*100+97,col*100+3:col*100+97]=255
    for k in range(11):residual[:,max(0,k*100-3):k*100+4]=255
    for k in range(8):residual[max(0,k*100-3):k*100+4,:]=255
    require(not (residual<190).any(),'Extra marks outside grid silhouette')
    observed={k:v for k,v in edges.items() if v or (k[0]=='h' and (k[1],k[2]) in occupied and (k[1],k[2]-1) in occupied)}
    return entries,target,observed,sorted(occupied)

def bank(a):
    import math
    result=[];observations=[];covered=np.zeros_like(a,dtype=bool)
    vocab=json.loads((ROOT/'spatial_rule_vocabulary.json').read_text())
    rule=recognize(a[325:375,140:1630]<128,vocab)
    covered[325:375,140:1630]=True
    for index in range(12):
        angle=math.radians(-90+30*index)
        ix,iy=round(850+650*math.cos(angle)),round(1180+700*math.sin(angle))
        cx,cy=round(850+440*math.cos(angle)),round(1180+480*math.sin(angle))
        top=max(380,iy-128)
        icon=a[top:iy+82,ix-120:ix+120]<128
        name=recognize(icon,VOC['icons'])
        covered[top:iy+82,ix-120:ix+120]=True
        if name in ['fall','rye']:
            region=a[iy+97:iy+142,ix-60:ix+50]<128
            require(recognize(region,VOC['words']).lower()==name,'Changed written disambiguator')
            covered[iy+97:iy+142,ix-60:ix+50]=True
        ring=a[cy-16:cy+17,cx-16:cx+17]<128
        _,box=tight(ring)
        # Recover the actual centre from ring pixels, not from picture identity.
        px=cx-16+round((box[0]+box[2])/2);py=cy-16+round((box[1]+box[3])/2)
        yy,xx=np.indices(ring.shape);rr=np.hypot(xx-(px-cx+16),yy-(py-cy+16))
        require((ring&(rr>=10)&(rr<=14)).sum()>=150 and not ring[rr<9].any(),'Malformed pairing circle')
        covered[cy-16:cy+17,cx-16:cx+17]=True
        result.append({'picture':name,'names':NAMES[name],'direction':'unknown','circle':[px,py]})
        observations.append({'picture':name,'circle':[px,py],'direction_label':None,'icon_region_index':index})
    require(not ((a[300:2100]<128)&~covered[300:2100]).any(),'Extra or leaked marks in spatial bank')
    return result,{'pictures':observations,'rule':rule,'direction_labels':0}

def example(a):
    from engine import load_dictionary,onset_swap
    # Read only the example image pair and its grid. No split-word labels.
    sources=[]
    for box in [(270,575,385,670),(645,580,765,675)]:
        x,y,r,b=box;sources.append(recognize(a[y:b,x:r]<128,VOC['icons']))
    # Read the example silhouette, grey continuations and actual given cells.
    occupied=set(); edges={}; given={}; ox,oy=1050,420
    for axis in ['h','v']:
        for y in range(5 if axis=='h' else 4):
            for x in range(3 if axis=='h' else 4):
                xx,yy=ox+x*100,oy+y*100
                profile=(a[yy-2:yy+3,xx+4:xx+97].min(axis=0) if axis=='h'
                         else a[yy+4:yy+97,xx-2:xx+3].min(axis=1))
                coverage=(profile<190).mean()
                require(coverage in (0,1),'Broken example boundary')
                edges[axis,x,y]=0 if not coverage else (2 if np.median(profile)<70 else 1)
    for y in range(4):
        for x in range(3):
            if edges['v',x,y] and edges['v',x+1,y]:
                occupied.add((x,y)); xx,yy=ox+100*x,oy+100*y
                ink=a[yy+8:yy+93,xx+8:xx+93]<128
                if ink.any():given[x,y]=recognize(ink,VOC['words'])
    slots=[]; paths=[]
    for axis,dx,dy in [('v',1,0),('h',0,1)]:
        runs=[]
        for x,y in sorted(occupied):
            if edges[axis,x,y]!=2:continue
            run=[(x,y)]
            while edges.get((axis,run[-1][0]+dx,run[-1][1]+dy))==1:
                run.append((run[-1][0]+dx,run[-1][1]+dy))
            if len(run)>1:runs.append(run)
        require(len(runs)==1,'Example requires one across and one down word')
        run=runs[0]; paths.append(run)
        slots.append({'length':len(run),'given':{str(i):given[p] for i,p in enumerate(run) if p in given}})
    common=set(paths[0])&set(paths[1]);require(len(common)==1,'Ambiguous example crossing')
    shared=next(iter(common)); ex={'inputs':sources,'slots':slots,'crossing':[path.index(shared) for path in paths]}
    from example_rules import infer
    inference=infer(ex,ROOT/'cmudict.dict')
    require(inference['rules']==['exchange_first_sounds'],'Incomplete example does not isolate the sound rule')
    require(len(inference['candidates'])==1,'Incomplete example has ambiguous completion')
    directions=[]
    for box in [(265,495,355,535),(645,495,720,535)]:
        x,y,r,b=box;directions.append(recognize(a[y:b,x:r]<128,VOC['arrows']))
    require(directions==['right','down'],'Example source directions do not match output slots')
    example_cells={(0,3),(1,3),(2,3),(2,2),(2,1),(2,0)}
    for cx,cy in example_cells:
        x,y=1050+100*cx,420+100*cy
        for p,q in [((x+4,y),(x+96,y)),((x+4,y+100),(x+96,y+100)),((x,y+4),(x,y+96)),((x+100,y+4),(x+100,y+96))]:
            require(segment(a,p,q),'Broken example grid edge')
    for cx,cy,r in [(320,550,12),(700,550,12)]:
        for theta in np.linspace(0,2*np.pi,240):
            x=round(cx+r*np.cos(theta));y=round(cy+r*np.sin(theta))
            require((a[y-1:y+2,x-1:x+2]<190).any(),'Incomplete example pairing circle')
    require(segment(a,(333,550),(687,550)),'Missing example pairing connection')
    require(not (a[700:850,200:810]<128).any(),'Unexpected explicit exchange diagram')
    require(recognize(a[1270:1308,240:270]<128,VOC['words'])=='?','Missing extraction question mark')
    require(segment(a,(300,1290),(326,1290)),'Missing output direction connection')
    require(recognize(a[1283:1297,316:331]<200,VOC['heads'])=='extract','Missing extraction arrowhead')
    return {'sources':sources,'directions':directions,'observed':ex,'inference':inference,'given_cells':[[*p,ch] for p,ch in sorted(given.items())],'segmentation_diagram':False}

def parse(directory):
    paths=sorted(Path(directory).glob('*.png'));require(len(paths)==2,'Expected two puzzle pages')
    arrays=[]
    for p in paths:
        im=Image.open(p);require(im.mode in ('RGB','RGBA') and im.size==(1700,2193),'Unexpected image geometry/mode')
        arrays.append(np.array(im.convert('L')))
    a,b=arrays;worked=example(a)
    rules=json.loads((ROOT/'rule_vocabulary.json').read_text())
    for i,(name,v) in enumerate(rules.items()):
        y=1750+45*i
        require(recognize(a[y-30:y+7,335:1650]<128,{name:v})==name,'Missing reconstruction rule')
    worked['reconstruction_rules']=list(rules)
    entries,target,edges,occupied=grid(a);sources,observations=bank(b)
    require(len(entries)==len(sources),'Number of spatially recovered slots differs from number of pictures')
    for direction,dx in [('right',1),('down',0)]:
        require(sum(e['direction']==direction for e in entries)>=sum(s['direction']==direction for s in sources),'Too many observed direction labels')
    # Canonical ordering affects only deterministic search, never source assignment.
    sources.sort(key=lambda s:s['picture'])
    return {'noncrossing_pairs':True,'entries':entries,'sources':sources,'answer_entry':target,'occupied':occupied,'edges':[[*k,v] for k,v in sorted(edges.items())]}, {'pictures':observations,'grid_entries':entries,'target':target,'example':worked,'source_to_slot_mapping':'unknown; jointly searched from scratch','grid_recovery':'intact vertical boundaries; all compatible down endpoints jointly searched','missing_horizontal_edges':[list(k[1:]) for k,v in edges.items() if k[0]=='h' and v==0]}
