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
        self.images={n:Image.open(Path(folder)/n).convert('RGB') for n in ['01.png','02.png']}
        self.a={n:np.asarray(im.convert('L')) for n,im in self.images.items()}
        self.text=[];self.checks=[]
        for n,im in self.images.items():require(im.size==(2400,1600),'unexpected page geometry')
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
        for i,(x,y) in enumerate([(140+310*i,1430) for i in range(7)]):
            a=self.a['02.png'];adj={};edges=[]
            for vertical in [False,True]:
                for r in range(4 if not vertical else 3):
                    for c in range(3 if not vertical else 4):
                        p=(x+30*c,y+30*r);q=(p[0]+(0 if vertical else 30),p[1]+(30 if vertical else 0))
                        mid=((p[0]+q[0])//2,(p[1]+q[1])//2)
                        if a[mid[1],mid[0]]<128:
                            self.line('02.png',p,q);adj.setdefault(p,set()).add(q);adj.setdefault(q,set()).add(p);edges.append([p,q])
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
            classifications.append({'kind':kind,'edges':edges,'box':[x,y,x+90,y+90]})
            if i==0:
                self.line('02.png',(x+115,y+45),(x+127,y+57));self.line('02.png',(x+127,y+57),(x+152,y+27))
            else:
                self.line('02.png',(x+115,y+31),(x+143,y+59));self.line('02.png',(x+115,y+59),(x+143,y+31))
        require([z['kind']for z in classifications]==['simple','empty','open','crossing','branch','touching','disconnected'],'loop witnesses do not establish all required cases')
        return classifications
    def grid(self,name,x,y,n=4,s=80,pairs=True,blank=False):
        a=self.a[name];values=[];letters=[];frames=[]
        # Read boundary strokes first, independently of any cell fill or numbers.
        horizontal=[];vertical=[]
        for rr in range(n+1):
            row=[]
            for cc in range(n):
                strip=a[y+rr*s-2:y+rr*s+2,x+cc*s+4:x+(cc+1)*s-4]<128
                widths=strip.sum(axis=0)
                require(np.all(widths==widths[0]),'broken horizontal boundary')
                require(int(widths[0]) in ([2,4] if rr in [0,n] else [0,4]),'invalid horizontal stroke')
                row.append(int(widths[0])==4)
            horizontal.append(row)
        for rr in range(n):
            row=[]
            for cc in range(n+1):
                strip=a[y+rr*s+4:y+(rr+1)*s-4,x+cc*s-2:x+cc*s+2]<128
                widths=strip.sum(axis=1)
                require(np.all(widths==widths[0]),'broken vertical boundary')
                require(int(widths[0]) in ([2,4] if cc in [0,n] else [0,4]),'invalid vertical stroke')
                row.append(int(widths[0])==4)
            vertical.append(row)
        exterior=set();todo=[]
        for rr in range(n):
            for cc in range(n):
                if (rr==0 and not horizontal[0][cc]) or (rr==n-1 and not horizontal[n][cc]) or (cc==0 and not vertical[rr][0]) or (cc==n-1 and not vertical[rr][n]):
                    exterior.add((rr,cc));todo.append((rr,cc))
        while todo:
            rr,cc=todo.pop()
            for nr,nc,wall in [(rr-1,cc,horizontal[rr][cc]),(rr+1,cc,horizontal[rr+1][cc]),(rr,cc-1,vertical[rr][cc]),(rr,cc+1,vertical[rr][cc+1])]:
                if not wall and 0<=nr<n and 0<=nc<n and (nr,nc) not in exterior:
                    exterior.add((nr,nc));todo.append((nr,nc))
        masks=[sum(1<<cc for cc in range(n) if (rr,cc) not in exterior) for rr in range(n)]
        for r in range(n):
            vr=[];lr=[]
            for c in range(n):
                xx=x+c*s;yy=y+r*s
                bg=int(np.median(a[yy+5:yy+9,xx+5:xx+9]));require(bg==255,f'redundant region shading {name} {r},{c}')
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
            values.append(vr);letters.append(lr)
        # Every edge must agree with the spatially recovered interior.
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
        return {'values':values,'letters':letters,'masks':masks,'frames':frames,'box':[x,y,x+n*s,y+n*s],'membership_source':'boundary flood fill'}

def parse(folder):
    p=Reader(folder);legality=p.legality()
    orig=p.grid('02.png',240,350);after=p.grid('02.png',820,350);final=p.grid('02.png',1500,350)
    require(single_loop(orig['masks']),'example boundary is not one simple loop')
    rows=[p.token('02.png',158,390+80*r)for r in range(4)]
    cols=[p.token('02.png',280+80*c,280)for c in range(4)]
    example_rows=rows[:];example_cols=cols[:]
    labels=[v for pair in zip(rows,cols)for v in pair]
    require(sorted(labels)==list(range(1,9)),'example order invalid')
    order=sorted(range(8),key=lambda j:labels[j]);sim=evaluate(orig['masks'],orig['letters'],order)
    def agree(g,step):
        st=sim['states'][step];ls=[[orig['letters'][i//4][i%4]for i in rr]for rr in st['ids']]
        require(g['masks']==orig['masks'] and g['values']==st['values'] and g['letters']==ls,f'example state {step} contradicts operation')
    require(orig['values']==sim['counts'],'side counts contradict boundary')
    agree(after,1);agree(final,8)
    before6=p.grid('02.png',820,1020);after6=p.grid('02.png',1500,1020);agree(before6,5);agree(after6,6)
    require(orig['frames']==list(map(list,sim['steps'][0]['sampled_cells'])),'first sampled cells differ')
    require(before6['frames']==list(map(list,sim['steps'][5]['sampled_cells'])),'later sampled cells differ')
    def mono(name,cx,baseline,alphabet='0123456789',half=32):
        return p.text_at(name,[cx-half,baseline-29,cx+half,baseline+5],alphabet)['text']
    require(p.token('02.png',680,425)==1 and p.token('02.png',1310,1060)==6,'action labels missing')
    require(int(mono('02.png',680,565))==sim['steps'][0]['sum'],'first sum wrong')
    require(int(mono('02.png',1310,1145))==sim['steps'][5]['sum'],'later sum wrong')
    p.line('02.png',(612,510),(741,510));p.line('02.png',(1310,1172),(1310,1230))
    for r in range(4):p.line('02.png',(200,390+80*r),(226,390+80*r))
    for c in range(4):p.line('02.png',(280+80*c,322),(280+80*c,336))
    er=[int(mono('02.png',1864,402+80*r))for r in range(4)]
    ec=[int(mono('02.png',1540+80*c,719))for c in range(4)]
    require(er==sim['row_totals'] and ec==sim['column_totals'],'example margins wrong')
    require(final['frames']==[[r,c]for r in range(4)for c in range(4)if final['values'][r][c]==3],'selector frames wrong')
    require(p.text_at('02.png',[2032,400,2068,430],'01234','DejaVuSans',28)['text']=='3','selector missing')
    word=mono('02.png',2050,565,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',half=50)
    require(word==sim['answer'],'extraction sample wrong')
    p.line('02.png',(2050,452),(2050,502))
    endpoints=[]
    for x in [1090]:
        a=p.pair('02.png',x+35,830);b=p.pair('02.png',x+155,830)
        bg1=int(p.a['02.png'][800,x+10]);bg2=int(p.a['02.png'][800,x+130])
        require(bg1 in [238,255]and bg2 in[238,255],'endpoint backgrounds missing')
        require(a[1]==b[1]and b[0]==(a[0]if bg1==bg2 else 4-a[0]),'complement witness wrong')
        p.line('02.png',(x+84,830),(x+102,830));endpoints.append([a,b,bg1,bg2])
    from infer import infer_rules
    rule_evidence=infer_rules(orig,after,before6,after6,final,labels,endpoints)
    for cx,(r,c)in zip([520,1140,1760],[(0,0),(0,2),(2,2)]):
        pair=p.pair('01.png',cx,1430);require(pair==[orig['values'][r][c],orig['letters'][r][c]],'local observation wrong')
        sides=[((cx-40,1390),(cx+40,1390)),((cx+40,1390),(cx+40,1470)),((cx-40,1470),(cx+40,1470)),((cx-40,1390),(cx-40,1470))];count=0
        for (x,y),(u,v)in sides:
            mx,my=(x+u)//2,(y+v)//2
            ink=p.a['01.png'][my-2:my+2,mx]if y==v else p.a['01.png'][my,mx-2:mx+2]
            if np.count_nonzero(ink<128)==4:p.line('01.png',(x,y),(u,v));count+=1
        require(count==pair[0],'local edge incidence wrong')
    target=p.grid('01.png',420,510,6,100,False);out=p.grid('01.png',1510,510,6,100,False,True)
    require(not any(target['masks']+out['masks']),'target leaks fixed region')
    rows=[p.token('01.png',338,560+100*r)for r in range(6)]
    cols=[p.token('01.png',470+100*c,440)for c in range(6)]
    for r in range(6):p.line('01.png',(380,560+100*r),(406,560+100*r))
    for c in range(6):p.line('01.png',(470+100*c,482),(470+100*c,496))
    rt=[int(mono('01.png',2154,572+100*r))for r in range(6)]
    ct=[int(mono('01.png',1560+100*c,1159))for c in range(6)]
    require(p.text_at('01.png',[1215,735,1295,765],'0123456789–','DejaVuSans',28)['text']=='1–12','action span missing')
    require(p.text_at('02.png',[1275,430,1345,460],'0123456789–','DejaVuSans',28)['text']=='2–8','example span missing')
    p.line('01.png',(1122,810),(1375,810));p.line('02.png',(1202,510),(1410,510))
    return {'letters':[''.join(r)for r in target['letters']],'row_totals':rt,'column_totals':ct,'labels':[v for pair in zip(rows,cols)for v in pair],'example':{'original':orig,'final':final,'row_order':example_rows,'column_order':example_cols,'endpoints':endpoints,'legality':legality,'answer':word},'text_regions':p.text,'rule_inference':rule_evidence}
