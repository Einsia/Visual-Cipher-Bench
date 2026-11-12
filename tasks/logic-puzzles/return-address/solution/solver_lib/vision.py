"""Geometry and glyph recognition. All page coordinates are detected, not stored."""
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from PIL import Image

@dataclass
class Region:
    x: int
    y: int
    r: int
    b: int
    area: int
    @property
    def w(self): return self.r-self.x
    @property
    def h(self): return self.b-self.y
    @property
    def cx(self): return (self.x+self.r)/2
    @property
    def cy(self): return (self.y+self.b)/2


def components(mask):
    """Four-connected run-length union/find, without SciPy or OpenCV."""
    parent=[]; runs=[]; previous=[]
    def root(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for y,line in enumerate(mask):
        edges=np.flatnonzero(np.diff(np.r_[False,line,False]))
        current=[]; j=0
        for x,r in zip(edges[::2],edges[1::2]):
            x=int(x);r=int(r); label=len(parent);parent.append(label)
            while j<len(previous) and previous[j][1]<=x: j+=1
            q=j
            while q<len(previous) and previous[q][0]<r:
                a=root(previous[q][2]);b=root(label)
                if a!=b: parent[b]=a
                q+=1
            current.append((x,r,label));runs.append((x,y,r,label))
        previous=current
    boxes={}
    for x,y,r,label in runs:
        label=root(label)
        if label not in boxes: boxes[label]=[x,y,r,y+1,r-x]
        else:
            z=boxes[label];z[0]=min(z[0],x);z[1]=min(z[1],y);z[2]=max(z[2],r);z[3]=y+1;z[4]+=r-x
    return [Region(*z) for z in boxes.values()]


def trim(a):
    yy,xx=np.where(a)
    if not len(xx): raise ValueError('Empty glyph')
    return a[yy.min():yy.max()+1,xx.min():xx.max()+1]

class OCR:
    def __init__(self):
        with np.load(Path(__file__).with_name('font_templates.npz')) as z:
            self.templates={key: z[key] for key in z.files}
    def glyph(self,a,alphabet='0123456789?'):
        a=trim(a); candidates=[]
        for key,t in self.templates.items():
            ch=chr(int(key.rsplit('_',1)[1]))
            if ch not in alphabet: continue
            # Compare normalized ink and penalize incompatible aspect ratios.
            target=np.array(Image.fromarray(t).resize((a.shape[1],a.shape[0]),Image.Resampling.NEAREST))
            error=np.mean(a!=target)+.15*abs(np.log((a.shape[1]/a.shape[0])/(t.shape[1]/t.shape[0])))
            candidates.append((float(error),ch))
        score,ch=min(candidates)
        if score>.35: raise ValueError(f'Unrecognized glyph (score {score:.3f})')
        return ch
    def read(self,ink,box,alphabet='0123456789?'):
        x,y,r,b=map(int,box)
        a=ink[y:b,x:r]
        if not np.any(a): return ''
        # Glyphs (including the disconnected dot of ?) share their x span.
        active=np.any(a,axis=0)
        edges=np.flatnonzero(np.diff(np.r_[False,active,False]))
        return ''.join(self.glyph(a[:,l:h],alphabet) for l,h in zip(edges[::2],edges[1::2]))
    def cell(self,ink,c):
        pad=max(2,round(min(c.w,c.h)*(.19 if .85<c.w/c.h<1.15 else .09)))
        return self.read(ink,(c.x+pad,c.y+pad,c.r-pad,c.b-pad))


def inspect(path):
    a=np.array(Image.open(path).convert('L'))
    ink=a<110
    holes=components(~ink)
    # Text holes are tiny. Diagram enclosures have substantial area and both
    # dimensions of at least 1.4% of page width, at every supported scale.
    unit=a.shape[1]*.014
    cells=[c for c in holes if min(c.w,c.h)>unit and max(c.w,c.h)<a.shape[1]*.15 and c.area>.25*c.w*c.h]
    return ink,cells


def row_groups(cells):
    groups=[]
    for c in sorted(cells,key=lambda z:(z.cy,z.x)):
        if groups and abs(c.cy-groups[-1][0].cy)<min(c.h,groups[-1][0].h)*.15:
            groups[-1].append(c)
        else: groups.append([c])
    return [sorted(g,key=lambda c:c.x) for g in groups]


def racks_on_page(ink,cells,ocr):
    rows=[g for g in row_groups([c for c in cells if c.w/c.h>1.5]) if len(g)>=3]
    racks=[]
    for top,bottom in zip(rows,rows[1:]):
        if len(top)!=len(bottom): continue
        if abs(bottom[0].y-top[0].b)>.3*top[0].h: continue
        if any(abs(a.cx-b.cx)>.1*a.w for a,b in zip(top,bottom)): continue
        if any(b.x-a.r>.15*a.w for a,b in zip(top,top[1:])): continue
        try:
            nums=[ocr.cell(ink,c) for c in top]
            if [int(t) for t in nums]!=list(range(1,len(top)+1)): continue
            vals=[ocr.cell(ink,c) for c in bottom]
            label=ocr.read(ink,(top[0].x-5,top[0].y-1.1*top[0].h,top[-1].r,top[0].y-.15*top[0].h),'SFabcdefghijklmnopqrstuvwxyz')
        except ValueError: continue
        racks.append((label,top,bottom,vals))
    return racks


def parse_page(path):
    ink,cells=inspect(path);ocr=OCR();racks=racks_on_page(ink,cells,ocr)
    if not racks: raise ValueError('No labelled racks detected')
    n=max(len(r[1]) for r in racks)
    racks=[r for r in racks if len(r[1])==n]
    byname={}
    for r in racks: byname.setdefault(r[0].lower(),[]).append(r)
    required=('startlabels','startrecord','finishlabels','finishrecord')
    if any(name not in byname for name in required):
        raise ValueError(f'Incomplete problem rack labels: {list(byname)}')
    start=byname['startlabels'][0];record=byname['startrecord'][0]
    finish=byname['finishlabels'][0];endrec=byname['finishrecord'][0]
    if len(byname['startlabels'])!=2:
        raise ValueError('Expected a repeated Start labels rack connected to the closure')
    closure=byname['startlabels'][1]
    if closure[3]!=start[3]: raise ValueError('Repeated start rack differs')
    # Read the equality glyph located in the gap between the last two racks.
    # The crop is based on detected table extents, not page coordinates.
    center=(endrec[1][0].x+endrec[1][-1].r)/2
    h=endrec[1][0].h
    eq=ocr.read(ink,(center-h,endrec[2][0].b+h*.2,center+h,closure[1][0].y-h*.3),'=')
    if eq!='=': raise ValueError('Closure equality sign missing')
    # Follow the long vertical return connector and its two horizontal ends.
    # Its x coordinate is recovered from the ink projection left of the racks.
    xedge=start[2][0].x
    y0=round(start[2][0].cy);y1=round(closure[2][0].cy)
    region=ink[y0:y1,:xedge-4]
    vertical=np.flatnonzero(np.mean(region,axis=0)>.95)
    connected=False
    for x in vertical:
        upper=ink[y0-round(h*.25):y0+round(h*.25),x:xedge]
        lower=ink[y1-round(h*.25):y1+round(h*.25),x:xedge]
        if np.any(np.mean(upper,axis=1)>.9) and np.any(np.mean(lower,axis=1)>.9):
            connected=True;break
    if not connected: raise ValueError('Start rack return connector missing')
    # Inventory is a row of separate (non-adjacent) boxed tokens above Start.
    groups=row_groups([c for c in cells if c.b<start[1][0].y and c.w/c.h>1.1])
    inventories=[g for g in groups if len(g)==n and all(b.x>a.r for a,b in zip(g,g[1:]))]
    if len(inventories)!=1: raise ValueError('Inventory not uniquely detected')
    identities=sorted(int(ocr.cell(ink,c)) for c in inventories[0])
    if identities!=list(range(1,n+1)): raise ValueError('Inventory must match the slot identities')
    # Coupon symbols lie between Start record and Finish labels; each lane has
    # two round copy sources, then two square address sources.
    symbols=[c for c in cells if record[2][0].b<c.y<c.b<finish[1][0].y and .85<c.w/c.h<1.15]
    large=[c for c in symbols if c.w>.8*np.median([z.w for z in symbols])]
    bands=row_groups(large)
    coupons=[]
    for band in bands:
        for off in range(0,len(band)-3,4):
            a,b,c,d=band[off:off+4]
            if not (a.area/a.w/a.h<.8 and b.area/b.w/b.h<.8 and c.area/c.w/c.h>.8 and d.area/d.w/d.h>.8): continue
            vals=[int(ocr.cell(ink,z)) for z in (a,b,c,d)]
            # Locate the empty selection square immediately to the left, then
            # read the printed coupon number to its left.
            boxes=[z for z in symbols if z.r<a.x and abs(z.cy-a.cy)<a.h*.15 and .35*a.w<z.w<.75*a.w]
            if not boxes: raise ValueError('Coupon checkbox missing')
            check=max(boxes,key=lambda z:z.x)
            num=ocr.read(ink,(check.x-2*check.w,check.cy-.5*check.h,check.x-.2*check.w,check.cy+.5*check.h),'0123456789')
            # Confirm copy arrow and bidirectional swap arrows in their gaps.
            for left,right,expected in ((a,b,[1]),(c,d,[1,-1])):
                gap=ink[int(left.cy-left.h*.48):int(left.cy+left.h*.48),left.r+2:right.x-2]
                arrows=sorted((z for z in components(gap) if z.w>left.w*.4 and z.h>left.h*.15),key=lambda z:z.cy)
                directions=[]
                for arrow in arrows:
                    mark=gap[arrow.y:arrow.b,arrow.x:arrow.r]
                    half=mark.shape[1]//2
                    directions.append(1 if mark[:,half:].sum()>mark[:,:half].sum() else -1)
                if directions!=expected: raise ValueError('Coupon arrow direction or count differs')
            coupons.append((int(num),vals))
    coupons.sort()
    if not coupons or [i for i,v in coupons]!=list(range(1,len(coupons)+1)):
        raise ValueError('Coupon numbering is incomplete')
    first=min(c.y for c in large if c.area/c.w/c.h<.8)
    checks=[c for c in symbols if c.b<first and c.w<.75*large[-1].w]
    if len(checks)!=1: raise ValueError('Count box not uniquely detected')
    check=checks[0]
    counttext=ocr.read(ink,(check.r+check.w*.3,check.y-check.h*.2,check.r+check.w*4,check.b+check.h*.2),'=0123456789')
    if not counttext.startswith('='): raise ValueError('Count equality missing')
    count=int(counttext[1:])
    if not 0<count<=len(coupons): raise ValueError('Invalid selected count')
    def values(r): return [-1 if s=='?' else int(s)-1 for s in r[3]]
    data={'n':n,'rows':[[v-1 for v in row] for _,row in coupons], 'initial':values(start),'finish':values(finish),'record':values(record),'count':count}
    if any(v<0 or v>=n for row in data['rows'] for v in row): raise ValueError('Source outside inventory')
    if any(row[2]==row[3] for row in data['rows']): raise ValueError('Duplicate address sources')
    if any(v<0 or v>=n for v in data['record']): raise ValueError('Invalid initial Record')
    for name in ('initial','finish'):
        known=[v for v in data[name] if v>=0]
        if len(set(known))!=len(known) or any(v>=n for v in known): raise ValueError('Invalid Labels clues')
    return data


def read_problem(directory):
    candidates=[];errors=[]
    for path in sorted(Path(directory).glob('*.png')):
        try: candidates.append((path,parse_page(path)))
        except ValueError as e: errors.append(f'{path.name}: {e}')
    if len(candidates)!=1: raise ValueError('Could not identify one problem page: '+'; '.join(errors))
    return candidates[0][1]
