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
    unit=a.shape[1]*.009
    cells=[c for c in holes if min(c.w,c.h)>unit and max(c.w,c.h)<a.shape[1]*.15 and c.area>.25*c.w*c.h]
    return ink,cells


def row_groups(cells):
    groups=[]
    for c in sorted(cells,key=lambda z:(z.cy,z.x)):
        if groups and abs(c.cy-groups[-1][0].cy)<min(c.h,groups[-1][0].h)*.15:
            groups[-1].append(c)
        else: groups.append([c])
    return [sorted(g,key=lambda c:c.x) for g in groups]



def paired_cells(ink,cells,ocr):
    pairs=[]
    for a in cells:
        if not 2.0<a.w/a.h<3.0:continue
        below=[b for b in cells if abs(b.x-a.x)<3 and abs(b.r-a.r)<3 and 0<=b.y-a.b<7 and 1.4<b.w/b.h<2.1]
        if len(below)!=1:continue
        b=below[0]
        try:
            idx=int(ocr.cell(ink,a));val=ocr.cell(ink,b)
            if val!='?' and not val.isdigit():continue
            pairs.append((idx,val,a,b))
        except ValueError:continue
    return pairs

def beds(ink,pairs,ocr):
    # Recover individual indexed pot/tray cells, then horizontal rows and the
    # consecutive second row. No page coordinates or instance values stored.
    bands=[]
    for z in sorted(pairs,key=lambda z:(z[2].y,z[2].x)):
        for band in bands:
            if abs(band[0][2].y-z[2].y)<4:
                band.append(z);break
        else:bands.append([z])
    groups=[]
    for band in bands:
        current=[]
        for z in sorted(band,key=lambda z:z[2].x):
            if current and (z[2].x-current[-1][2].r>current[-1][2].w*.5 or z[0]!=current[-1][0]+1):
                groups.append(current);current=[]
            current.append(z)
        if current:groups.append(current)
    result=[]
    for g in groups:
        if g[0][0]!=1 or len(g)<3:continue
        matches=[h for h in groups if h[0][0]==len(g)+1 and len(h)==len(g) and abs(h[0][2].x-g[0][2].x)<3 and 0<h[0][2].y-g[0][3].b<g[0][3].h*.7]
        gg=g+(matches[0] if len(matches)==1 else [])
        a=g[0][2];last=g[-1][2]
        label=ocr.read(ink,(a.x-3,a.y-a.h*1.35,last.r,a.y-4),'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        result.append((label.lower(),gg))
    return result

def arrow_directions(mask,axis='h'):
    if axis=='v':mask=mask.T
    out=[]
    for a in sorted(components(mask),key=lambda z:z.cy):
        if a.w<8 or a.h<5:continue
        m=mask[a.y:a.b,a.x:a.r];half=m.shape[1]//2
        out.append(1 if m[:,half:].sum()>m[:,:half].sum() else -1)
    return out

def parse_page(path):
    ink,cells=inspect(path);ocr=OCR();pairs=paired_cells(ink,cells,ocr);allbeds=beds(ink,pairs,ocr)
    if not allbeds:raise ValueError('No indexed nursery beds')
    n=max(len(g) for name,g in allbeds)
    if n<6:raise ValueError('Demonstration page')
    byname={}
    for name,g in allbeds:
        if len(g)==n:byname.setdefault(name,[]).append(g)
    for name in ('firsttags','firstimpressions','lasttags','lastimpressions'):
        if name not in byname:raise ValueError(f'Missing bed {name}: {list(byname)}')
    if len(byname['firsttags'])!=2:raise ValueError('Closure must repeat First tags')
    start,repeat=sorted(byname['firsttags'],key=lambda g:g[0][2].y)
    record=byname['firstimpressions'][0];finish=byname['lasttags'][0];last=byname['lastimpressions'][0]
    if [z[1] for z in start]!=[z[1] for z in repeat]:raise ValueError('Closure start mismatch')
    half=n//2;h=start[0][2].h
    eq=ocr.read(ink,(last[half-1][2].r+10,last[0][2].y,repeat[0][2].x-h,last[-1][3].b),'=')
    if eq!='=':raise ValueError('Closure equality missing')
    # The long return path has a left vertical and top/bottom horizontal joins.
    xedge=start[0][3].x;y0=round(start[0][3].cy);yturn=round(last[0][2].y-h*1.5)
    vert=np.flatnonzero(np.mean(ink[y0:yturn,:xedge-4],axis=0)>.97)
    if not len(vert):raise ValueError('First-tags return connector missing')
    inventory_groups=row_groups([c for c in cells if c.b<start[0][2].y and 1.3<c.w/c.h<1.8])
    inventories=[g for g in inventory_groups if len(g)==n]
    if len(inventories)!=1:raise ValueError('Seed inventory not identified')
    if sorted(int(ocr.cell(ink,c)) for c in inventories[0])!=list(range(1,n+1)):raise ValueError('Seed inventory invalid')
    lo=max(g[-1][3].b for g in (start,record,finish));hi=last[0][2].y
    symbols=[c for c in cells if lo<c.y<c.b<hi and .85<c.w/c.h<1.15]
    circles=[c for c in symbols if c.w>h*1.2 and c.area/(c.w*c.h)<.79]
    bands=row_groups(circles);rows=[]
    for band in bands:
        if len(band)%2:raise ValueError('Unpaired graft branches')
        for off in range(0,len(band),2):
            top=band[off:off+2];bottom=[]
            for c in top:
                below=[z for z in symbols if abs(z.cx-c.cx)<3 and z.y>c.b and z.y-c.b<c.h*.8 and z.w>c.w*.9 and z.area/(z.w*z.h)>.79]
                if len(below)!=1:raise ValueError('Graft address square missing')
                z=below[0];bottom.append(z)
                gap=ink[c.b+2:z.y-2,int(c.cx-12):int(c.cx+12)]
                if arrow_directions(gap,'v')!=[1]:raise ValueError('Graft vertical binding missing')
            a,b=bottom
            gap=ink[round(a.cy-a.h*.44):round(a.cy+a.h*.44),a.r+3:b.x-3]
            if arrow_directions(gap)!=[1,-1]:raise ValueError('Exchange arrows missing')
            a=top[0];boxes=[z for z in symbols if z.r<a.x and .45*a.w<z.w<.75*a.w and a.b<z.cy<bottom[0].cy]
            if not boxes:raise ValueError('Round selection square missing')
            box=max(boxes,key=lambda z:z.x)
            if ocr.cell(ink,box):raise ValueError('Main round is already selected')
            number=ocr.read(ink,(box.x-8,a.cy-a.h*.45,box.r+8,a.cy+a.h*.45),'0123456789')
            vals=[int(ocr.cell(ink,z))-1 for z in top+bottom]
            rows.append((int(number),vals))
    rows.sort()
    if [i for i,v in rows]!=list(range(1,len(rows)+1)):raise ValueError('Incomplete round sequence')
    first=min(c.y for c in circles)
    countboxes=[c for c in symbols if c.b<first and c.w<h]
    if len(countboxes)!=1:raise ValueError('Count box missing')
    box=countboxes[0]
    val=ocr.read(ink,(box.r+box.w*.3,box.y-box.h*.3,box.r+box.w*4,box.b+box.h*.3),'=0123456789')
    if not val.startswith('='):raise ValueError('Count equality missing')
    def values(g):return [-1 if z[1]=='?' else int(z[1])-1 for z in g]
    data={'n':n,'rows':[v for _,v in rows],'initial':values(start),'finish':values(finish),'record':values(record),'count':int(val[1:])}
    if not 0<data['count']<=len(rows):raise ValueError('Count outside range')
    if any(v<0 or v>=n for row in data['rows'] for v in row):raise ValueError('Graft endpoint outside nursery')
    if any(row[0]==row[1] or row[2]==row[3] for row in data['rows']):raise ValueError('Repeated endpoints')
    if any(v<0 or v>=n for v in data['record']):raise ValueError('Impression outside domain')
    for name in ('initial','finish'):
        known=[v for v in data[name] if v>=0]
        if len(known)!=len(set(known)) or any(v>=n for v in known):raise ValueError('Invalid tags')
    return data

def read_problem(directory):
    found=[];errors=[]
    for path in sorted(Path(directory).glob('*.png')):
        try:found.append(parse_page(path))
        except ValueError as exc:errors.append(f'{path.name}: {exc}')
    if len(found)!=1:raise ValueError('Expected one night-cycle page: '+'; '.join(errors))
    return found[0]
