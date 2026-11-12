"""Continuous inverse projection and marked sightline, using only pixel data."""
import numpy as np
from .inverse_camera import cameras
from .parser import require


def camera(cells,ts,holes,R,grid_size=180):
    x,y,z=R
    vertices=np.array([(t@np.r_[cells[p]+uv,0.,1.])[:3] for p,t in enumerate(ts) for uv in [(0,0),(1,0),(1,1),(0,1)]])
    projected=vertices@R[:2].T;center=projected.mean(axis=0)
    radius=np.linalg.norm(projected-center,axis=1).max()
    planes=[]
    for p,t in enumerate(ts):
        normal=t[:3,2];den=normal@z
        if abs(den)>1e-8:planes.append((p,t,normal,den))
    def sample(xx,yy):
        xx,yy=np.broadcast_arrays(xx,yy)
        q=(center[0]+radius*xx)[...,None]*x+(center[1]+radius*yy)[...,None]*y
        best=np.full(xx.shape,np.inf);label=np.zeros(xx.shape,np.uint8)
        for p,t,normal,den in planes:
            origin=(t@np.r_[cells[p],0.,1.])[:3]
            depth=np.sum((origin-q)*normal,axis=-1)/den
            uv=(q+depth[...,None]*z-origin)@t[:3,:2]
            inside=np.all((uv>=0)&(uv<=1),axis=-1)
            for l,b,r,top in holes[p]:inside&=~((uv[...,0]>l)&(uv[...,0]<r)&(uv[...,1]>b)&(uv[...,1]<top))
            use=inside&(depth<best);best[use]=depth[use];label[use]=2 if den<0 else 1
        return label
    grid=(np.arange(grid_size)+.5)/(grid_size/2)-1
    xx,yy=np.meshgrid(grid,grid);mask=sample(xx,yy)>0
    require(mask.any(),'Empty candidate projection')
    centroid=np.array([xx[mask].mean(),yy[mask].mean()])
    rms=np.sqrt(((xx[mask]-centroid[0])**2+(yy[mask]-centroid[1])**2).mean())
    return sample,centroid,rms,center,radius


def match(cells,ts,holes,card):
    choices,proof=cameras(card['slopes'],ts,.026)
    require(choices,'No camera satisfies the observed spatial edge directions')
    yy,xx=np.mgrid[-119:120:3,-119:120:3]
    observed=card['labels'][::3,::3];valid=card['valid'][::3,::3]
    normalized_x=(xx-card['centroid'][0])/card['rms']
    normalized_y=-(yy-card['centroid'][1])/card['rms']
    def evaluate(R):
        sample,c,rms,center,radius=camera(cells,ts,holes,R)
        best=(1.,1.)
        for scale in (.985,1.,1.015):
            pred=sample(c[0]+rms*scale*normalized_x,c[1]+rms*scale*normalized_y)
            error=float(np.mean((pred!=observed)[valid]))
            best=min(best,(error,scale))
        return best
    scored=sorted([(evaluate(R),i) for i,R in enumerate(choices)])
    # Multiple noisy triples can reconstruct one physical orientation. Treat
    # them as one cluster, not additional solutions or independent evidence.
    distinct=[]
    for (error,scale),i in scored:
        R=choices[i]
        if all(np.linalg.norm(R-row[2])>.09 for row in distinct):distinct.append((error,scale,R))
    require(distinct,'No spatial camera candidates')
    error,scale,R=distinct[0]
    runner=distinct[1][0] if len(distinct)>1 else 1.
    require(error<.012,'No precise visible-body match: '+str((error,runner,card['code'])))
    require(runner-error>.008,'Ambiguous visible-body match: '+str((error,runner,card['code'])))
    sample,c,rms,center,radius=camera(cells,ts,holes,R,grid_size=400)
    sight=card['sight'];xy=np.array([(sight[0]-card['centroid'][0])/card['rms'],-(sight[1]-card['centroid'][1])/card['rms']])
    screen=center+radius*(c+rms*scale*xy)
    origin=screen@R[:2];direction=R[2]
    return origin,direction,{'pixel_error':error,'runner_up_error':runner,'scale_fit':scale,
        'screen_rows':R.tolist(),'sight_px':sight.tolist(),'world_origin':origin.tolist(),'direction':direction.tolist(),
        'candidate_clusters':len(distinct),'algebra':proof,
        'candidate_scores':[{'error':e,'scale':s,'direction':m[2].tolist()} for e,s,m in distinct]}
