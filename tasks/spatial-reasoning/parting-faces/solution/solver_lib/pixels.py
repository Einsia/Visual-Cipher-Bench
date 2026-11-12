"""Read printed geometry and type from PNG pixels; constants are page layout only.
"""
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image, ImageDraw


def components(a):
    todo=set(zip(*np.nonzero(a)))
    out=[]
    while todo:
        start=todo.pop();q=[start];pts=[]
        while q:
            y,x=q.pop();pts.append((x,y))
            for d in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                if d in todo:todo.remove(d);q.append(d)
        if len(pts)>8:out.append(np.array(pts))
    return sorted(out,key=len,reverse=True)


def hull(pts):
    pts=sorted(set(map(tuple,pts)))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def half(seq):
        h=[]
        for p in seq:
            while len(h)>1 and cross(h[-2],h[-1],p)<=0:h.pop()
            h.append(p)
        return h
    return half(pts)[:-1]+half(pts[::-1])[:-1]


def outline_vertices(points,origin,unit):
    h=hull(points)
    while len(h)>3:
        errors=[]
        for j,b in enumerate(h):
            a=h[j-1];c=h[(j+1)%len(h)]
            errors.append(abs((c[0]-a[0])*(b[1]-a[1])-(c[1]-a[1])*(b[0]-a[0]))/max(1e-6,np.linalg.norm(np.subtract(c,a))))
        j=int(np.argmin(errors))
        if errors[j]>2.8:break
        h.pop(j)
    return [list(p) for p in hull([(round((x-origin[0])/unit),round((y-origin[1])/unit)) for x,y in h])]


def normalize(a):
    ys,xs=np.nonzero(a)
    if not len(xs):raise ValueError('Empty printed symbol')
    a=a[ys.min():ys.max()+1,xs.min():xs.max()+1]
    return np.array(Image.fromarray(a).resize((32,32),Image.Resampling.NEAREST))


def symbol_mask(family,turn):
    p=[(-.5,-.5),(-.15,-.5),(-.15,.15),(.5,.15),(.5,.5),(-.5,.5)] if family=='L' else [(-.5,-.5),(-.5,.5),(.5,.5)]
    for _ in range(turn):p=[(-y,x) for x,y in p]
    im=Image.new('1',(80,80));ImageDraw.Draw(im).polygon([(40+32*x,40+32*y) for x,y in p],fill=1)
    return normalize(np.asarray(im))


class Reader:
    def __init__(self,folder):
        self.pages={n:np.asarray(Image.open(Path(folder)/f'{n:02}.png').convert('L')) for n in [1,2,3]}
        assert all(a.shape==(2193,1700) for a in self.pages.values())
        self.atlas=np.load(Path(__file__).with_name('font_atlas.npz'))
        self.audit=[]
    def crop(self,page,box):
        x0,y0,x1,y1=map(int,box);return self.pages[page][y0:y1,x0:x1]
    def text(self,page,box,choices,mono=False,level='label'):
        a=normalize(self.crop(page,box)<100)
        scores=sorted((np.mean(a!=self.atlas[f'{int(mono)}_{level}_{ch}']),ch) for ch in choices)
        if scores[0][0]>.19 or (len(scores)>1 and scores[1][0]-scores[0][0]<.025):raise ValueError(('Ambiguous text',page,box,scores[:3]))
        self.audit.append({'kind':'text','page':page,'box':box,'value':scores[0][1],'error':scores[0][0]})
        return scores[0][1]
    def stamp(self,mask):
        a=normalize(mask)
        scores=sorted((np.mean(a!=symbol_mask(f,t)),f,t) for f in ['L','V'] for t in range(4))
        assert scores[0][0]<.15 and scores[1][0]-scores[0][0]>.08,scores
        return scores[0][1:]
    def card(self,page,origin,unit,box):
        x0,y0,x1,y1=box;a=self.crop(page,box)<100;cs=components(a)
        outline=cs[0];poly=outline_vertices(outline+[x0,y0],origin,unit)
        # Internal attached marks are the filled small disk and the larger stamp;
        # registration cross is outside the recovered convex polygon.
        inside=[]
        for c in cs[1:]:
            q=((c[:,0].mean()+x0-origin[0])/unit,(c[:,1].mean()+y0-origin[1])/unit)
            if all((b[0]-v[0])*(q[1]-v[1])-(b[1]-v[1])*(q[0]-v[0])>=-.1 for v,b in zip(poly,poly[1:]+poly[:1])):inside.append(c)
        assert len(inside)==2,(page,origin,[(len(c),c.mean(0).tolist()) for c in inside])
        stamp,dot=sorted(inside,key=len,reverse=True)
        mask=np.zeros(a.shape,bool);mask[stamp[:,1],stamp[:,0]]=True;family,turn=self.stamp(mask)
        center=(dot.mean(0)+[x0,y0]-origin)/unit;d=[int(round(v)) for v in center]
        stamp_center=(np.array([(stamp[:,0].min()+stamp[:,0].max()+1)/2,(stamp[:,1].min()+stamp[:,1].max()+1)/2])+[x0,y0]-origin)/unit
        # Marks use continuous placement; recover offset separately for drawing checks.
        offset=(stamp_center-np.array(d)).tolist()
        result={'polygon':poly,'dot':d,'family':family,'turn':turn,'stamp_offset':offset}
        self.audit.append({'kind':'card','page':page,'origin':origin,'value':result})
        return result
    def key(self):
        out=[]
        for j in range(8):
            y=400+78*j;family,turn=self.stamp(self.crop(1,(175,y-25,225,y+25))<100)
            letter=self.text(1,(296,y-18,332,y+18),list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),True,'body')
            count=int(self.text(1,(397,y-18,427,y+18),list('0123456789'),True,'body'))
            out.append({'family':family,'turn':turn,'letter':letter,'count':count})
        return out
    def angles(self,page,xs,y):
        return [int(self.text(page,(x-43,y-31,x+43,y+5),['0°','90°','180°','270°'],True,'body')[:-1])//90 for x in xs]
    def main(self,key):
        cards=[]
        for i in range(9):
            x=362+488*(i%3);y=458+346*(i//3)
            # Read each identity at its own cell; local coordinates use the 18 px unit.
            nx=x-174;ny=y-84
            identity=int(self.text(3,(nx-11,ny-12,nx+11,ny+13),list('123456789')))
            assert identity==i+1,('Template identity does not match its grid',identity,i+1)
            cx,cy=x-162,y+162
            assert np.all(self.crop(3,(cx-5,cy-1,cx+5,cy+1))<150)
            assert np.all(self.crop(3,(cx-1,cy-5,cx+1,cy+5))<150)
            self.audit.append({'kind':'registration','page':3,'identity':identity,'center':[cx,cy]})
            cards.append(dict(id=i+1,**self.card(3,(x,y),18,(x-151,y-149,x+201,y+151))))
        exit_labels=[self.text(3,(x-40,1340,x+40,1370),list('12345678')) for x in [366+140*j for j in range(8)]]
        assert exit_labels==list('12345678'),exit_labels
        qs=self.angles(3,[366+140*j for j in range(9)],1466)
        pair_tokens=[self.text(3,(x-20,1698,x+20,1736),['?']+list('0123456789'),False,'body') for x in [930,1030]]
        assert pair_tokens==['?','?'],('Expected two unknown checkpoints',pair_tokens)
        pair=[-1,-1]
        return {'cards':cards,'key':key,'readings':8,'starting_turns':{'slot_quarters':qs},'pair':pair}
    def example(self,key):
        cards=[]
        for i,(x,y) in enumerate([(850,505),(1338,505),(850,810),(1338,810)]):
            cards.append(dict(id=i+1,**self.card(1,(x,y),24,(x-130,y-130,x+130,y+130))))
        xs=[300,665,1030,1395];exits=[int(self.text(1,(x-11,1053,x+11,1079),list('1234')))-1 for x in xs]
        qslots=self.angles(1,xs,1125);qs=[None]*4
        for i,q in zip(exits,qslots):qs[i]=q
        stack=[int(self.text(1,(310+50*j,1836,336+50*j,1871),list('1234')))-1 for j in range(4)]
        return {'cards':cards,'key':key,'readings':3,'initial_quarters':qs,'stack':stack,'exit_order':exits}
    def footprint_input(self,spec,npoints=1000):
        import random
        rng=random.Random(451);pts=[];values=[];a=self.pages[3]
        # Sample only pixels whose entire neighborhood is a uniform region.
        # Gray/white boundaries and grid dots are excluded, never guessed.
        while len(pts)<npoints:
            p=[rng.uniform(-11.5,16.5),rng.uniform(-10.5,17.5)]
            x,y=[round(v) for v in (460+14*p[0],1715+14*p[1])]
            patch=a[y-2:y+3,x-2:x+3]
            if np.all(abs(patch.astype(int)-217)<3):v=1
            elif np.all(patch>=252):v=0
            else:continue
            pts.append(p);values.append(v)
        key={(k['family'],k['turn']):k for k in spec['key']}
        lines=[f"{len(spec['cards'])} {spec['readings']} {npoints}"]
        for c in spec['cards']:
            lines.append(str(len(c['polygon'])));lines+=[' '.join(map(str,p)) for p in c['polygon']];lines.append(' '.join(map(str,c['dot'])))
            lines.append(' '.join(f"{key[c['family'],(c['turn']+t)%4]['letter']} {key[c['family'],(c['turn']+t)%4]['count']}" for t in range(4)))
        lines+=[' '.join(map(str,p)) for p in pts];lines+=['1',' '.join(map(str,spec['pair'])),' '.join(map(str,values)),' '.join(map(str,spec['starting_turns']['slot_quarters']))]
        return '\n'.join(lines)+'\n'
