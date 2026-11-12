"""Read the page's spatial grammar. Numeric and letter content comes from PNG ink."""
from pathlib import Path
import numpy as np
from PIL import Image
from pixel_font import read
from model import evaluate, single_loop
from infer import infer_rule

class PixelError(ValueError): pass
def require(ok,msg):
    if not ok: raise PixelError(msg)

class Reader:
    def __init__(self,folder):
        self.images={n:Image.open(Path(folder)/n).convert('RGB') for n in ['01.png','02.png']}
        self.a={n:np.asarray(im.convert('L')) for n,im in self.images.items()}
        self.text=[];self.checks=[]
        for n,im in self.images.items():require(im.size==(1800,1800),'unexpected page geometry')
    def text_at(self,name,box,alphabet,family='DejaVuSansMono',size=34):
        box=list(map(int,box))
        cs=read(self.images[name],box,family,size,alphabet)
        require(bool(cs),f'missing text {name} {box}')
        require(all(c['error']<(.23 if c['char'].islower() else .19) for c in cs),f'unrecognized glyph {name} {box}: {cs}')
        require(all(c['height']>=20 for c in cs if c['char'].isdigit()or c['char'].isupper()or c['char']=='?'),f'undersized data glyph {name} {box}')
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
        positions=[(180,1220),(440,1220),(700,1220),(180,1430),(440,1430),(700,1430),(700,1640)]
        for i,(x,y) in enumerate(positions):
            a=self.a['01.png'];adj={};edges=[]
            for vertical in [False,True]:
                for r in range(4 if not vertical else 3):
                    for c in range(3 if not vertical else 4):
                        q=(x+32*c,y+32*r);z=(q[0]+(0 if vertical else 32),q[1]+(32 if vertical else 0))
                        mx,my=(q[0]+z[0])//2,(q[1]+z[1])//2
                        if a[my,mx]<128:
                            self.line('01.png',q,z);adj.setdefault(q,set()).add(z);adj.setdefault(z,set()).add(q);edges.append([q,z])
            deg=[len(v)for v in adj.values()];remaining=set(adj);components=0
            while remaining:
                components+=1;todo=[remaining.pop()]
                while todo:
                    for q in adj[todo.pop()]:
                        if q in remaining:remaining.remove(q);todo.append(q)
            if not deg:kind='empty'
            elif all(d==2 for d in deg):kind='simple'if components==1 else'disconnected'
            elif 4 in deg:kind='crossing'if 1 in deg else'touching'
            elif 3 in deg:kind='branch'
            else:kind='open'
            classifications.append({'kind':kind,'edges':edges,'box':[x,y,x+96,y+96]})
            if i==0:
                self.line('01.png',(x+120,y+45),(x+132,y+57));self.line('01.png',(x+132,y+57),(x+156,y+25))
            else:
                self.line('01.png',(x+120,y+30),(x+148,y+58));self.line('01.png',(x+120,y+58),(x+148,y+30))
        require([z['kind']for z in classifications]==['simple','empty','open','crossing','branch','touching','disconnected'],'inconsistent topology witnesses')
        return classifications
    def boundary(self,name,x,y,n,s):
        """Trace thick segments, then flood exterior cells across unblocked sides."""
        a=self.a[name];edges=set()
        for vertical in [False,True]:
            for r in range(n if vertical else n+1):
                for c in range(n+1 if vertical else n):
                    xx=x+c*s;yy=y+r*s
                    strip=(a[yy+4:yy+s-4,xx-2:xx+2] if vertical else a[yy-2:yy+2,xx+4:xx+s-4])<128
                    thickness=strip.sum(axis=1 if vertical else 0)
                    outer=c in [0,n] if vertical else r in [0,n]
                    support=2 if outer else 0
                    require(np.all(thickness==4)or np.all(thickness==support),f'broken or ambiguous edge {name} {x},{y} {r},{c}')
                    if np.all(thickness==4):
                        edge=((r,c),(r+1,c))if vertical else((r,c),(r,c+1))
                        edges.add(edge)
        outside={(-1,-1)};todo=[(-1,-1)]
        while todo:
            r,c=todo.pop()
            for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr,cc=r+dr,c+dc
                if not(-1<=rr<=n and -1<=cc<=n)or(rr,cc)in outside:continue
                edge=(((max(r,rr),c),(max(r,rr),c+1))if dr else((r,max(c,cc)),(r+1,max(c,cc))))
                if edge not in edges:outside.add((rr,cc));todo.append((rr,cc))
        masks=[sum(1<<c for c in range(n)if(r,c)not in outside)for r in range(n)]
        counts=[[sum(edge in edges for edge in [((r,c),(r,c+1)),((r+1,c),(r+1,c+1)),((r,c),(r+1,c)),((r,c+1),(r+1,c+1))])for c in range(n)]for r in range(n)]
        return masks,counts,sorted(edges)
    def grid(self,name,x,y,n=4,s=80,pairs=True,blank=False,framed_only=False):
        a=self.a[name];values=[];letters=[];masks=[];frames=[]
        for r in range(n):
            vr=[];lr=[];mask=0
            for c in range(n):
                xx=x+c*s;yy=y+r*s
                bg=int(np.median(a[yy+5:yy+9,xx+5:xx+9]));require(bg==255,f'cell membership must not be given by fill {name} {r},{c}')
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
                if framed_only and not framed:
                    lr.append(None)
                if not blank and (not framed_only or framed):
                    if pairs:
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
            masks.append(int(mask));values.append(vr);letters.append(lr)
        masks,counts,edges=self.boundary(name,x,y,n,s)
        # Recovered exterior connectivity must explain every drawn boundary edge.
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
        return {'values':values,'letters':letters,'masks':masks,'frames':frames,'edge_counts':counts,'edges':edges,'box':[x,y,x+n*s,y+n*s]}

def parse(folder):
    p=Reader(folder);legality=p.legality()
    def control(name,cx,cy):
        a=p.a[name]
        for theta in np.linspace(0,2*np.pi,80,endpoint=False):
            x=int(round(cx+26*np.cos(theta)));y=int(round(cy+26*np.sin(theta)))
            require((a[y-1:y+2,x-1:x+2]<128).any(),'missing control circle')
        return p.token(name,cx,cy)
    def labels(name,x,y,n,s):
        rows=[control(name,x-82,y+(i+.5)*s)for i in range(n)]
        cols=[control(name,x+(i+.5)*s,y-70)for i in range(n)]
        for i in range(n):
            p.line(name,(x-46,int(y+(i+.5)*s)),(x-13,int(y+(i+.5)*s)))
            p.line(name,(int(x+(i+.5)*s),y-34),(int(x+(i+.5)*s),y-13))
        return [v for rc in zip(rows,cols)for v in rc]
    def margins(name,x,y,n,s):
        rt=[int(p.text_at(name,[x+n*s+20,int(y+(r+.5)*s)-20,x+n*s+70,int(y+(r+.5)*s)+20],'0123456789')['text'])for r in range(n)]
        ct=[int(p.text_at(name,[int(x+(c+.5)*s)-26,y+n*s+20,int(x+(c+.5)*s)+26,y+n*s+55],'0123456789')['text'])for c in range(n)]
        return rt,ct
    def centered(name,x,y,alphabet='0123456789',mono=True,label=False,half=50):
        return p.text_at(name,[x-half,y-29,x+half,y+6],alphabet,'DejaVuSansMono'if mono else'DejaVuSans',28 if label else 34)['text']
    orig=p.grid('02.png',270,440,4,110,pairs=False)
    final=p.grid('02.png',1090,440,4,110,pairs=False,framed_only=True)
    # The letter-only parser refuses any extra digit ink on both boards.
    orig['values']=orig['edge_counts']
    orig['values_source']='incident thick edges reconstructed from PNG, not printed digits'
    final.pop('values')  # Missing values are latent, never supplied state.
    require(single_loop(orig['masks']),'calibration is not one simple loop')
    require(final['masks']==orig['masks'],'calibration boundary changes')
    seq=labels('02.png',270,440,4,110)
    require(sorted(seq)==list(range(1,9)),'example numbering invalid')
    order=sorted(range(8),key=lambda i:seq[i])
    word=centered('02.png',1310,1030,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',half=70)
    require(''.join(final['letters'][r][c]for r,c in final['frames'])==word,'reading order witness inconsistent')
    rt,ct=margins('02.png',1090,440,4,110)
    final['row_totals']=rt;final['column_totals']=ct
    require(centered('02.png',895,610,'0123456789–',False,True)=='1–8','example span missing')
    p.line('02.png',(750,660),(1035,660))
    local=[]
    for cx in [420,900,1380]:
        cy=1320;payload=p.pair('02.png',cx,cy);count=0
        sides=[((cx-40,cy-40),(cx+40,cy-40)),((cx+40,cy-40),(cx+40,cy+40)),
               ((cx-40,cy+40),(cx+40,cy+40)),((cx-40,cy-40),(cx-40,cy+40))]
        for (x,y),(u,v)in sides:
            mx,my=(x+u)//2,(y+v)//2
            sample=p.a['02.png'][my-2:my+2,mx]if y==v else p.a['02.png'][my,mx-2:mx+2]
            if np.count_nonzero(sample<128)==4:p.line('02.png',(x,y),(u,v));count+=1
        require(count==payload[0],'local boundary witness inconsistent')
        require(any(orig['letters'][r][c]==payload[1] and orig['edge_counts'][r][c]==count
                    for r in range(4)for c in range(4)),'local witness has no spatial source')
        local.append({'payload':payload,'incident_edges':count})
    induction=infer_rule(orig['masks'],orig['letters'],orig['edge_counts'],order,{8:final})
    # Only after unique inference do we reconstruct the unprinted digits.
    latent=induction['rule']['final_values']
    criteria=[v for v in range(5) if final['frames']==
              [[r,c]for r in range(4)for c in range(4)if latent[r][c]==v]]
    require(len(criteria)==1,'extraction digit criterion not uniquely recoverable')
    require(criteria[0]==3,'unsupported extraction criterion')
    sim=evaluate(orig['masks'],orig['letters'],order)
    require(sim['final']==latent and sim['row_totals']==rt and sim['column_totals']==ct,
            'independent replay contradicts recovered latent state')
    final['reconstructed_values']=latent
    final['values_source']='unique endpoint-only induction, no printed board digits'
    induction['extraction_digit']=criteria[0]
    target=p.grid('01.png',260,470,6,84,False);out=p.grid('01.png',1110,1090,6,84,False,True)
    require(not any(target['masks']+out['masks']),'extra fixed region in target')
    seq=labels('01.png',260,470,6,84);rt,ct=margins('01.png',1110,1090,6,84)
    require(seq.count(None)==4,'expected four erased action labels')
    require(centered('01.png',970,825,'0123456789–',False,True)=='1–12','target span missing')
    p.line('01.png',(835,785),(995,974))
    return {'letters':[''.join(r)for r in target['letters']],'row_totals':rt,'column_totals':ct,'labels':seq,'example':{'original':orig,'final':final,'order':order,'local_witnesses':local,'legality':legality,'word':word,'induction':induction},'text_regions':p.text}
