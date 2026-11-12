"""Recover the notebook's data from raster ink; no puzzle values in this module.
Fixed coordinates describe the page grammar. glyphs.npz contains single glyphs
and only non-data headings, never full records, queues, pairs or answers.
"""
from pathlib import Path
import numpy as np
from PIL import Image

class PixelError(ValueError): pass

def need(ok,msg):
    if not ok: raise PixelError(msg)

def bbox(m):
    ys,xs=np.where(m)
    need(len(xs)>0,'missing glyph')
    return [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]

def norm(m):
    l,t,r,b=bbox(m)
    return np.array(Image.fromarray(m[t:b,l:r].astype('uint8')*255).resize((24,36),Image.Resampling.NEAREST))>127

class Reader:
    def __init__(self,path):
        im=Image.open(path)
        need(im.size==(1700,2193),'wrong page dimensions')
        need(im.mode in ('RGB','RGBA'),'not RGB/RGBA')
        need(not any(k.lower() in ('exif','comment','text','description') for k in im.info),'unexpected image metadata')
        a=np.array(im.convert('RGB'));need(int(np.max(a.max(2)-a.min(2)))==0,'unexpected coloured pixels')
        self.a=a[:,:,0];self.ink=self.a<128;self.used=np.zeros(self.a.shape,bool)
        self.lib=dict(np.load(Path(__file__).with_name('glyphs.npz')))
        self.regions=[];self.metrics=[];self.structures=[]
    def mark(self,box):
        l,t,r,b=map(int,box);self.used[t:b,l:r]=True
    def line(self,x1,y1,x2,y2,threshold=200):
        # Check every location, not just endpoints; a one-pixel transverse cut fails.
        if x1==x2:
            band=self.a[y1:y2+1,x1-1:x1+2]<threshold
            need(np.all(self.a[y1:y2+1,x1]<threshold),f'broken vertical line {(x1,y1,x2,y2)}')
            self.mark((x1-3,y1-3,x1+4,y2+4))
        else:
            band=self.a[y1-1:y1+2,x1:x2+1]<threshold
            need(np.all(self.a[y1,x1:x2+1]<threshold),f'broken horizontal line {(x1,y1,x2,y2)}')
            self.mark((x1-3,y1-3,x2+4,y1+4))
        self.structures.append([x1,y1,x2,y2])
    def rect(self,l,t,r,b,threshold=200):
        self.line(l,t,r,t,threshold);self.line(l,b,r,b,threshold)
        self.line(l,t,l,b,threshold);self.line(r,t,r,b,threshold)
    def fixed(self,key,box,text,role='label',cap=20):
        l,t,r,b=box;m=self.ink[t:b,l:r];sample=self.lib['label_'+key]
        need(m.shape==sample.shape and np.array_equal(m,sample),f'missing/altered heading or label {text}')
        z=bbox(m);self.mark(box)
        self.regions.append(dict(role=role,text=text,box=[l+z[0],t+z[1],l+z[2],t+z[3]],min_glyph_height_px=cap))
    def text(self,box,alphabet,small=False,role='clue'):
        l,t,r,b=map(int,box);a=self.a[t:b,l:r];bg=int(np.median(a))
        need(min(abs(bg-c) for c in (255,217,238))<=2,f'unknown cell fill in {box}')
        m=a<(bg+17)/2
        cols=m.any(0);runs=[];start=None
        for k,v in enumerate(list(cols)+[False]):
            if v and start is None:start=k
            if not v and start is not None:runs.append((start,k));start=None
        chars=[];glyphs=[]
        for x1,x2 in runs:
            g=m[:,x1:x2];gl,gt,gr,gb=bbox(g);g=g[gt:gb,gl:gr]
            scored=[]
            for ch in alphabet:
                sample=self.lib[('small_' if small else 'glyph_')+(ch if small else str(ord(ch)))].astype(bool)
                # Shape, aspect ratio and native size all matter.
                score=float(np.mean(norm(g)!=norm(sample)))
                score+=.3*abs(g.shape[1]/g.shape[0]-sample.shape[1]/sample.shape[0])
                score+=.15*abs(g.shape[0]-sample.shape[0])/sample.shape[0]
                scored.append((score,ch))
            scored.sort();score,ch=scored[0]
            need(score<.13,f'unrecognised or damaged glyph at {[l+x1,t+gt]} best={scored[:2]}')
            need(len(scored)==1 or scored[1][0]-score>.045,f'ambiguous glyph at {[l+x1,t+gt]}')
            chars.append(ch);glyphs.append(dict(char=ch,box=[l+x1+gl,t+gt,l+x1+gr,t+gb],height_px=gb-gt,score=score))
        # Uniform fill except in the antialiasing neighbourhood of actual glyphs.
        padded=np.pad(m,2); near=np.zeros_like(m)
        for dy in range(5):
            for dx in range(5):near |= padded[dy:dy+m.shape[0],dx:dx+m.shape[1]]
        need(not np.any((np.abs(a.astype(int)-bg)>4)&~near),f'incomplete fill or extra pale mark in {box}')
        self.mark(box)
        text=''.join(chars)
        if glyphs:
            bs=[g['box'] for g in glyphs];tb=[min(v[0] for v in bs),min(v[1] for v in bs),max(v[2] for v in bs),max(v[3] for v in bs)]
            heights=[g['height_px'] for g in glyphs if g['char'].isalnum()] or [g['height_px'] for g in glyphs]
            self.regions.append(dict(role=role,text=text,box=tb,min_glyph_height_px=min(heights)))
            self.metrics.extend(glyphs)
        return text,bg
    def arrow(self,cx,y1,y2,half):
        self.line(cx,y1,cx,y2-2,128)
        # Verify full downward triangular arrowhead, including both wings.
        tip=y2;top=y2-14
        # Native two arrow sizes: small heads are 12 px high; large 16 px.
        h=12 if half==5 else 16;top=y2-h
        for dy in range(2,h-1):
            width=max(1,int(half*(1-dy/h)))
            need(np.all(self.ink[top+dy,cx-width:cx+width]),f'missing arrow head {cx,y1,y2}')
        self.mark((cx-half-2,y1-2,cx+half+3,y2+3))
    def state(self,y,pair_count,queue_count,active):
        pairs=[];boxed=[];alphabet='ABCDEFNIRST'
        for k in range(pair_count):
            x=176+80*k;letters=[]
            for cy in (y-56,y+56):
                txt,bg=self.text((x-24,cy-26,x+25,cy+27),alphabet)
                need(len(txt)==1,f'pair letter missing/extra at {x,cy}')
                letters.append(txt)
                area=self.ink[cy-34:cy+35,x-32:x+33].copy()
                area[8:-8,8:-8]=False
                if area.any():
                    self.rect(x-28,cy-30,x+28,cy+30,128);boxed.append(txt)
            pairs.append(''.join(letters));self.line(x,y-16,x,y+15,128)
        letters=''.join(pairs)
        need(len(set(letters))==len(letters),'pair identities are not distinct')
        queue=[]
        for k in range(queue_count):
            l=506+96*k;t=y-34
            self.rect(l,t,l+96,t+68,200)
            s,bg=self.text((l+4,t+4,l+92,t+64),'12345678,')
            if active:
                need(len(s)==3 and s[1]==',' and s[0]!=s[2],f'invalid request {s}')
                queue.append([int(s[0]),int(s[2])])
                need(bg==(217 if k==0 else 255),'queue active fill incorrect')
            else:need(s=='' and bg==238,'completed queue not empty')
        if active:self.arrow(554,y-74,y-44,5)
        record=[];indices=[];shaded=[]
        for k in range(8):
            l=1132+54*k
            s,_=self.text((l+4,y-76,l+50,y-38),'12345678',small=True,role='label')
            need(len(s)==1,'missing/extra position index');indices.append(int(s))
            self.rect(l,y-32,l+54,y+32,128)
            s,bg=self.text((l+4,y-28,l+50,y+28),alphabet)
            need(len(s)==1,f'missing/extra Record letter {k+1,y}');record.append(s)
            if bg==217:shaded.append(k+1)
            else:need(bg==255,'unknown Record shading')
        need(indices==list(range(1,9)),'position order is not consecutive left-to-right')
        need(set(record)<=set(letters),'Record identity absent from Pairs')
        if active:
            need(shaded==sorted(queue[0]),'shading does not identify queue head')
            need(set(boxed)=={record[i-1] for i in queue[0]},'boxed identities disagree with addressed Record')
        else:need(not boxed and not shaded,'final state has active selection')
        return dict(pairs=sorted(''.join(sorted(p)) for p in pairs),queue=queue,record=''.join(record))
    def read(self):
        self.fixed('title',(138,130,775,199),'Notebook Society','heading',47)
        self.fixed('lede',(137,225,1118,259),'The characters in this notebook lead eventful social lives.','heading',24)
        for off in (0,540,1050):
            for key,box in [('Pairs',(262,306,331,335)),('Queue',(747,306,841,337)),('Record',(1299,306,1398,334))]:
                l,t,r,b=box;self.fixed(key,(l,t+off,r,b+off),key,cap=20 if key!='Queue' else 24)
        s=[self.state(y,n,q,active) for y,n,q,active in [(466,3,4,True),(706,3,4,False),(976,3,4,True),(1216,3,4,False),(1496,4,6,True)]]
        for y in (826,1336):self.line(136,y,1563,y,200)
        self.arrow(794,568,604,6);self.arrow(794,1078,1114,6);self.arrow(794,1570,1624,6)
        for k in range(6):
            l=506+96*k;self.rect(l,1696,l+96,1764,200)
            txt,bg=self.text((l+4,1700,l+92,1760),'12345678,');need(txt=='' and bg==238,'target queue endpoint not empty')
        self.fixed('Final record',(1132,1619,1333,1652),'Final record',cap=25)
        for k in range(8):
            l=1132+54*k;self.rect(l,1703,l+54,1757,128)
            txt,_=self.text((l+4,1707,l+50,1753),'?',role='label');need(txt=='?','missing/extra unknown cell')
        extra=self.ink&~self.used
        need(not extra.any(),f'extra unparsed ink: {bbox(extra) if extra.any() else None}')
        return dict(episodes=[dict(initial=s[0],final=s[1]),dict(initial=s[2],final=s[3])],target=s[4],text_regions=self.regions,glyphs=self.metrics,structural_lines=len(self.structures))

def read(path):return Reader(path).read()
