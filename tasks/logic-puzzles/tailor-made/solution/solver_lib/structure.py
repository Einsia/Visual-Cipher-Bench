"""Check full strokes, arrowheads, frames, and unaccounted-for ink.

geometry.json is a calibrated coordinate sampling plan, not pixel evidence.
Every segment is checked against the supplied PNG, including its interior.
No dilation/closing is applied to input ink: a missing cross section fails.
"""
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def check_structure(reader, fields):
    strokes=json.loads(Path(__file__).with_name('geometry.json').read_text())
    ink=reader.gray<210
    # Cell divisions and chosen partition cuts are different semantic marks.
    # An added black cut exactly on a gray grid line must not disappear into
    # the coordinate-tolerance mask used below.
    gray_dividers=[(x,y,y+56) for y in [1700,1880] for x in range(292,1488,92)]
    gray_dividers += [(380,515,581),(490,515,581),(1140,515,581)]
    for x,y,b in gray_dividers:
        if (reader.gray[y+4:b-4,x-2:x+3]<128).any():raise ValueError(f'Extra partition cut on gray cell boundary {x},{y}')
    for x,y,b in [(600,515,581),(1250,515,581)]:
        rows=(reader.gray[y+4:b-4,x-3:x+4]<128).sum(axis=1)
        if (rows<3).any():raise ValueError(f'Missing thick example partition cut {x},{y}')
    allowed=Image.new('1',reader.image.size)
    draw=ImageDraw.Draw(allowed)
    for n,s in enumerate(strokes):
        x,y,r,b=s['line'];dx,dy=r-x,b-y
        width=s['width'];rad=max(1,int(math.ceil(width/2)))
        if abs(dx)>=abs(dy):
            xx=np.arange(math.ceil(min(x,r)),math.floor(max(x,r))+1,dtype=int)
            yy=y+(xx-x)*dy/dx if dx else np.full_like(xx,y)
            center=np.floor(yy).astype(int)
            hits=np.stack([ink[center+d,xx] for d in range(-rad,rad+2)]).any(axis=0)
            slices=[{int(c+d) for d in range(-rad,rad+2) if ink[c+d,p]} for p,c in zip(xx,center)]
        else:
            yy=np.arange(math.ceil(min(y,b)),math.floor(max(y,b))+1,dtype=int)
            xx=x+(yy-y)*dx/dy
            center=np.floor(xx).astype(int)
            hits=np.stack([ink[yy,center+d] for d in range(-rad,rad+2)]).any(axis=0)
            slices=[{int(c+d) for d in range(-rad,rad+2) if ink[p,c+d]} for p,c in zip(yy,center)]
        if not hits.all():
            raise ValueError(f'Broken or missing stroke {n}: {s["line"]}; missing cross-sections {np.flatnonzero(~hits).tolist()}')
        reachable=slices[0]
        for candidates in slices[1:]:
            nxt={q for q in candidates if any(abs(q-p)<=1 for p in reachable)}
            while True:
                expanded=nxt|{q for q in candidates if q-1 in nxt or q+1 in nxt}
                if expanded==nxt:break
                nxt=expanded
            if not nxt:raise ValueError(f'Disconnected pixel path in stroke {n}')
            reachable=nxt
        draw.line([(x,y),(r,b)],fill=1,width=int(math.ceil(width+5)))
        for px,py in [(x,y),(r,b)]:draw.rectangle((px-3,py-3,px+3,py+3),fill=1)
        if 'arrow' in s:
            angle=math.atan2(dy,dx);head=s['arrow']
            pts=[(r,b)]+[(r-head*math.cos(angle+q*.42),b-head*math.sin(angle+q*.42)) for q in [1,-1]]
            # Interior barycentric samples check BOTH wings, not just the tip.
            for u,v in [(0.45,0.45),(0.65,0.15),(0.15,0.65)]:
                px=(1-u-v)*pts[0][0]+u*pts[1][0]+v*pts[2][0]
                py=(1-u-v)*pts[0][1]+u*pts[1][1]+v*pts[2][1]
                cx,cy=round(px),round(py)
                if not ink[cy-1:cy+2,cx-1:cx+2].any():raise ValueError(f'Missing arrow wing {n}')
            draw.polygon(pts,fill=1);draw.line(pts+[pts[0]],fill=1,width=4)
    for f in fields:draw.rectangle(f['region'],fill=1)
    # Editorial heading is not used as numeric data and is never used to
    # look up an answer.
    draw.rectangle((130,125,1320,268),fill=1)
    # Question-mark glyph, inside the independently checked square.
    val=reader.read('question_mark',(143,1242,177,1278),'?',28)
    if val!='?':raise ValueError('Unknown marker missing')
    draw.rectangle((143,1242,177,1278),fill=1)
    extra=ink & ~np.asarray(allowed,dtype=bool)
    if extra.any():
        yy,xx=np.where(extra)
        raise ValueError(f'Unexpected graphic or symbol: {len(xx)} pixels; box {[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]}')
    # Verify exact one-row inventory and all output frames. Erasure of a
    # complete frame fails the stroke pass, even if its center stays blank.
    return dict(complete_strokes=len(strokes),arrowheads=sum('arrow' in s for s in strokes),
                extra_ink_pixels=0,output_frames=15,output_arrows=14,
                gray_cell_dividers=len(gray_dividers),thick_example_cuts=2)
