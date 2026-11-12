"""PNG-only geometric reader. Layout constants are coordinates, not puzzle data.

All 475 grid bits and all seal identities are recovered from pixels. A coverage
mask rejects additional marks anywhere on the page. Font resources are generic
DejaVu outlines, not images or an answer-bearing transcription.
"""
import hashlib, json, math, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageChops

class PixelError(ValueError): pass

def require(ok, message):
    if not ok: raise PixelError(message)

def dilate(a):
    p=np.pad(a,1); out=np.zeros_like(a)
    for y in range(3):
        for x in range(3): out |= p[y:y+a.shape[0],x:x+a.shape[1]]
    return out

def bbox(mask, origin=(0,0)):
    yy,xx=np.where(mask)
    require(len(xx)>0,'Empty expected object')
    return [int(xx.min()+origin[0]),int(yy.min()+origin[1]),int(xx.max()+origin[0]+1),int(yy.max()+origin[1]+1)]

def runs(a):
    v=np.flatnonzero(np.diff(np.r_[False,a,False].astype(int)))
    return list(zip(v[::2].tolist(),v[1::2].tolist()))

FACES=json.loads((Path(__file__).parent/'glyphs.json').read_text())['faces']
TOKEN=re.compile(r'[MLQCZ]|-?\d+(?:\.\d+)?')

def font_image(text,size=34,bold=False,italic=False):
    """Sample bundled outlines; independently rendered solely for OCR checks."""
    face=FACES['sans-bold' if bold else 'sans']; scale=size/face['units_per_em']
    width=sum(face['glyphs'][c]['adv']*scale for c in text)
    ss=4; pad=8; baseline=size+pad
    canvas=Image.new('1',(int(math.ceil(width+2*pad+size/3))*ss,(size+2*pad+20)*ss))
    ox=pad; cap_boxes=[]
    for ch in text:
        tokens=TOKEN.findall(face['glyphs'][ch]['d']); pos=0; contours=[]; pts=[]; cur=None
        def point(x,y): return (ox+(x+y*(math.tan(math.radians(11)) if italic else 0))*scale,baseline-y*scale)
        while pos<len(tokens):
            cmd=tokens[pos];pos+=1
            if cmd=='Z':
                if pts: contours.append(pts)
                pts=[];continue
            n={'M':2,'L':2,'Q':4,'C':6}[cmd]
            vals=list(map(float,tokens[pos:pos+n]));pos+=n
            ps=[point(*vals[i:i+2]) for i in range(0,n,2)]
            if cmd in ('M','L'):
                if cmd=='M' and pts:contours.append(pts);pts=[]
                cur=ps[0];pts.append(cur)
            else:
                p0=cur
                for t in np.linspace(0,1,21)[1:]:
                    u=1-t
                    if cmd=='Q':q=tuple(u*u*p0[k]+2*u*t*ps[0][k]+t*t*ps[1][k] for k in (0,1))
                    else:q=tuple(u**3*p0[k]+3*u*u*t*ps[0][k]+3*u*t*t*ps[1][k]+t**3*ps[2][k] for k in (0,1))
                    pts.append(q)
                cur=ps[-1]
        if pts:contours.append(pts)
        char=Image.new('1',canvas.size)
        for contour in contours:
            layer=Image.new('1',canvas.size);ImageDraw.Draw(layer).polygon([(round(x*ss),round(y*ss)) for x,y in contour],fill=1)
            char=ImageChops.logical_xor(char,layer)
        canvas=ImageChops.logical_or(canvas,char)
        ox+=face['glyphs'][ch]['adv']*scale
    small=canvas.convert('L').resize((canvas.width//ss,canvas.height//ss),Image.Resampling.LANCZOS)
    a=np.array(small)>127; b=bbox(a)
    return a[b[1]:b[3],b[0]:b[2]]

def shape_close(a,b):
    # Tight crops may differ by one pixel from curve rasterization conventions.
    if abs(a.shape[0]-b.shape[0])>2 or abs(a.shape[1]-b.shape[1])>2:return False
    if max(a.shape)<60 and a.shape!=b.shape:b=np.array(Image.fromarray(b).resize((a.shape[1],a.shape[0]),Image.Resampling.NEAREST))
    h=max(a.shape[0],b.shape[0])+4;w=max(a.shape[1],b.shape[1])+4
    aa=np.zeros((h,w),bool);aa[2:2+a.shape[0],2:2+a.shape[1]]=a
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            bb=np.zeros((h,w),bool);bb[2+dy:2+dy+b.shape[0],2+dx:2+dx+b.shape[1]]=b
            if not (aa&~dilate(bb)).any() and not (bb&~dilate(aa)).any():return True
    return False

class Page:
    def __init__(self,path):
        self.path=Path(path);im=Image.open(path)
        require(im.size==(1700,2193),'Unexpected page dimensions')
        require(im.mode in ('RGB','RGBA'),'Unexpected PNG mode')
        require(not any(k in im.info for k in ('exif','comment','Description','Comment')),'Unexpected metadata')
        rgb=np.array(im.convert('RGB'));require(np.all(rgb.max(2)==rgb.min(2)),'Non-monochrome pixels')
        if im.mode=='RGBA':require(np.all(np.array(im)[:,:,3]==255),'Transparent pixels')
        self.gray=rgb[:,:,0]; self.ink=self.gray<200;self.cover=np.zeros(self.ink.shape,bool)
        self.records=[];self.text=[];self.counts={'grids':0,'seals':0,'arrows':0,'blanks':0}
        self.hash=hashlib.sha256(self.path.read_bytes()).hexdigest()

    def area(self,box):
        x,y,X,Y=map(int,box);self.cover[y:Y,x:X]=True
        return self.gray[y:Y,x:X]

    def text_at(self,box,expected=None,role='label',size=34,bold=False,italic=False):
        x,y,X,Y=box;a=self.area(box)<128;b=bbox(a,(x,y));crop=self.gray[b[1]:b[3],b[0]:b[2]]<128
        choices=[expected] if expected is not None else list('ABCDEFGHIJKLMNOPQRSTUVWXYZ?0123456789')
        hits=[s for s in choices if shape_close(crop,font_image(s,size,bold,italic))]
        require(len(hits)==1,f'Text absent, damaged or ambiguous at {box}: {hits}')
        s=hits[0]
        # Cap measurements use actual isolated capital ink, not font target values.
        # These header lines each begin with an isolated capital (L or T).
        if role=='heading':
            first_width=33 if bold else 19
            # T's horizontal bar has no overlap with h at its cap-height rows.
            sub=self.gray[b[1]:b[3],b[0]:b[0]+first_width]<128
            if bold:
                xx=b[0]; yy,xxs=np.where(self.gray[120:200,xx:xx+33]<128);height=int(yy.max()-yy.min()+1)
            else:
                # restrict first T to its original advance, excluding h descender
                yy,xxs=np.where(sub);height=int(yy.max()-yy.min()+1)
        else:height=b[3]-b[1]
        self.text.append({'role':role,'text':s,'box':b,'min_glyph_height_px':height})
        require(height>=19,f'Glyph below native threshold: {b}')
        return s,b,height

    def grid(self,x,y):
        full=self.area((x-2,y-2,x+182,y+182))
        bits=[]
        for r in range(5):
            row=''
            for c in range(5):
                a=self.gray[y+36*r+3:y+36*(r+1)-3,x+36*c+3:x+36*(c+1)-3]
                black=float((a<40).mean());white=float((a>240).mean())
                require(max(black,white)>0.999,f'Partial/foreign mark in grid cell {(x,y,r,c)}')
                row+=str(int(black>white))
            bits.append(row)
        for k in range(6):
            for axis in (0,1):
                a=(self.gray[y:y+181,x+36*k-1:x+36*k+2] if axis==0 else self.gray[y+36*k-1:y+36*k+2,x:x+181])<210
                require(np.all(a.any(axis=1-axis)),f'Missing grid boundary at {(x,y,k,axis)}')
        # Outer margins must not contain extra marks.
        b=bbox(full<200,(x-2,y-2))
        require(b[0]>=x-2 and b[2]<=x+182,'Unexpected grid extent')
        self.counts['grids']+=1
        return bits,b

    def seals(self,cx,cy):
        box=(cx-125,cy-27,cx+126,cy+28);a=self.area(box)<128
        rs=runs(a.any(0)); out=[];boxes=[]
        require(1<=len(rs)<=4,f'Missing/extra seal at {box}')
        centers=[]
        for l,r in rs:
            m=a[:,l:r]; b=bbox(m,(box[0]+l,box[1]));w=b[2]-b[0];h=b[3]-b[1]
            require(41<=w<=47 and 41<=h<=47,f'Incomplete seal at {b}')
            crop=self.gray[b[1]:b[3],b[0]:b[2]]<128
            hits=[]
            for kind in ('diamond','circle'):
                yy,xx=np.mgrid[:h,:w];dx=xx+0.5-w/2;dy=yy+0.5-h/2
                distance=np.sqrt(dx*dx+dy*dy) if kind=='circle' else (np.abs(dx)+np.abs(dy))/math.sqrt(2)
                radius=21 if kind=='circle' else 21/math.sqrt(2)
                t=np.abs(distance-radius)<=2
                if shape_close(crop,t):hits.append(kind)
            require(len(hits)==1,f'Seal not a complete circle/diamond at {b}: {hits}')
            out+=hits;boxes.append(b);centers.append((b[0]+b[2])/2)
        require(abs(sum(centers)/len(centers)-cx)<2,'Uncentred extra/missing seal')
        require(all(abs(b-a-58)<2 for a,b in zip(centers,centers[1:])),'Irregular seal spacing')
        self.counts['seals']+=len(out)
        return out,boxes

    def arrow(self,x1,y1,x2,y2):
        x=min(x1,x2)-3;y=min(y1,y2)-9;X=max(x1,x2)+3;Y=max(y1,y2)+9
        if x1==x2:x=x1-9;X=x1+9;y=min(y1,y2)-3;Y=max(y1,y2)+3
        a=self.area((x,y,X,Y))<128;b=bbox(a,(x,y))
        # Require an unbroken centre shaft, plus connected, symmetric head.
        if y1==y2:
            require(np.all((self.gray[y1-1:y1+2,x1:x2]<128).any(0)),f'Broken horizontal arrow at {b}')
            require((self.gray[y1-6:y1-3,x2-14:x2-8]<128).any() and (self.gray[y1+3:y1+7,x2-14:x2-8]<128).any(),'Missing arrow head')
            require(b[0]>=x1-2 and b[2]<=x2+2 and b[1]>=y1-8 and b[3]<=y1+8,'Extra arrow marks')
        else:
            require(np.all((self.gray[y1:y2,x1-1:x1+2]<128).any(1)),f'Broken down arrow at {b}')
            require((self.gray[y2-14:y2-8,x1-6:x1-3]<128).any() and (self.gray[y2-14:y2-8,x1+3:x1+7]<128).any(),'Missing down arrow head')
        # Flood-fill local ink; arrow head alone cannot satisfy continuity.
        ys,xs=np.where(a);seen={(int(ys[0]),int(xs[0]))};stack=list(seen)
        while stack:
            yy,xx=stack.pop()
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(yy+dy,xx+dx)
                if 0<=q[0]<a.shape[0] and 0<=q[1]<a.shape[1] and a[q] and q not in seen:seen.add(q);stack.append(q)
        require(len(seen)==len(ys),'Disconnected extra arrow component')
        self.counts['arrows']+=1
        return b

    def blank(self,cx,y):
        a=self.area((cx-44,y-3,cx+44,y+4))<128;b=bbox(a,(cx-44,y-3))
        require(np.all(a[:,3:85].any(0)),'Missing/broken answer underline')
        require(b[3]-b[1]<=3 and 81<=b[2]-b[0]<=85,'Malformed answer underline')
        self.counts['blanks']+=1;return b

    def unknown(self,x,y):
        # Separate border and text regions, leaving all remaining interior blank.
        for b in ((x-2,y-2,x+182,y+3),(x-2,y+178,x+182,y+183),(x-2,y-2,x+3,y+182),(x+178,y-2,x+183,y+182)):
            a=self.area(b)<128
            require(np.all(a.any(0 if a.shape[1]>a.shape[0] else 1)),'Broken unknown-box outline')
        return self.text_at((x+66,y+65,x+114,y+115))

    def finish(self):
        stray=self.ink&~self.cover
        require(not stray.any(),f'Unaccounted extra mark at {bbox(stray) if stray.any() else None}')
        return {'file':self.path.name,'all_visible_text_inventoried':True,'text_regions':self.text,'counts':self.counts}

def parse(images):
    pages=[Page(Path(images)/f'{i:02}.png') for i in (1,2)]
    observations=[];targets=[];elements=[]
    for p in pages:
        for suffix,box,txt,bold,italic,size in [('title',(130,120,900,205),'Lasting Impressions',True,False,64)]:
            text,bb,hh=p.text_at(box,txt,'heading',size,bold,italic)
            elements.append(dict(id=p.path.name+'_'+suffix,image=p.path.name,box=bb,observed={'text':text},must_read=True,glyph_height_px=hh))
    p=pages[0]
    positions=[(247,420),(1009,420),(247,760),(1009,760),(628,1100)]
    for ident,(x,y) in zip(('proof_1','proof_2','proof_3','proof_4','proof_6'),positions):
        before,bb=p.grid(x,y);after,ab=p.grid(x+264,y)
        sy,sb=p.seals(x+222,y-57);arr=p.arrow(x+200,y+90,x+244,y+90)
        record={'id':ident,'before':before,'after':after,'symbols':sy,'grid_dimensions':[5,5],'black_value':1,'white_value':0,'arrow_direction':'left_to_right','intermediate_grids':0}
        box=[bb[0],min(b[1] for b in sb),ab[2],ab[3]]
        observations.append(record)
        elements.append(dict(id=record['id'],image=p.path.name,box=box,observed={k:v for k,v in record.items() if k!='id'},must_read=True,glyph_height_px=None,component_boxes={'before':bb,'after':ab,'symbols':sb,'arrow':arr}))
    # No operation string or starting bitmap is supplied for this legend.
    x,y=760,1480
    after,ab=p.grid(x,y);down=p.arrow(x+90,y+200,x+90,y+232)
    letter,hb,hh=p.text_at((x+55,y+240,x+125,y+280));bl=p.blank(x+90,y+298)
    legend={'id':'worked_H','after':after,'letter':letter,'grid_dimensions':[5,5],'black_value':1,'white_value':0,'extraction_arrow':'down to H','answer_blank_count':1}
    elements.append(dict(id=legend['id'],image=p.path.name,box=[ab[0],ab[1],ab[2],bl[3]],observed={k:v for k,v in legend.items() if k!='id'},must_read=True,glyph_height_px=hh,component_boxes={'after':ab,'arrow':down,'letter':hb,'blank':bl}))
    p=pages[1]
    for j in range(8):
        x=247+762*(j%2);y=416+360*(j//2)
        before,bb=p.grid(x,y);sy,sb=p.seals(x+222,y-57);arr=p.arrow(x+200,y+90,x+244,y+90)
        q,qb,hh=p.unknown(x+264,y);require(q=='?','Unknown output marker changed')
        blank=p.blank(x+354,y+222)
        record={'id':f'target_{j+1}','before':before,'symbols':sy,'grid_dimensions':[5,5],'black_value':1,'white_value':0,'arrow_direction':'left_to_right','intermediate_grids':0,'unknown_text':q,'answer_blank_count':1}
        targets.append(record)
        elements.append(dict(id=record['id'],image=p.path.name,box=[bb[0],min(b[1] for b in sb),x+446,blank[3]],observed={k:v for k,v in record.items() if k!='id'},must_read=True,glyph_height_px=hh,component_boxes={'before':bb,'symbols':sb,'arrow':arr,'unknown':qb,'blank':blank}))
    inventories=[p.finish() for p in pages]
    return {'examples':observations,'worked':legend,'targets':targets,'heading':{'title':pages[0].text[0]['text'],'lede':''},'elements':elements,'pages':inventories,'image_hashes':{p.path.name:p.hash for p in pages}}
