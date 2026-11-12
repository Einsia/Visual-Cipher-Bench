"""Full semantic-region structure checks; constants describe layout, not data."""
from collections import deque
import numpy as np
from PIL import Image

def components(mask):
    remaining = set(zip(*np.where(mask)))
    groups = []
    while remaining:
        seed = remaining.pop()
        q = deque([seed]); group = [seed]
        while q:
            y, x = q.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    p = (y+dy, x+dx)
                    if p in remaining:
                        remaining.remove(p); q.append(p); group.append(p)
        groups.append(group)
    return groups

def check(path, spec):
    a = np.asarray(Image.open(path).convert('RGB'))
    g = a.mean(axis=2); ink = g < 125
    def require(ok, reason):
        if not ok: raise ValueError(reason)
    def line(x1,y1,x2,y2):
        # Every cross-section must contain ink. No percentage/gap allowance.
        if y1 == y2:
            band = g[round(y1)-1:round(y1)+2,round(x1):round(x2)+1] < 210
            ok = band.any(axis=0).all()
            ok = ok and any(min(p[1] for p in group)==0 and max(p[1] for p in group)==band.shape[1]-1 for group in components(band))
        else:
            band = g[round(y1):round(y2)+1,round(x1)-1:round(x1)+2] < 210
            ok = band.any(axis=1).all()
            ok = ok and any(min(p[0] for p in group)==0 and max(p[0] for p in group)==band.shape[0]-1 for group in components(band))
        require(ok, 'discontinuous frame/grid segment '+str((x1,y1,x2,y2)))
    def arrow(box, direction, long=False):
        x1,y1,x2,y2=box; m=ink[y1:y2,x1:x2]
        groups=components(m)
        require(len(groups)==1, 'missing, extra or disconnected arrow '+str(box))
        ys,xs=np.where(m); w=int(xs.max()-xs.min()+1);h=int(ys.max()-ys.min()+1)
        major,minor=(w,h) if direction in 'EW' else (h,w)
        require((115<=major<=125 and 10<=minor<=16) if long else (22<=major<=28 and 5<=minor<=11), 'malformed arrow dimensions '+str((box,w,h)))
        mx=np.sum((xs-(xs.min()+xs.max())/2)**3);my=np.sum((ys-(ys.min()+ys.max())/2)**3)
        observed=('E' if mx>0 else 'W') if abs(mx)>abs(my) else ('S' if my>0 else 'N')
        require(observed==direction,'wrong arrowhead direction '+str(box))
        if long: require(8<=int(xs.min())<=10 and 129<=int(xs.max())<=131,'missing link endpoint')
        # A continuous shaft traverses the long axis and reaches the head.
        if direction in 'EW':
            require(m[:,xs.min():xs.max()+1].any(axis=0).all(),'broken arrow shaft')
        else:
            require(m[ys.min():ys.max()+1,:].any(axis=1).all(),'broken arrow shaft')
    def board(b,x,y,n,c):
        for j in range(n+1):
            line(x+j*c,y,x+j*c,y+n*c);line(x,y+j*c,x+n*c,y+j*c)
        bypos={(t['r'],t['c']):t for t in b['cells']}
        for r in range(n):
            for col in range(n):
                xx=round(x+col*c); yy=round(y+r*c)
                residual=ink[yy+4:yy+c-3,xx+4:xx+c-3].copy()
                covered=np.zeros_like(residual)
                def clear(bx):
                    x1,y1,x2,y2=bx
                    residual[max(0,y1-yy-4):max(0,y2-yy-4),max(0,x1-xx-4):max(0,x2-xx-4)]=False
                    covered[max(0,y1-yy-4):max(0,y2-yy-4),max(0,x1-xx-4):max(0,x2-xx-4)]=True
                t=bypos.get((r,col))
                if t:
                    for v in [(xx+8,yy+8,xx+c-8,yy+8),(xx+8,yy+c-8,xx+c-8,yy+c-8),(xx+8,yy+8,xx+8,yy+c-8),(xx+c-8,yy+8,xx+c-8,yy+c-8)]:line(*v)
                    for bx in [(xx+5,yy+5,xx+c-4,yy+11),(xx+5,yy+c-11,xx+c-4,yy+c-4),(xx+5,yy+5,xx+11,yy+c-4),(xx+c-11,yy+5,xx+c-4,yy+c-4)]:clear(bx)
                    clear((xx+21,yy+25,xx+54,yy+63))
                    ax=round(xx+c*.52);ay=yy+c-30
                    abox=(ax-17,ay-17,ax+18,ay+18)
                    arrow(abox,t['dir']);clear(abox)
                if [r,col]==b['token']:
                    cx=xx+c-28;cy=yy+28
                    ring=ink[cy-12:cy+13,cx-12:cx+13]
                    require(len(components(ring))==1,'missing or split visitor ring')
                    require(not ink[cy-4:cy+4,cx-4:cx+4].any(),'filled visitor ring')
                    # The ring must enclose its white center, not merely touch
                    # all angular sampling neighborhoods.
                    pending=deque([(12,12)]);seen={(12,12)}
                    while pending:
                        ry,rx=pending.popleft()
                        require(0<ry<24 and 0<rx<24,'open visitor ring')
                        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                            nxt=(ry+dy,rx+dx)
                            if nxt not in seen and not ring[nxt]:
                                seen.add(nxt);pending.append(nxt)
                    # Four cardinal sections and all angular sections exist.
                    for angle in np.linspace(0,2*np.pi,180,endpoint=False):
                        px=round(cx+9*np.cos(angle));py=round(cy+9*np.sin(angle))
                        require(ink[py-1:py+2,px-1:px+2].any(),'incomplete visitor ring')
                    clear((cx-12,cy-12,cx+13,cy+13))
                require(int(residual.sum())<=2,'extra or displaced semantic ink in cell '+str((x,y,r,col,int(residual.sum()))))
                background=g[yy+12:yy+c-12,xx+12:xx+c-12]
                free=~covered[8:c-16,8:c-16]
                tone=217 if t and t['visited'] else 255
                require(int((np.abs(background[free]-tone)>12).sum())<=2,'nonuniform or damaged card state '+str((x,y,r,col)))
    for i,(x1,x2,y,n,c) in enumerate([(260,1000,396,4,110),(292.5,1032.5,968,3,125)]):
        board(spec['examples'][i]['before'],x1,y,n,c)
        board(spec['examples'][i]['after'],x2,y,n,c)
        cy=round(y+n*c/2)
        arrow((780,cy-12,920,cy+13),'E',long=True)
    board(spec['target'],610,1475,4,120)
    count=sum(len(e[k]['cells']) for e in spec['examples'] for k in ('before','after'))+len(spec['target']['cells'])
    return {'continuous_grid_and_card_frames':True,'complete_arrows':count+2,'visitor_rings':5,'all_cell_interiors_checked_for_extra_ink':True}
