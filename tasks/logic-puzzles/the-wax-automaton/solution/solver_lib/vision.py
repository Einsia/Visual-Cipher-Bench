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
        if score>.40: raise ValueError(f'Unrecognized glyph (score {score:.3f})')
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
    a=np.array(Image.open(path).convert('L'));ink=a<110
    unit=min(a.shape)*.011
    cells=[c for c in components(~ink) if min(c.w,c.h)>unit and max(c.w,c.h)<a.shape[1]*.4 and c.area>.23*c.w*c.h]
    return ink,cells


def row_groups(cells):
    groups=[]
    for c in sorted(cells,key=lambda z:(z.cy,z.x)):
        if groups and abs(c.cy-groups[-1][0].cy)<min(c.h,groups[-1][0].h)*.15:groups[-1].append(c)
        else:groups.append([c])
    return [sorted(g,key=lambda c:c.x) for g in groups]


def paired_cells(ink,cells,ocr):
    pairs=[]
    for a in cells:
        if not 1.35<a.w/a.h<3.0:continue
        for b in cells:
            if abs(a.x-b.x)>2 or abs(a.r-b.r)>2:continue
            if not 0<b.y-a.b<a.h*.16 or not 1.1<b.h/a.h<1.4:continue
            try:
                index=int(ocr.cell(ink,a));value=ocr.cell(ink,b)
                if not 1<=index<=16 or not (value=='?' or value.isdigit()):continue
                pairs.append((a,b,index,value))
            except ValueError:pass
    return pairs


def read_hubs(ink,cells,ocr,pairs):
    hubs={}
    for c in cells:
        if not .96<c.w/c.h<1.04 or not ink.shape[1]*.055<c.w<ink.shape[1]*.12:continue
        try:
            top=ocr.read(ink,(c.x+c.w*.10,c.cy-c.h*.20,c.r-c.w*.10,c.cy+c.h*.01),'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            bottom=ocr.read(ink,(c.x+c.w*.10,c.cy+c.h*.035,c.r-c.w*.10,c.cy+c.h*.22),'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        except ValueError:continue
        if bottom!='REEDS' or top not in ('OPENING','CLOSING'):continue
        found=[]
        for a,b,j,v in pairs:
            dist=((a.cx-c.cx)**2+(((a.y+b.b)/2)-c.cy)**2)**.5
            if .70*c.w<dist<1.55*c.w and a.w>.38*c.w:found.append((a,b,j,v))
        found.sort(key=lambda q:q[2])
        if [q[2] for q in found]!=list(range(1,len(found)+1)):continue
        hubs[top]=(c,found)
    if set(hubs)!=set(('OPENING','CLOSING')):raise ValueError('Two labelled circular reed banks not recovered')
    return hubs


def parse_page(path):
    ink,cells=inspect(path);ocr=OCR();pairs=paired_cells(ink,cells,ocr)
    hubs=read_hubs(ink,cells,ocr,pairs)
    start=hubs['OPENING'];finish=hubs['CLOSING'];n=len(start[1])
    if n!=len(finish[1]) or n<5:raise ValueError('Not the full instrument page')
    # Straight wax strips are recognized by contiguous indexed cells.
    strips={}
    bank_cells=[q[0] for _,qs in hubs.values() for q in qs]
    for group in row_groups([q[0] for q in pairs if q[0] not in bank_cells]):
        if len(group)!=n:continue
        if any(b.x-a.r>a.h*.2 for a,b in zip(group,group[1:])):continue
        found=sorted([q for q in pairs if q[0] in group],key=lambda q:q[0].x)
        if [q[2] for q in found]!=list(range(1,n+1)):continue
        a=group[0];z=group[-1]
        try:label=ocr.read(ink,(a.x-3,a.y-a.h*1.8,z.r,a.y-a.h*.4),'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        except ValueError:continue
        strips[label.lower()]=found
    if set(strips)!=set(('freshwax','finalwax','openingreeds')):raise ValueError(f'Wax / closure strips incomplete: {list(strips)}')
    record=strips['freshwax'];final=strips['finalwax'];repeat=strips['openingreeds']
    if [q[3] for q in repeat]!=[q[3] for q in start[1]]:raise ValueError('Repeated opening bank differs')
    if any(q[3]!='?' for q in final):raise ValueError('Unexpected disclosed final wax value')
    h=final[0][0].h;cx=(final[0][0].x+final[-1][0].r)/2
    eq=ocr.read(ink,(cx-h,final[0][1].b+h*.5,cx+h,repeat[0][0].y-h*1.6),'=')
    if eq!='=':raise ValueError('Closure equation is missing')
    # Long identity wire joins the opening disc and its repeated indexed strip.
    left=min(q[0].x for q in start[1]);cy=round(start[0].cy)
    bottom=max(q[1].b for q in start[1]);end_y=round(repeat[0][1].cy)
    region=ink[cy:int(bottom+10),:int(left-5)]
    xs=np.flatnonzero(np.mean(region,axis=0)>.93)
    wire=False
    for x in xs:
        ys=np.flatnonzero(np.mean(ink[int(bottom):,x:int(repeat[-1][0].r)],axis=1)>.95)+int(bottom)
        for y in ys:
            if y>bottom+h*4:continue
            right=ink[end_y:y+1,int(repeat[-1][0].r):]
            xr=np.flatnonzero(np.mean(right,axis=0)>.95)+int(repeat[-1][0].r)
            if len(xr) and np.any(np.mean(ink[cy-3:cy+4,x:int(left+1)],axis=1)>.85):wire=True
    if not wire:raise ValueError('Opening-bank identity wire missing')
    # Individual reed tongues above the circular bank; decorative underline excluded.
    top=min(q[0].y for q in start[1]);tokens=[]
    for c in cells:
        if c.b>=top or not .8<c.w/c.h<1.02 or not h*1.4<c.w<h*1.9:continue
        try:tokens.append(int(ocr.read(ink,(c.x+4,c.y+c.h*.08,c.r-4,c.y+c.h*.7))))
        except ValueError:continue
    if sorted(tokens)!=list(range(1,n+1)):raise ValueError('Spare reed inventory incomplete')
    # Each programme module is a large enclosure around two wired lanes.
    modules=[c for c in cells if 2.75<c.w/c.h<3.1 and c.w>h*9 and c.y>bottom]
    rows=[];boxlist=[]
    for c in modules:
        inside=[z for z in cells if c.x<z.x<z.r<c.r and c.y<z.y<z.b<c.b]
        ends=[z for z in inside if .92<z.w/z.h<1.08 and .34*c.h<z.w<.44*c.h]
        if len(ends)!=4:continue
        cols=sorted(ends,key=lambda z:z.x);rounds=sorted(cols[:2],key=lambda z:z.y);squares=sorted(cols[2:],key=lambda z:z.y)
        if any(z.area/z.w/z.h>.8 for z in rounds) or any(z.area/z.w/z.h<.8 for z in squares):raise ValueError('Sample/address shape mismatch')
        boxes=[z for z in inside if .92<z.w/z.h<1.08 and .20*c.h<z.w<.26*c.h]
        if len(boxes)!=1:raise ValueError('Module selection square missing')
        box=boxes[0];boxlist.append(box)
        if ocr.read(ink,(box.x+4,box.y+4,box.r-4,box.b-4))!='':raise ValueError('A programme module is already selected')
        number=int(ocr.read(ink,(c.x+c.w*.025,box.y-1,box.x-c.w*.035,box.b+1)))
        vals=[]
        for z in rounds+squares:
            val=ocr.read(ink,(z.cx-z.w*.39,z.cy-z.h*.24,z.cx+z.w*.39,z.cy+z.h*.24))
            vals.append(int(val))
        # Check each arrow's orientation using its tip's greater ink mass.
        for a,b in zip(rounds,squares):
            patch=ink[round(a.cy-a.h*.28):round(a.cy+a.h*.28),a.r+3:b.x-3]
            marks=[z for z in components(patch) if z.w>a.w*.8]
            if len(marks)!=1:raise ValueError('Sample/address wire disconnected')
            mark=marks[0];arr=patch[mark.y:mark.b,mark.x:mark.r];mid=arr.shape[1]//2
            if arr[:,mid:].sum()<=arr[:,:mid].sum():raise ValueError('Sample arrow reversed')
        # The exchange consists of two routed return lines, outside both squares.
        x0=squares[0].r+3;x1=round(c.r-c.w*.05)
        patch=ink[round(squares[0].cy-squares[0].h*.30):round(squares[1].cy+squares[1].h*.30),x0:x1]
        wires=[z for z in components(patch) if z.h>c.h*.4]
        if len(wires)!=2:raise ValueError('Two exchange paths not recovered')
        rows.append((number,vals,c))
    rows.sort(key=lambda q:q[0])
    if not rows or [q[0] for q in rows]!=list(range(1,len(rows)+1)):raise ValueError('Incomplete programme numbering')
    # Validate physical programme continuity in the printed numbered order.
    for (_,_,a),(_,_,b) in zip(rows,rows[1:]):
        if abs(a.cy-b.cy)<h:
            lo,hi=sorted((a,b),key=lambda z:z.x);patch=ink[round(a.cy-h*.4):round(a.cy+h*.4),lo.r+3:hi.x-3]
            if not any(z.w>patch.shape[1]*.6 for z in components(patch)):raise ValueError('Programme order connector missing')
        else:
            xx=round(max(a.r,b.r)+h*.6) if a.cx>ink.shape[1]/2 else round(min(a.x,b.x)-h*.6)
            patch=ink[round(a.cy):round(b.cy),xx-5:xx+6]
            if np.max(np.mean(patch,axis=0))<.9:raise ValueError('Programme turn connector missing')
    first_y=min(q[2].y for q in rows);bh=boxlist[0].h
    counts=[z for z in cells if bottom<z.y<z.b<first_y and abs(z.w-bh)<3 and abs(z.h-bh)<3]
    if len(counts)!=1:raise ValueError('Engaged count checkbox missing')
    c=counts[0]
    # Checked count must contain actual ink, not a blank square.
    if not ink[c.y+5:c.b-5,c.x+5:c.r-5].any():raise ValueError('Engaged checkbox is unchecked')
    counttext=ocr.read(ink,(c.r+bh*.3,c.y-bh*.2,c.r+bh*4.6,c.b+bh*.25),'=0123456789')
    if not counttext.startswith('='):raise ValueError('Engaged count equality missing')
    count=int(counttext[1:])
    def values(ps):return [-1 if q[3]=='?' else int(q[3])-1 for q in ps]
    data={'n':n,'rows':[[v-1 for v in vals] for _,vals,_ in rows],'initial':values(start[1]),'finish':values(finish[1]),'record':values(record),'count':count}
    if not 0<count<=len(rows):raise ValueError('Invalid selection count')
    if any(not 0<=v<n for row in data['rows'] for v in row):raise ValueError('Invalid source: '+str(data['rows']))
    if any(row[0]==row[1] or row[2]==row[3] for row in data['rows']):raise ValueError('Coincident source pair')
    if any(not 0<=v<n for v in data['record']):raise ValueError('Invalid fresh wax')
    return data


def read_problem(directory):
    candidates=[];errors=[]
    for path in sorted(Path(directory).glob('*.png')):
        try:candidates.append((path,parse_page(path)))
        except (ValueError,IndexError) as e:errors.append(f'{path.name}: {e}')
    if len(candidates)!=1:raise ValueError('Could not identify one performance page: '+'; '.join(errors))
    return candidates[0][1]
