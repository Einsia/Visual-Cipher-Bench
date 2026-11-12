"""Recover anonymous line directions and aim marks from PNG crops."""
import numpy as np
from .parser import OCR,require
from .inverse_camera import cluster_slopes


def contours(mask):
    # Directed unit lattice edges around filled raster regions. Keeping the
    # material on the left gives closed cycles, including hole boundaries.
    padded=np.pad(mask,1)
    edges={}
    def add(yy,xx,start,end):
        for y,x in zip(yy,xx):
            a=(int(x+start[0]),int(y+start[1]));b=(int(x+end[0]),int(y+end[1]))
            edges.setdefault(a,[]).append(b)
    add(*np.nonzero(mask&~padded[:-2,1:-1]),(0,0),(1,0))
    add(*np.nonzero(mask&~padded[1:-1,2:]),(1,0),(1,1))
    add(*np.nonzero(mask&~padded[2:,1:-1]),(1,1),(0,1))
    add(*np.nonzero(mask&~padded[1:-1,:-2]),(0,1),(0,0))
    result=[]
    while edges:
        start=next(iter(edges));path=[start];p=start
        while p in edges:
            q=edges[p].pop()
            if not edges[p]:del edges[p]
            path.append(q);p=q
            if p==start:break
        if len(path)>25 and path[-1]==start:result.append(np.array(path,dtype=float))
    return result


def read_lines(crop):
    lines=[]
    for mask in [crop>240,(crop>130)&(crop<175)]:
        for points in contours(mask):
            # Split a cycle at its farthest vertex, then recursively retain
            # true corners. Lattice stair-steps are below the 1.4px tolerance.
            split=int(np.argmax(np.linalg.norm(points-points[0],axis=1)))
            def simplify(i,j):
                if j-i<2:return [i,j]
                v=points[j]-points[i];length=np.linalg.norm(v)
                if length<1e-8:return [i,j]
                d=np.abs(v[0]*(points[i+1:j,1]-points[i,1])-v[1]*(points[i+1:j,0]-points[i,0]))/length
                k=int(np.argmax(d))+i+1
                if d[k-i-1]>1.4:return simplify(i,k)[:-1]+simplify(k,j)
                return [i,j]
            ids=simplify(0,split)[:-1]+simplify(split,len(points)-1)
            for i,j in zip(ids,ids[1:]):
                segment=points[i:j+1];v=segment[-1]-segment[0]
                length=np.linalg.norm(v)
                if length<20:continue
                _,_,vh=np.linalg.svd(segment-segment.mean(axis=0),full_matrices=False)
                v=vh[0]
                # Image y points down, camera y points up.
                lines.append((float(length),float(np.arctan2(-v[1],v[0])%np.pi)))
    groups=cluster_slopes(lines,.018)
    return [(l,a) for l,a in groups if l>35][:5]


def read_cards(arr,ocr=None):
    ocr=ocr or OCR();cards={}
    for cy in (26,64,102):
        for cx in (264,320,376):
            x,y=cx*8,cy*8
            code=ocr.char(arr[y-27:y+27,x-212:x-156,0]<140,'JKLMNPQRS')[0]
            crop=arr[y-119:y+120,x-119:x+120,0].copy()
            yy,xx=np.mgrid[-119:120,-119:120]
            marker=np.abs(crop.astype(int)-85)<5
            require(marker.sum()>35,'Missing sight mark '+code)
            # Grayscale antialiasing can contain isolated value-85 pixels on
            # black outline edges. Locate the complete circular cross pattern,
            # then fit its ring, rather than bound every grey pixel in a card.
            correlation=np.zeros(crop.shape,dtype=float)
            padded=np.pad(marker,14)
            for dy in range(-13,14):
                for dx in range(-13,14):
                    rr=np.hypot(dx,dy)
                    core=(4.6<rr<5.8) or (abs(dx)<.6 and 8<=abs(dy)<=12) or (abs(dy)<.6 and 8<=abs(dx)<=12)
                    if core:correlation+=padded[14+dy:253+dy,14+dx:253+dx]
            py,px=np.unravel_index(np.argmax(correlation),correlation.shape)
            require(correlation[py,px]>24,'Incomplete sight cross '+code)
            gy,gx=np.nonzero(marker)
            rr=np.hypot(gx-px,gy-py);keep=(rr>3.7)&(rr<6.7)
            gx=gx[keep].astype(float);gy=gy[keep].astype(float)
            require(len(gx)>=18,'Missing sight ring '+code)
            fit=np.linalg.lstsq(np.c_[2*gx,2*gy,np.ones(len(gx))],gx*gx+gy*gy,rcond=None)[0]
            sight=fit[:2]-119
            foreground=(crop>240)|(crop<180)
            c=np.array([xx[foreground].mean(),yy[foreground].mean()])
            rms=np.sqrt(((xx[foreground]-c[0])**2+(yy[foreground]-c[1])**2).mean())
            # Conservative mask of the cross's entire envelope, including its
            # antialiasing. Its coordinates are read separately, never fitted.
            cross_region=(abs(xx-sight[0])<14)&(abs(yy-sight[1])<14)
            val=crop
            labels=np.zeros(val.shape,np.uint8);labels[val>240]=2;labels[(val>130)&(val<175)]=1
            valid=((val>240)|((val>130)&(val<175))|((val>205)&(val<228)))&~cross_region
            slopes=read_lines(crop)
            require(len(slopes)>=4,'Insufficient readable straight directions '+code+str(slopes))
            cards[code]={'labels':labels,'valid':valid,'centroid':c,'rms':float(rms),'sight':sight,
                         'slopes':slopes,'code':code,'center_px':[x,y]}
    require(len(cards)==9,'View codes must be unique')
    return cards
