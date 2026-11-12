"""Inverse spatial view matching from pixels, independently ray-rasterized.
All view outlines and poses are recovered from the image.
Free translation, scale and roll are removed before comparison; reflection is not.
"""
import itertools
import numpy as np
from .parser import require

N=360
RADII=np.linspace(.025,2.65,64)
THETA=np.arange(N)*2*np.pi/N

def camera(cells,ts,holes,direction):
    z=np.asarray(direction,dtype=float);z/=np.linalg.norm(z)
    seed=np.eye(3)[np.argmin(np.abs(z))];x=np.cross(seed,z);x/=np.linalg.norm(x);y=np.cross(z,x)
    screen=np.array([x,y,z])
    vertices=[];planes=[]
    for p,t in enumerate(ts):
        for uv in [(0,0),(1,0),(1,1),(0,1)]:
            vertices.append(screen@(t@np.r_[cells[p]+uv,0.,1.])[:3])
        normal=t[:3,2];den=normal@z
        if abs(den)>1e-8:planes.append((p,t,normal,den))
    vertices=np.array(vertices);center=vertices[:,:2].mean(axis=0)
    radius=np.linalg.norm(vertices[:,:2]-center,axis=1).max()
    def sample(xx,yy):
        xx,yy=np.broadcast_arrays(xx,yy)
        q=(center[0]+radius*xx)[...,None]*x+(center[1]+radius*yy)[...,None]*y
        best=np.full(xx.shape,np.inf);label=np.zeros(xx.shape,dtype=np.uint8)
        for p,t,normal,den in planes:
            origin=(t@np.r_[cells[p],0.,1.])[:3]
            depth=np.sum((origin-q)*normal,axis=-1)/den
            hit=q+depth[...,None]*z
            uv=(hit-origin)@t[:3,:2]
            inside=np.all((uv>=0)&(uv<=1),axis=-1)
            for l,b,r,top in holes[p]:inside &= ~((uv[...,0]>l)&(uv[...,0]<r)&(uv[...,1]>b)&(uv[...,1]<top))
            use=inside&(depth<best);best[use]=depth[use];label[use]=2 if den<0 else 1
        return label
    grid=(np.arange(160)+.5)/80-1
    xx,yy=np.meshgrid(grid,grid);lab=sample(xx,yy);mask=lab>0
    require(mask.any(),'Empty candidate spatial view')
    c=np.array([xx[mask].mean(),yy[mask].mean()]);rms=np.sqrt(((xx[mask]-c[0])**2+(yy[mask]-c[1])**2).mean())
    return sample,c,rms

def read_cards(arr,ocr):
    cards={}
    for cy in (26,64,102):
        for cx in (264,320,376):
            x,y=cx*8,cy*8
            region=arr[y-27:y+27,x-212:x-156]
            code=ocr.char(region[:,:,0]<140,'JKLMNPQRS')[0]
            crop=arr[y-119:y+120,x-119:x+120,0]
            yy,xx=np.mgrid[-119:120,-119:120]
            # Ignore the grey field. The thin black silhouette belongs to the
            # foreground for centroid/scale, but is excluded from colour scoring.
            foreground=(crop>240)|(crop<180)
            require(foreground.sum()>600,'Missing view silhouette '+code)
            c=np.array([xx[foreground].mean(),yy[foreground].mean()])
            rms=np.sqrt(((xx[foreground]-c[0])**2+(yy[foreground]-c[1])**2).mean())
            px=c[0]+rms*RADII[:,None]*np.cos(THETA)
            py=c[1]-rms*RADII[:,None]*np.sin(THETA)
            ix=np.rint(px+119).astype(int);iy=np.rint(py+119).astype(int)
            inbounds=(ix>=0)&(ix<239)&(iy>=0)&(iy<239)
            val=np.full(ix.shape,217,dtype=np.uint8);val[inbounds]=crop[iy[inbounds],ix[inbounds]]
            obs=np.zeros(val.shape,np.uint8);obs[val>240]=2;obs[(val>130)&(val<175)]=1
            valid=(val>240)|((val>130)&(val<175))|((val>205)&(val<228))
            cards[code]={'observed':obs,'valid':valid,'center_px':[x,y],
                         'foreground_centroid_px':c.tolist(),'rms_px':float(rms)}
    require(len(cards)==9,'View card codes are not unique')
    return cards

def recover_view(worlds,cells,ts,holes,card):
    obs,valid=card['observed'],card['valid'];scores=[]
    # Circular correlation checks every one-degree rotation without reflecting.
    of=[np.fft.rfft(((obs==k)&valid).astype(float),axis=1) for k in range(3)]
    for a,b in itertools.permutations(worlds,2):
        sample,center,rms=camera(cells,ts,holes,worlds[b]-worlds[a])
        best=(1.,0,0)
        for scale in (.96,.98,1.,1.02,1.04):
            xx=center[0]+rms*scale*RADII[:,None]*np.cos(THETA)
            yy=center[1]+rms*scale*RADII[:,None]*np.sin(THETA)
            pred=sample(xx,yy)
            spectrum=sum((of[k]*np.conj(np.fft.rfft((pred==k).astype(float),axis=1))).sum(axis=0) for k in range(3))
            corr=np.fft.irfft(spectrum,n=N);j=int(np.argmax(corr));error=1-float(corr[j])/valid.sum()
            best=min(best,(error,j,scale))
        scores.append({'pair':[a,b],'error':best[0],'roll_degrees':best[1],'scale_fit':best[2]})
    scores.sort(key=lambda s:s['error'])
    require(sum(s['error']<.022 for s in scores)==1,'No unique spatial view within pixel tolerance: '+str(scores[:2]))
    require(scores[1]['error']-scores[0]['error']>.025,'Ambiguous spatial view: '+str(scores[:2]))
    return scores[0]['pair'],{'best':scores[0],'runner_up':scores[1],'tested_ordered_pairs':len(scores),'all_scores':scores,
                            'alignment':'free centroid, RMS size, 360 rolls, 5 scale refinements; no reflection'}
