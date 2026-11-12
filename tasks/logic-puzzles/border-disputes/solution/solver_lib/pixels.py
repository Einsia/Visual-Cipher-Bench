"""Read the page's spatial grammar. Numeric and letter content comes from PNG ink."""
from pathlib import Path
import numpy as np
from PIL import Image
from pixel_font import read
from model import evaluate, single_loop

class PixelError(ValueError): pass
def require(ok,msg):
    if not ok: raise PixelError(msg)

class Reader:
    def __init__(self,folder):
        require(sorted(p.name for p in Path(folder).glob('*.png'))==['01.png'],'unexpected or stale puzzle page')
        self.images={n:Image.open(Path(folder)/n).convert('RGB') for n in ['01.png']}
        self.a={n:np.asarray(im.convert('L')) for n,im in self.images.items()}
        self.text=[];self.checks=[]
        for n,im in self.images.items():require(im.size==(1700,2193),'unexpected page geometry')
    def text_at(self,name,box,alphabet,family='DejaVuSansMono',size=34):
        cs=read(self.images[name],box,family,size,alphabet)
        require(bool(cs),f'missing text {name} {box}')
        require(all(c['error']<(.23 if c['char'].islower() else .19) for c in cs),f'unrecognized glyph {name} {box}: {cs}')
        require(all(c['height']>=19 for c in cs if c['char'].isdigit()or c['char'].isupper()or c['char']=='?'),f'undersized data glyph {name} {box}')
        b=[min(c['box'][0]for c in cs),min(c['box'][1]for c in cs),max(c['box'][2]for c in cs),max(c['box'][3]for c in cs)]
        z={'image':name,'box':b,'text':''.join(c['char']for c in cs),'glyphs':cs,'min_glyph_height_px':min(c['height']for c in cs)}
        self.text.append(z);return z
    def token(self,name,cx,cy,numeric=True):
        z=self.text_at(name,[cx-17,cy-13,cx+18,cy+13],'0123456789?' if numeric else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','DejaVuSans' if numeric else 'DejaVuSansMono',28 if numeric else 34)
        if not numeric:return z['text']
        require(z['text']=='?' or z['text'].isdigit(),'invalid numeric token')
        return None if z['text']=='?' else int(z['text'])
    def line(self,name,start,end,width=2):
        a=self.a[name];x,y=start;u,v=end
        l,t=min(x,u)-2,min(y,v)-2;rr,bb=max(x,u)+3,max(y,v)+3
        yy,xx=np.mgrid[t:bb,l:rr];dx,dy=u-x,v-y
        mask=(a[t:bb,l:rr]<128)&(abs(dy*(xx-x)-dx*(yy-y))<=1.7*(dx*dx+dy*dy)**.5)
        starts=list(zip(*np.where(mask&((xx-x)**2+(yy-y)**2<=4))))
        ends=set(zip(*np.where(mask&((xx-u)**2+(yy-v)**2<=4))))
        seen=set(starts);todo=starts[:]
        while todo:
            q=todo.pop()
            if q in ends:return
            for j in [-1,0,1]:
                for k in [-1,0,1]:
                    z=(q[0]+j,q[1]+k)
                    if 0<=z[0]<mask.shape[0] and 0<=z[1]<mask.shape[1] and mask[z] and z not in seen:seen.add(z);todo.append(z)
        raise PixelError(f'no continuous ink path {name} {start} {end}')
    def pair(self,name,cx,cy):
        a=self.text_at(name,[cx-23,cy-20,cx,cy+20],'01234')
        b=self.text_at(name,[cx,cy-20,cx+24,cy+20],'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        require(len(a['text'])==len(b['text'])==1,'bad strip pair')
        return [int(a['text']),b['text']]
    def legality(self):
        classifications=[]
        for i,(x,y) in enumerate([(136+204*i,1010)for i in range(7)]):
            a=self.a['01.png'];adj={};edges=[]
            for vertical in [False,True]:
                for r in range(4 if not vertical else 3):
                    for c in range(3 if not vertical else 4):
                        p=(x+40*c,y+40*r);q=(p[0]+(0 if vertical else 40),p[1]+(40 if vertical else 0))
                        mid=((p[0]+q[0])//2,(p[1]+q[1])//2)
                        if a[mid[1],mid[0]]<128:
                            self.line('01.png',p,q);adj.setdefault(p,set()).add(q);adj.setdefault(q,set()).add(p);edges.append([p,q])
            deg=[len(v)for v in adj.values()];remaining=set(adj);components=0
            while remaining:
                components+=1;todo=[remaining.pop()]
                while todo:
                    for q in adj[todo.pop()]:
                        if q in remaining:remaining.remove(q);todo.append(q)
            if not deg:kind='empty'
            elif all(d==2 for d in deg):kind='simple' if components==1 else 'disconnected'
            elif 4 in deg:kind='crossing' if 1 in deg else 'touching'
            elif 3 in deg:kind='branch'
            else:kind='open'
            classifications.append({'kind':kind,'edges':edges,'box':[x,y,x+120,y+120]})
            if i==0:
                self.line('01.png',(x+145,y+62),(x+157,y+74));self.line('01.png',(x+157,y+74),(x+182,y+44))
            else:
                self.line('01.png',(x+145,y+46),(x+173,y+74));self.line('01.png',(x+145,y+74),(x+173,y+46))
        require([z['kind']for z in classifications]==['simple','empty','open','crossing','branch','touching','disconnected'],'loop witnesses do not establish all required cases')
        return classifications
    def geometry(self,name,x,y,n,s):
        """Trace thick segments, flood from outside, then count incident sides.

        Cell fills, design specs, a stored example mask and answer data are never read.
        """
        a=self.a[name];h=[];v=[];edges=[]
        for vertical in [False,True]:
            result=[]
            for r in range(n if vertical else n+1):
                row=[]
                for c in range(n+1 if vertical else n):
                    xx=x+c*s;yy=y+r*s
                    sample=a[yy+s//2,xx-2:xx+2] if vertical else a[yy-2:yy+2,xx+s//2]
                    thick=int(np.count_nonzero(sample<128))==4
                    row.append(thick)
                    if thick:
                        p=(xx,yy);q=(xx if vertical else xx+s,yy+s if vertical else yy)
                        self.line(name,p,q)
                        edges.append([[r,c],[r+int(vertical),c+int(not vertical)]])
                result.append(row)
            if vertical:v=result
            else:h=result
        # One exterior node joins every unblocked perimeter side.
        outside=set();todo=[]
        def put(r,c):
            if (r,c)not in outside:outside.add((r,c));todo.append((r,c))
        for i in range(n):
            if not h[0][i]:put(0,i)
            if not h[n][i]:put(n-1,i)
            if not v[i][0]:put(i,0)
            if not v[i][n]:put(i,n-1)
        while todo:
            r,c=todo.pop()
            for rr,cc,blocked in [(r-1,c,h[r][c]),(r+1,c,h[r+1][c]),(r,c-1,v[r][c]),(r,c+1,v[r][c+1])]:
                if 0<=rr<n and 0<=cc<n and not blocked:put(rr,cc)
        masks=[sum(1<<c for c in range(n)if(r,c)not in outside)for r in range(n)]
        counts=[[sum([h[r][c],h[r+1][c],v[r][c],v[r][c+1]])for c in range(n)]for r in range(n)]
        return {'masks':masks,'counts':counts,'edges':edges,'method':'trace thick edges and flood from exterior; count four incident sides'}

    def margin_key(self):
        # Recover the closed region from PNG ink. The plus/minus strokes are
        # classified independently; no spec or stored membership is read.
        a=self.a['01.png'];crop=a[1140:1260,680:880]<128
        outside=set();todo=[]
        for r in range(crop.shape[0]):
            for c in [0,crop.shape[1]-1]:
                if not crop[r,c]:outside.add((r,c));todo.append((r,c))
        for c in range(crop.shape[1]):
            for r in [0,crop.shape[0]-1]:
                if not crop[r,c]:outside.add((r,c));todo.append((r,c))
        while todo:
            r,c=todo.pop()
            for rr,cc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if 0<=rr<crop.shape[0] and 0<=cc<crop.shape[1] and not crop[rr,cc] and (rr,cc)not in outside:
                    outside.add((rr,cc));todo.append((rr,cc))
        signs=[]
        for x,y in [(750,1200),(850,1200)]:
            self.line('01.png',(x-9,y),(x+9,y))
            vertical=bool(a[y-8,x]<128 and a[y+8,x]<128)
            if vertical:self.line('01.png',(x,y-9),(x,y+9))
            bounded=(y+15-1140,x+15-680)not in outside
            signs.append({'position':[x,y],'sign':1 if vertical else -1,'inside':bounded})
        require(sorted((v['inside'],v['sign'])for v in signs)==[(False,-1),(True,1)],'signed margin key does not assign + inside and minus outside')
        for p,q in [((700,1160),(800,1160)),((800,1160),(800,1240)),((800,1240),(700,1240)),((700,1240),(700,1160))]:self.line('01.png',p,q)
        require(self.text_at('01.png',[570,1185,645,1215],'sum','DejaVuSans',28)['text']=='sum','missing margin-key label')
        return {'signs':signs,'method':'PNG flood fill separates the sign positions; independent horizontal/vertical stroke classification'}

    def grid(self,name,x,y,n=4,s=80,pairs=True,blank=False,sparse=False):
        a=self.a[name];values=[];letters=[];frames=[]
        geometry=self.geometry(name,x,y,n,s);masks=geometry['masks']
        for r in range(n):
            vr=[];lr=[]
            for c in range(n):
                xx=x+c*s;yy=y+r*s
                bg=int(np.median(a[yy+5:yy+9,xx+5:xx+9]));require(bg==255,f'invalid cell background {name} {r},{c}')
                inner=a[yy+4:yy+s-4,xx+4:xx+s-4]<128
                allowed=np.zeros_like(inner)
                framed=(a[yy+s//2,xx+12]<128)
                if framed:
                    # Full frame, including both ends and all four segments.
                    for p,q in [((xx+12,yy+14),(xx+s-12,yy+14)),((xx+s-12,yy+14),(xx+s-12,yy+s-14)),((xx+s-12,yy+s-14),(xx+12,yy+s-14)),((xx+12,yy+s-14),(xx+12,yy+14))]:self.line(name,p,q)
                    frames.append([r,c])
                    for p,q in [(8,10),(s-16,10)]:allowed[8:s-16,p-2:p+3]=True
                    allowed[8:13,6:s-10]=True;allowed[s-21:s-16,6:s-10]=True
                cs=[]
                if not blank:
                    if sparse and not inner.any():
                        vr.append(None);lr.append(None)
                    elif pairs:
                        z1=self.text_at(name,[xx+18,yy+20,xx+40,yy+s-16],'01234')
                        z2=self.text_at(name,[xx+40,yy+20,xx+s-16,yy+s-16],'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                        require(len(z1['text'])==len(z2['text'])==1,'extra or missing cell glyph')
                        vr.append(int(z1['text']));lr.append(z2['text']);cs=z1['glyphs']+z2['glyphs']
                    else:
                        z=self.text_at(name,[xx+16,yy+20,xx+s-16,yy+s-16],'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                        require(len(z['text'])==1,'extra or missing letter');lr.append(z['text']);cs=z['glyphs']
                for g in cs:
                    l,t,u,v=g['box'];allowed[max(0,t-yy-5):min(s-8,v-yy-3),max(0,l-xx-5):min(s-8,u-xx-3)]=True
                require(not (inner&~allowed).any(),f'extra ink in semantic cell {name} grid {x},{y}, cell {r},{c}')
            values.append(vr);letters.append(lr)
        # Every full edge must agree with enclosure reconstructed from its geometry.
        for r in range(n+1):
            for c in range(n):
                inside1=(r>0 and bool(masks[r-1]>>c&1));inside2=(r<n and bool(masks[r]>>c&1))
                strip=a[y+r*s-2:y+r*s+2,x+c*s+4:x+(c+1)*s-4]<128
                expected=4 if inside1!=inside2 else (2 if r in [0,n] else 0)
                require(np.all(strip.sum(axis=0)==expected),f'wrong/broken horizontal edge {name} grid {x},{y}: {r},{c}')
        for r in range(n):
            for c in range(n+1):
                inside1=(c>0 and bool(masks[r]>>(c-1)&1));inside2=(c<n and bool(masks[r]>>c&1))
                strip=a[y+r*s+4:y+(r+1)*s-4,x+c*s-2:x+c*s+2]<128
                expected=4 if inside1!=inside2 else (2 if c in [0,n] else 0)
                require(np.all(strip.sum(axis=1)==expected),f'wrong/broken vertical edge {name} grid {x},{y}: {r},{c}')
        return {'values':values,'letters':letters,'masks':masks,'frames':frames,'box':[x,y,x+n*s,y+n*s],'geometry':geometry}

def parse(folder):
    p=Reader(folder)
    legality=p.legality()
    margin_key=p.margin_key()
    orig=p.grid('01.png',252,520,pairs=False)
    fifth=p.grid('01.png',684,520,sparse=True)
    final=p.grid('01.png',1156,520,sparse=True)
    require(single_loop(orig['masks']),'example boundary is not one simple loop')
    row=[p.token('01.png',170,560+80*r)for r in range(4)]
    col=[p.token('01.png',292+80*c,450)for c in range(4)]
    for r in range(4):p.line('01.png',(207,560+80*r),(235,560+80*r))
    for c in range(4):p.line('01.png',(292+80*c,485),(292+80*c,503))
    labels=[v for pair in zip(row,col)for v in pair]
    require(sorted(labels)==list(range(1,9)),'example order is not a permutation')
    order=sorted(range(8),key=lambda j:labels[j])
    for g in [fifth,final]:require(g['geometry']==orig['geometry'],'fixed boundary changed between snapshots')
    def margin(cx,cy,row=False):
        box=[cx-25,cy-20,cx+60,cy+20]if row else[cx-36,cy-20,cx+36,cy+20]
        return int(p.text_at('01.png',box,'0123456789−')['text'].replace('−','-'))
    er=[margin(1510,560+80*r,True)for r in range(4)]
    ec=[margin(1196+80*c,878)for c in range(4)]
    final['row_totals']=er;final['column_totals']=ec
    span1=p.text_at('01.png',[592,585,664,615],'0123456789–','DejaVuSans',28)['text']
    span2=p.text_at('01.png',[1044,585,1116,615],'0123456789–','DejaVuSans',28)['text']
    require(span1=='1–5' and span2=='6–8','example action ranges do not identify nonadjacent observations')
    from inference import infer
    witnesses={5:fifth,8:final}
    inferred=infer(orig,witnesses,order)
    require(inferred['unique_mechanism'],'sparse spatial observations do not distinguish the tested rule family')
    sim=evaluate(orig['masks'],orig['letters'],order)
    require(orig['geometry']['counts']==sim['counts'],'independent incident-edge counts disagree')
    reconstructed={}
    for step,g in witnesses.items():
        st=sim['states'][step]
        ls=[[orig['letters'][i//4][i%4]for i in rr]for rr in st['ids']]
        for r in range(4):
            for c in range(4):
                if g['values'][r][c] is not None:
                    require(g['values'][r][c]==st['values'][r][c] and g['letters'][r][c]==ls[r][c],f'observed pair at step {step} contradicts operation')
        reconstructed[str(step)]={'values':st['values'],'letters':ls}
    require(bool(final['frames']),'no extraction witness')
    selector={final['values'][r][c]for r,c in final['frames']}
    require(len(selector)==1 and None not in selector,'framed values do not agree')
    selector=next(iter(selector))
    require(final['frames']==[[r,c]for r in range(4)for c in range(4)if sim['final'][r][c]==selector],'frames do not select exactly one reconstructed value class')
    word=p.text_at('01.png',[1265,910,1368,950],'ABCDEFGHIJKLMNOPQRSTUVWXYZ')['text']
    extracted=''.join(final['letters'][r][c]for r,c in final['frames'])
    require(word==extracted,'framed cells in reading order disagree with printed word')
    require(er==sim['row_totals']and ec==sim['column_totals'],'example signed sums contradict reconstructed final state')
    candidates=[]
    for wi in [-1,0,1]:
        for wo in [-1,0,1]:
            z=[[v*(wi if orig['masks'][r]>>c&1 else wo)for c,v in enumerate(row)]for r,row in enumerate(sim['final'])]
            if list(map(sum,z))==er and list(map(sum,zip(*z)))==ec:candidates.append([wi,wo])
    require(candidates==[[1,-1]],'reconstructed worked final does not establish signed region sums')
    margin_key['coefficient_candidates']=candidates
    margin_key['tested_coefficient_pairs']=9
    target=p.grid('01.png',280,1410,6,82,False)
    out=p.grid('01.png',990,1410,6,82,False,True)
    require(not any(target['masks']+out['masks']),'target contains extra fixed region')
    rows=[p.token('01.png',188,1451+82*r)for r in range(6)]
    cols=[p.token('01.png',321+82*c,1332)for c in range(6)]
    rt=[margin(1528,1451+82*r,True)for r in range(6)]
    ct=[margin(1031+82*c,1940)for c in range(6)]
    for r in range(6):p.line('01.png',(233,1451+82*r),(263,1451+82*r))
    for c in range(6):p.line('01.png',(321+82*c,1378),(321+82*c,1397))
    p.line('01.png',(808,1616),(948,1616));p.line('01.png',(600,660),(651,660));p.line('01.png',(1032,650),(1123,650))
    span=p.text_at('01.png',[844,1560,919,1590],'0123456789–','DejaVuSans',28)['text']
    require(span=='1–12','target action span missing or inconsistent')
    return {'letters':[''.join(r)for r in target['letters']],'row_totals':rt,'column_totals':ct,'labels':[v for pair in zip(rows,cols)for v in pair],
            'selector':selector,'margin_key':margin_key,'inference':inferred,
            'example':{'original':orig,'after_five':fifth,'final':final,'reconstructed':reconstructed,'row_order':row,'column_order':col,'legality':legality},'text_regions':p.text}
