"""Pixel readers. No puzzle transcription or answer is stored here.

Coordinates describe typography/lanes, not the values in them. All labels,
letters, roots, directions, walls and demonstrated regions are recovered.
"""
from pathlib import Path
from collections import deque
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).parent

def components(a):
    a=a.copy(); out=[]
    for y,x in zip(*np.where(a)):
        if not a[y,x]: continue
        todo=[(int(y),int(x))];a[y,x]=False; pts=[]
        while todo:
            yy,xx=todo.pop();pts.append((yy,xx))
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<a.shape[0] and 0<=nx<a.shape[1] and a[ny,nx]:
                        a[ny,nx]=False;todo.append((ny,nx))
        out.append(np.array(pts))
    return out

def bbox(a):
    yy,xx=np.where(a)
    if not len(xx): raise ValueError('Missing glyph or graphic')
    return [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]

def trim(a):
    x,y,r,b=bbox(a);return a[y:b,x:r]

def dilate(a):
    p=np.pad(a,1);r=np.zeros_like(a)
    for y in range(3):
        for x in range(3):r|=p[y:y+a.shape[0],x:x+a.shape[1]]
    return r

class Reader:
    def __init__(self,path):
        self.image=Image.open(path).convert('RGB')
        if self.image.size!=(1700,2193):raise ValueError('Unexpected page dimensions')
        rgb=np.array(self.image)
        if np.any(rgb.max(2)-rgb.min(2)>2):raise ValueError('Unexpected colored pixels')
        self.gray=rgb[:,:,0];self.ink=self.gray<128
        self.cover=np.zeros(self.gray.shape,bool)
        self.texts=[];self.graphics=[];self.fonts={};self.templates={}
    def roi(self,box,threshold=128,mark=True):
        x,y,r,b=map(int,box)
        if mark:self.cover[y:b,x:r]=True
        return self.gray[y:b,x:r]<threshold
    def text(self,box,alphabet,mono=False,role='clue',expected=None):
        a=self.roi(box);bb=bbox(a);s=trim(a)
        # Split along empty columns; decimal digits and uppercase data are unjoined.
        cols=np.any(s,axis=0);runs=[];start=None
        for x,v in enumerate(list(cols)+[False]):
            if v and start is None:start=x
            if not v and start is not None:runs.append((start,x));start=None
        result=''; heights=[];cap_heights=[]
        for x,r in runs:
            z=trim(s[:,x:r]); best=(1e9,None)
            for ch in alphabet:
                key=(ch,mono)
                if key not in self.templates:
                    fkey=mono
                    if fkey not in self.fonts:self.fonts[fkey]=ImageFont.truetype(str(HERE/('DejaVuSansMono.ttf' if mono else 'DejaVuSans.ttf')),136,layout_engine=ImageFont.Layout.BASIC)
                    im=Image.new('L',(240,240),255);ImageDraw.Draw(im).text((20,0),ch,font=self.fonts[fkey],fill=0)
                    self.templates[key]=trim(np.array(im)<128)
                t=self.templates[key]
                aspect=abs(z.shape[1]/z.shape[0]-t.shape[1]/t.shape[0])
                norm=np.array(Image.fromarray(t).resize((z.shape[1],z.shape[0]),Image.Resampling.NEAREST))
                score=np.logical_xor(z,norm).sum()/max(z.sum(),norm.sum())+aspect
                if score<best[0]:best=(score,ch)
            if best[0]>.38:raise ValueError(f'Unreadable glyph at {box}: {best}')
            result+=best[1];heights.append(z.shape[0])
            if best[1].isdigit() or best[1].isupper():cap_heights.append(z.shape[0])
        if expected is not None and result.lower()!=expected.lower():raise ValueError(f'Text mismatch {box}: {result} vs {expected}')
        if expected is not None:
            cap_heights=[h for ch,h in zip(expected,heights) if ch.isupper() or ch.isdigit()]
        actual=[box[0]+bb[0],box[1]+bb[1],box[0]+bb[2],box[1]+bb[3]]
        self.texts.append(dict(role=role,text=result,box=actual,min_glyph_height_px=min(cap_heights or heights)))
        return result
    def graphic(self,box,draw,name,threshold=128):
        x,y,r,b=box;a=self.roi(box,threshold)
        scale=4;im=Image.new('L',((r-x)*scale,(b-y)*scale),255)
        d=ImageDraw.Draw(im)
        def point(p):return ((p[0]-x)*scale,(p[1]-y)*scale)
        draw(d,point,scale)
        t=np.array(im.resize((r-x,b-y),Image.Resampling.LANCZOS))<128
        missing=t&~dilate(a);extra=a&~dilate(t)
        if missing.sum()>max(4,t.sum()*.012) or extra.sum()>max(4,a.sum()*.012):
            raise ValueError(f'Malformed {name} at {box}; missing {missing.sum()}, extra {extra.sum()}')
        self.graphics.append(dict(name=name,box=box))
    def line(self,p,q,width=2.5,threshold=128):
        x,y=p;r,b=q;pad=4
        box=[int(min(x,r)-pad),int(min(y,b)-pad),int(max(x,r)+pad+1),int(max(y,b)+pad+1)]
        def draw(d,pt,s):d.line([pt(p),pt(q)],fill=0,width=round(width*s))
        # At endpoints lines may meet other graphics: continuity is tested on the shaft.
        a=self.roi(box,threshold)
        if x==r:
            shaft=a[pad:-pad,pad-1:pad+2]
            if not np.all(np.any(shaft,axis=1)):raise ValueError(f'Broken vertical line {p,q}')
        elif y==b:
            shaft=a[pad-1:pad+2,pad:-pad]
            if not np.all(np.any(shaft,axis=0)):raise ValueError(f'Broken horizontal line {p,q}')
        else:raise ValueError('Nonaxis line')
        self.graphics.append(dict(name='continuous line',box=box))
    def ring(self,c,r):
        x,y=c;box=[int(x-r-3),int(y-r-3),int(x+r+4),int(y+r+4)]
        a=self.roi(box,mark=False);yy,xx=np.indices(a.shape)
        rad=np.hypot(xx+box[0]-x,yy+box[1]-y)
        # Require a complete ring, not merely dark digits at its center.
        for angle in np.linspace(0,2*math.pi,180,endpoint=False):
            px=x+r*math.cos(angle)-box[0];py=y+r*math.sin(angle)-box[1]
            close=(xx-px)**2+(yy-py)**2<=4
            if not np.any(a&close):raise ValueError(f'Broken/missing ring at {c}')
        ann=(rad>=r-2)&(rad<=r+2)
        self.cover[box[1]:box[3],box[0]:box[2]]|=ann
        return box
    def badge(self,c,required=True,radii=(20,23,24,28,30,26)):
        x,y=c
        small=self.roi([x-17,y-14,x+18,y+14],mark=False)
        if not small.any():
            if required:raise ValueError(f'Missing badge at {c}')
            return None
        # Ring radius is measured independently of the number.
        found=[]
        for r in radii:
            scores=[]
            for t in np.linspace(0,2*math.pi,180,endpoint=False):
                px=int(round(x+r*math.cos(t)));py=int(round(y+r*math.sin(t)))
                scores.append(self.ink[py,px])
            if np.mean(scores)>.9:found.append(r)
        if not found:raise ValueError(f'No complete badge outline at {c}')
        half=10 if min(found)==20 else 18
        num=int(self.text([x-half,y-12,x+half+1,y+12],'0123456789',role='label'))
        for r in found:self.ring(c,r)
        if len(found)>2:raise ValueError('Too many badge rings')
        return num,len(found)==2
    def arrow(self,box):
        a=self.roi(box);cs=components(a)
        if len(cs)!=1:raise ValueError(f'Broken/extra arrow at {box}, components={len(cs)}')
        z=trim(a);h,w=z.shape
        if min(h,w)>max(h,w)*.65 and max(h,w)>14:raise ValueError(f'Not an axis arrow {box}')
        horizontal=w>h
        counts=z.sum(axis=0 if horizontal else 1)
        scores=[]
        for sign in (-1,1):
            distance=(np.arange(len(counts)) if sign<0 else np.arange(len(counts))[::-1])-.5
            ideal=np.maximum(2.5,np.where((distance>=0)&(distance<=10.3),2*math.tan(.42)*distance,0))
            scores.append((float(((counts-ideal)**2).mean()),sign))
        score,sign=min(scores)
        if len(counts)<14:
            sign=1 if np.argmax(counts)<len(counts)/2 else -1
            score=0 if counts.max()>=5 and counts.min()<=3 else 100
        direction=('right' if sign>0 else 'left') if horizontal else ('down' if sign>0 else 'up')
        if counts.max()<5 or counts.min()<1 or score>8:raise ValueError(f'Incomplete arrow {box}: {score}')
        self.graphics.append(dict(name='arrow '+direction,box=box))
        return direction
    def grid(self,x,y,c,w,h,solved=False,small=False):
        # Read every possible separator, including unexpected added separators.
        walls=[]
        for orient in ('v','h'):
            for r in range(h if orient=='v' else h+1):
                for col in range(w+1 if orient=='v' else w):
                    xx=x+col*c;yy=y+r*c
                    if orient=='v':box=[xx-2,yy+4,xx+3,yy+c-3];axis=1
                    else:box=[xx+4,yy-2,xx+c-3,yy+3];axis=0
                    a=self.roi(box,threshold=60);occupied=np.any(a,axis=axis)
                    if occupied.mean()>.95:
                        if not np.all(np.any(self.roi(box),axis=axis)):raise ValueError(f'Broken heavy boundary {box}')
                        heavy=True
                    elif occupied.mean()<.06:heavy=False
                    else:raise ValueError(f'Partial boundary {box}')
                    # Complete fine grid also required at all edges.
                    gray=self.roi(box,threshold=210)
                    if not np.all(np.any(gray,axis=axis)):raise ValueError(f'Missing grid edge {box}')
                    if orient=='v' and 0<col<w and heavy:walls.append([r*w+col-1,r*w+col])
                    if orient=='h' and 0<r<h and heavy:walls.append([(r-1)*w+col,r*w+col])
                    if (orient=='v' and col in (0,w) or orient=='h' and r in (0,h)) and not heavy:raise ValueError('Missing outer boundary')
        for r in range(h+1):
            for col in range(w+1):self.cover[y+r*c-4:y+r*c+5,x+col*c-4:x+col*c+5]=True
        letters=[];roots=[]
        for r in range(h):
            for col in range(w):
                xx=x+col*c;yy=y+r*c
                bottom=12 if small or solved else 20
                field=[xx+c-44,yy+c-bottom-28,xx+c-10,yy+c-bottom+6]
                if solved:
                    letters.append(self.text(field,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',True))
                    if len(letters[-1])!=1:raise ValueError('Extra glyph in a grid letter field')
                elif self.roi(field).any():
                    raise ValueError('Unsolved cells must not reveal letters')
                bx=xx+(36 if small else 43 if solved else 50);by=yy+(34 if small else 38 if solved else 40)
                # Solved diagram's left-bottom badge was shifted within its cell.
                if solved:
                    candidates=[]
                    for off in (0,16):
                        sample=self.ink[by-11:by+11,bx+off-9:bx+off+9]
                        if sample.sum()>45:candidates.append(off)
                    if candidates:
                        off=max(candidates,key=lambda o:self.ink[by-11:by+11,bx+o-9:bx+o+9].sum());bx+=off
                b=self.badge((bx,by),required=False)
                if b:
                    ident,double=b
                    if solved:di=None
                    else:
                        a,off,span=(18,18,8) if small else (27,29,15)
                        mx=xx+a;my=yy+c-off
                        di=self.arrow([mx-span-4,my-span-4,mx+span+5,my+span+5])
                    roots.append((ident,r*w+col,di,double,(bx,by)))
        roots.sort()
        ids=[a[0] for a in roots]
        if len(ids)!=len(set(ids)) or ids!=list(range(1,len(ids)+1)):raise ValueError('Duplicate/missing region identities')
        start=[i for i,a in enumerate(roots) if a[3]]
        if len(start)!=1:raise ValueError('Need exactly one double-ring starting badge')
        ds={'right':1,'left':-1,'up':-w,'down':w}
        return dict(width=w,height=h,letters=letters,seeds=[a[1] for a in roots],ids=ids,directions=[ds.get(a[2]) for a in roots],walls=walls,start=start[0],badge_centers=[a[4] for a in roots])

    def remaining(self,box):
        x,y,r,b=box;unexplained=self.ink[y:b,x:r]&~self.cover[y:b,x:r]
        n=int(unexplained.sum())
        if n>4:
            bb=bbox(unexplained)
            raise ValueError(f'Unrecognized/extra ink ({n} pixels) at {[x+bb[0],y+bb[1],x+bb[2],y+bb[3]]}')

def read_grids(path):
    p=Reader(path)
    main=p.grid(478,1260,124,6,6)
    p.remaining([474,1256,1227,2009])
    inp=p.grid(136,392,96,4,3,small=True)
    p.remaining([132,388,525,685])
    for g,bx,by,step,count in ((inp,230,735,24,12),(main,360,2060,28,36)):
        g.pop('letters')
        g['letter_bank']=[p.text([bx+i*step-12,by-28,bx+i*step+13,by+5], 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',True,role='unallocated letter') for i in range(count)]
        if any(len(ch)!=1 for ch in g['letter_bank']):raise ValueError('Bank must contain one glyph per position')
    return p,main,inp

def regions_from_grid(g):
    w=g['width'];h=g['height'];walls={frozenset(e) for e in g['walls']};seen=set();regions=[]
    for root in g['seeds']:
        todo=[root];region={root}
        while todo:
            v=todo.pop()
            for u in range(w*h):
                if abs(u//w-v//w)+abs(u%w-v%w)==1 and frozenset((u,v)) not in walls and u not in region:
                    region.add(u);todo.append(u)
        if seen&region:raise ValueError('Multiple arrows in an example region')
        seen|=region;regions.append(sorted(region))
    if len(seen)!=w*h:raise ValueError('Example cells without an arrow region')
    return regions

def silhouette(p,c):
    x,y=c;box=[x-28,y-28,x+29,y+29]
    a=p.roi(box,threshold=210)
    cs=components(~a);inside=[]
    for pts in cs:
        if any((pts[:,0]==0)|(pts[:,0]==56)|(pts[:,1]==0)|(pts[:,1]==56)):continue
        if not 350<=len(pts)<=550:raise ValueError(f'Bad silhouette cell {c}')
        inside.append((float(pts[:,1].mean()),float(pts[:,0].mean())))
    if not inside:raise ValueError('Missing area silhouette')
    left=min(a for a,b in inside);top=min(b for a,b in inside)
    coords=sorted((round((a-left)/24),round((b-top)/24)) for a,b in inside)
    # All lines, including boundaries and internal cell edges, must belong to the counted cells.
    scale=4;im=Image.new('L',(57*scale,57*scale),255);d=ImageDraw.Draw(im)
    for a,b in inside:d.rectangle(((a-12)*scale,(b-12)*scale,(a+12)*scale,(b+12)*scale),outline=0,width=6)
    t=np.array(im.resize((57,57),Image.Resampling.LANCZOS))<210
    missing=t&~dilate(dilate(p.roi(box,threshold=210)));extra=p.roi(box,threshold=210)&~dilate(dilate(t))
    if missing.sum()>3 or extra.sum()>3:raise ValueError(f'Broken/extra silhouette at {c}')
    return coords

def normalized_shape(cells,w):
    left=min(v%w for v in cells);top=min(v//w for v in cells)
    return sorted((v%w-left,v//w-top) for v in cells)

def read_example(p,inp):
    from model import solve_cover,describe
    solved=p.grid(606,350,124,4,3,solved=True)
    for key in ('seeds','ids','start'):
        if solved[key]!=inp[key]:raise ValueError(f'Input and completed example disagree: {key}')
    if not {tuple(e) for e in inp['walls']}<={tuple(e) for e in solved['walls']}:raise ValueError('Given wall lost in completion')
    regions=regions_from_grid(solved);areas=list(map(len,regions));rows=[]
    from inference import infer_letter_order
    allocation=infer_letter_order(inp['ids'],regions,inp['width'],inp['letter_bank'],solved['letters'])
    from model import place_letters
    inp['letters']=place_letters(inp,regions)
    if inp['letters']!=solved['letters']:raise ValueError('Bank disagrees with spatially completed example')
    # Read the surviving data. Neither receiver nor lookup ID is printed.
    for yy in (844,930,1016,1102):
        source,root=p.badge((350,yy))
        lshape=silhouette(p,(705,yy))
        equation=p.text([976,yy-18,1120,yy+24],'0123456789|-=',True)
        if source not in inp['ids']:raise ValueError('Unknown example source')
        i=inp['ids'].index(source)
        matches=[k for k,R in enumerate(regions) if normalized_shape(R,4)==lshape]
        if len(matches)!=1:raise ValueError('Silhouette does not identify exactly one oriented region')
        k=matches[0];lookup=inp['ids'][k];lcount=len(lshape)
        # Find the arrival ring on the printed ray, independently of arithmetic.
        v=inp['seeds'][i];di=inp['directions'][i];w=inp['width']
        dr,dc={1:(0,1),-1:(0,-1),w:(1,0),-w:(-1,0)}[di]
        arrivals=[]
        for steps in range(1,max(w,inp['height'])):
            rr=v//w+dr*steps;cc=v%w+dc*steps
            if not (0<=rr<inp['height'] and 0<=cc<w):break
            cx=606+cc*124+18;cy=350+rr*124+78
            # A complete small ring, not just a shaft intersection.
            hits=[]
            for theta in np.linspace(0,2*math.pi,72,endpoint=False):
                px=cx+6*math.cos(theta);py=cy+6*math.sin(theta)
                hits.append(p.ink[round(py),round(px)])
            if np.mean(hits)>.9:arrivals.append((rr*w+cc,steps))
        if len(arrivals)!=1:raise ValueError(f'Ambiguous/missing example arrival: {source}, {arrivals}')
        landing,distance=arrivals[0]
        j=next(j for j,R in enumerate(regions) if landing in R)
        receiver=inp['ids'][j];count=areas[j];letter=inp['letters'][landing]
        if equation!=f'|{areas[i]}-{lcount}|={distance}':raise ValueError('Arithmetic disagrees with counted regions and measured path')
        if root!=(i==inp['start']):raise ValueError('Incorrect example double-circle')
        direction={1:'right',-1:'left',w:'down',-w:'up'}[di]
        # Independently inspect the full drawn path from source to its arrival circle.
        v=inp['seeds'][i];sx=606+v%4*124+18;sy=350+v//4*124+78
        tx=606+landing%4*124+18;ty=350+landing//4*124+78
        dx=0 if sx==tx else (1 if tx>sx else -1);dy=0 if sy==ty else (1 if ty>sy else -1)
        p.line((sx,sy),(tx-dx*9,ty-dy*9),threshold=128)
        p.ring((tx,ty),6)
        # Directional head at the arrival, shaft checked separately above.
        hx=tx-dx*8;hy=ty-dy*8
        counts=[]
        for distance in (2,8,12):
            cx=hx-dx*distance;cy=hy-dy*distance
            box=([cx,cy-6,cx+1,cy+7] if dx else [cx-6,cy,cx+7,cy+1])
            counts.append(int(p.roi(box).sum()))
        if not counts[1]>=6 or counts[1]<=counts[0] or counts[1]<=counts[2]:raise ValueError('Completed trajectory head missing or reversed')
        p.cover[min(hy,hy-dy*12)-5:max(hy,hy-dy*12)+6,min(hx,hx-dx*12)-5:max(hx,hx-dx*12)+6]=True
        rows.append(dict(source=source,receiver=receiver,count=count,lookup=lookup,lookup_count=lcount,equation=equation,direction=direction,landing_cell=landing,letter=letter,distance=abs(v//4-landing//4)+abs(v%4-landing%4),shape=lshape))
    from inference import infer_address
    inferred=infer_address(inp['ids'],regions,rows)
    order=[r['source'] for r in rows]
    if len(set(order))!=len(inp['ids']) or order[0]!=inp['ids'][inp['start']]:raise ValueError('Example starts/order mismatch')
    if [r['receiver'] for r in rows]!=order[1:]+order[:1]:raise ValueError('Example table does not form a single cycle')
    loop_ids=[];loop_letters=[]
    for idx,xx in enumerate((320,510,700,890,1080)):
        num,double=p.badge((xx,1200));loop_ids.append(num)
        if double!=(idx in (0,4)):raise ValueError('Loop start marks incorrect')
        if idx<4:
            nx=xx+190;p.line((xx+42,1200),(nx-42,1200))
            # Larger head is tested by explicit shaft+connected shape near its endpoint.
            head=p.roi([nx-57,1192,nx-39,1209]);
            if len(components(head))!=1 or head.sum()<55:raise ValueError('Missing loop arrowhead')
            loop_letters.append(p.text([xx+77,1151,xx+113,1185],'ABCDEFGHIJKLMNOPQRSTUVWXYZ',True))
    word=p.text([1370,1178,1470,1216],'ABCDEFGHIJKLMNOPQRSTUVWXYZ',True)
    if loop_ids!=order+order[:1] or loop_letters!=[r['letter'] for r in rows] or word!=''.join(loop_letters):raise ValueError('Example output does not match arrivals')
    for yy in (888,974,1060):p.line((300,yy),(1150,yy),threshold=210)
    if p.arrow([543,528,584,545])!='right':raise ValueError('Missing input/completion arrow')
    p.remaining([602,346,1107,727])
    p.remaining([132,803,1565,1140])
    models,stats=solve_cover(inp)
    if len(models)!=1 or not stats['exhaustive']:raise ValueError('Example not uniquely completable')
    desc=describe(inp,models[0])
    if desc['regions']!=regions or desc['answer']!=word:raise ValueError('Completion contradicts example input')
    return dict(regions=regions,rows=rows,output=word,loop_ids=loop_ids,proof=stats,inferred_address=inferred,letter_allocation=allocation)

def rectangle(p,box,width=4):
    x,y,r,b=box
    for u,v in (((x,y),(r,y)),((r,y),(r,b)),((r,b),(x,b)),((x,b),(x,y))):p.line(u,v,width)

def mark(p,c,yes):
    x,y=c;box=[x-17,y-23,x+24,y+17]
    if yes:
        def draw(d,pt,s):
            d.line([pt((x-12,y)),pt((x-2,y+10))],fill=0,width=round(4*s))
            d.line([pt((x-2,y+10)),pt((x+18,y-17))],fill=0,width=round(4*s))
        p.graphic(box,draw,'check mark')
    else:p.text([x-13,y-13,x+14,y+15],'×',expected='×',role='label')

def read_legend(p):
    # These are rule demonstrations, not the unknown board configuration.
    for origin,tiles,yes in ((1120,((0,0),(1,0),(1,1)),True),(1335,((0,0),(1,1)),False)):
        for col,row in tiles:rectangle(p,[origin+col*30,355+row*30,origin+(col+1)*30,355+(row+1)*30],2.5)
        mark(p,(origin+100,385),yes)
    for rect,centers,yes,markx in (([1120,433,1188,527],[(1154,467)],True,1215),([1245,433,1305,527],[],False,1330),([1370,433,1498,527],[(1403,467),(1464,467)],False,1530)):
        rectangle(p,rect)
        for x,y in centers:
            p.badge((x,y))
            if p.arrow([x-17,y+29,x+22,y+46])!='right':raise ValueError('Malformed region arrow icon')
        mark(p,(markx,475),yes)
    graph_results=[]
    for x,y,split in ((1145,620,False),(1400,620,True)):
        centers=[(x,y),(x+94,y),(x+94,y+66),(x,y+66)]
        ids=[p.badge(c)[0] for c in centers]
        if len(set(ids))!=4:raise ValueError('Cycle diagram repeats identities')
        edges=[]
        for i,a in enumerate(centers):
            j=i^1 if split else (i+1)%4;b=centers[j]
            dx=int(np.sign(b[0]-a[0]));dy=int(np.sign(b[1]-a[1]));off=(10 if i%2==0 else -10) if split else 0
            sx=a[0]+dx*32;sy=a[1]+dy*32+off;tx=b[0]-dx*32;ty=b[1]-dy*32+off
            box=[min(sx,tx)-4,min(sy,ty)-7,max(sx,tx)+5,max(sy,ty)+8]
            direction=p.arrow(box)
            wanted=('right' if dx>0 else 'left') if dx else ('down' if dy>0 else 'up')
            if direction!=wanted:raise ValueError('Cycle diagram arrow reversed')
            edges.append([ids[i],ids[j]])
        mark(p,(1535 if split else 1280,653),not split)
        graph_results.append(dict(accepted=not split,ids=ids,edges=edges))
    p.remaining([1116,347,1565,721])
    return graph_results

def read_labels(p):
    import string
    rows=[('Example',[132,294,288,337]),('Region',[1116,299,1220,336]),('All regions',[1116,544,1272,581]),('Arrow',[304,747,396,782]),('Jump',[1003,747,1085,785]),('Loop',[132,1183,208,1221]),('Letters',[1161,1183,1267,1217]),('Bank',[132,709,208,745]),('Bank',[256,2034,333,2070])]
    for text,box in rows:
        p.text(box,string.ascii_letters,role='label',expected=text.replace(' ',''))
        p.texts[-1]['text']=text
    # Title and italic lede are matched and measured here; the solver does not
    # use them as constraints.
    for text,box,cap in [('City Limits',[132,125,525,204],[304,134,340,185]),("Fill by region number; inside each region, use reading order.",[132,221,1210,270],[139,229,160,255])]:
        a=p.roi(box);bb=bbox(a);cc=p.roi(cap,mark=False);cb=bbox(cc)
        if a.sum()<500:raise ValueError('Missing heading/lede')
        p.texts.append(dict(role='heading',text=text,box=[box[0]+bb[0],box[1]+bb[1],box[0]+bb[2],box[1]+bb[3]],min_glyph_height_px=cb[3]-cb[1],transcription_method='independent visual reading; native-pixel measurement'))

def read_page(path):
    p,m,e=read_grids(path)
    # Read labels before checking the legend's residual ink.
    read_labels(p)
    example=read_example(p,e)
    legend=read_legend(p)
    p.remaining([0,0,1700,2193])
    return p,m,e,example,legend
