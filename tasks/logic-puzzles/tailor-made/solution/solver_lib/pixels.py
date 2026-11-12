"""PNG component extraction and independent single-character font recognition."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def components(ink):
    parent, boxes, prev = [], [], []
    def root(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for y, row in enumerate(ink):
        edge = np.diff(np.r_[False,row,False].astype('i1'))
        starts, ends = np.where(edge==1)[0],np.where(edge==-1)[0]
        cur=[];i=0
        for l,r in zip(starts,ends):
            n=len(parent);parent.append(n);boxes.append([int(l),y,int(r),y+1]);cur.append((l,r,n))
            while i<len(prev) and prev[i][1]<l:i+=1
            j=i
            while j<len(prev) and prev[j][0]<=r:
                parent[root(n)]=root(prev[j][2]);j+=1
        prev=cur
    out={}
    for i,b in enumerate(boxes):
        a=root(i)
        if a not in out:out[a]=b.copy()
        else:
            c=out[a];c[:]=[min(c[0],b[0]),min(c[1],b[1]),max(c[2],b[2]),max(c[3],b[3])]
    return list(out.values())


def tight(ink, box):
    x,y,r,b=map(int,box)
    yy,xx=np.where(ink[y:b,x:r])
    if not len(xx):raise ValueError('Blank text region: '+str(box))
    return [int(xx.min()+x),int(yy.min()+y),int(xx.max()+x+1),int(yy.max()+y+1)]


def normalized(a):
    return np.asarray(Image.fromarray(np.uint8(a)*255).resize((32,40),Image.Resampling.BILINEAR),dtype=float)/255


class Reader:
    def __init__(self, path):
        self.image=Image.open(path).convert('RGB')
        self.gray=np.asarray(self.image.convert('L'))
        self.ink=self.gray<128
        self.components=components(self.ink)
        self.templates={}
        self.reads=[]
    def template(self,char,size):
        key=char,size
        if key not in self.templates:
            font=ImageFont.truetype(str(Path(__file__).with_name('DejaVuSans.ttf')),size,layout_engine=ImageFont.Layout.BASIC)
            im=Image.new('L',(100,100));ImageDraw.Draw(im).text((20,20),char,font=font,fill=255)
            raw=np.asarray(im)>127
            yy,xx=np.where(raw);a=raw[yy.min():yy.max()+1,xx.min():xx.max()+1]
            self.templates[key]=(normalized(a),a.shape)
        return self.templates[key]
    def glyph(self,box,allowed,size):
        x,y,r,b=box;a=self.ink[y:b,x:r];n=normalized(a);scores=[]
        for c in allowed:
            t,shape=self.template(c,size)
            score=np.mean(abs(n-t))+0.025*abs(a.shape[1]-shape[1])+0.025*abs(a.shape[0]-shape[0])
            scores.append((score,c))
        scores.sort()
        if scores[0][0]>0.28:raise ValueError('Unrecognized glyph '+str(box)+' '+str(scores[:3]))
        if len(scores)>1 and scores[1][0]-scores[0][0]<0.015:raise ValueError('Ambiguous glyph '+str(box)+' '+str(scores[:3]))
        return scores[0]
    def read(self,name,region,allowed='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',size=34):
        x,y,r,b=region
        # Vertical projections join disconnected parts of one glyph (=, i)
        # without merging adjacent letters. Tight region contains text only.
        crop=self.ink[y:b,x:r]
        cols=crop.any(axis=0)
        ed=np.diff(np.r_[False,cols,False].astype('i1'))
        boxes=[tight(self.ink,[int(x+l),y,int(x+rr),b]) for l,rr in zip(np.where(ed==1)[0],np.where(ed==-1)[0])]
        if not boxes:raise ValueError('Missing text '+name)
        chars=[];scores=[]
        for box in boxes:
            score,char=self.glyph(box,allowed,size);chars.append(char);scores.append(float(score))
        box=[min(q[0] for q in boxes),min(q[1] for q in boxes),max(q[2] for q in boxes),max(q[3] for q in boxes)]
        caps=[q[3]-q[1] for c,q in zip(chars,boxes) if c.isupper() or c.isdigit()]
        item=dict(name=name,text=''.join(chars),box=box,glyph_height_px=min(caps) if caps else None,glyph_boxes=boxes,scores=scores)
        self.reads.append(item)
        return item['text']
