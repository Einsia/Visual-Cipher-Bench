"""Finite orthographic camera recovery from anonymous projected edge directions.

No window centres are used. Four distinct observed slopes suffice here: the
folded square edges have at most one direction outside a common plane, hence
at least three observed slopes have coplanar antecedents. For each assignment,
three homogeneous slope equations determine the plane's 2x2 projection up to
scale. Equal orthogonal camera rows give the missing column (two signs).
The four sign choices are then screened against every observed slope.
"""
import itertools
import numpy as np


def canonical(v):
    v=np.asarray(v,dtype=float);v=v/np.linalg.norm(v)
    first=np.flatnonzero(np.abs(v)>1e-8)[0]
    return v if v[first]>0 else -v


def world_edges(ts):
    out=[]
    for t in ts:
        for v in t[:3,:2].T:
            v=canonical(v)
            if all(abs(v@w)<1-1e-8 for w in out):out.append(v)
    return np.array(out)


def angle_distance(a,b):
    return np.abs((np.asarray(a)-np.asarray(b)+np.pi/2)%np.pi-np.pi/2)


def edge_slopes(shapes,min_length=.035):
    """Directions from vector boundary rings; also useful on simplified pixels."""
    edges=[]
    for shape in shapes:
        for ring in shape['rings']:
            for a,b in zip(ring,ring[1:]):
                v=np.subtract(b,a);n=np.linalg.norm(v)
                if n>min_length:edges.append((n,float(np.arctan2(v[1],v[0])%np.pi)))
    return cluster_slopes(edges,.008)


def cluster_slopes(edges,tolerance):
    groups=[]
    for length,angle in sorted(edges,reverse=True):
        match=next((g for g in groups if angle_distance(angle,g[1])<tolerance),None)
        if match is None:groups.append([length,angle])
        else:
            z=match[0]*np.exp(2j*match[1])+length*np.exp(2j*angle)
            match[0]+=length;match[1]=float(np.angle(z)/2%np.pi)
    return sorted(groups,reverse=True)


def cameras(slopes,ts,tolerance=.018,dedup_tolerance=.006):
    """Exhaust all nondegenerate assignments, not a sampled sphere search."""
    obs=np.array([a for _,a in slopes]);world=world_edges(ts)
    if len(obs)<4:raise ValueError('Need four distinct boundary directions for complete inverse camera recovery')
    if len(world)>5:raise ValueError('Unsupported folded edge family count')
    # Verify the structural pigeonhole premise, rather than assume it.
    planes=[]
    for i,j in itertools.combinations(range(len(world)),2):
        normal=np.cross(world[i],world[j])
        if np.linalg.norm(normal)<1e-7:continue
        normal/=np.linalg.norm(normal)
        members=np.abs(world@normal)<1e-7
        if members.sum()>=len(world)-1:planes.append(normal)
    if not planes:raise ValueError('Folded edges lack the required coplanar family')
    candidates=[];raw=0;assignments=0
    for ids in itertools.permutations(range(len(world)),3):
        w=world[list(ids)]
        normal=np.cross(w[0],w[1]);normal/=np.linalg.norm(normal)
        if abs(normal@w[2])>1e-7:continue
        e=w[0];f=np.cross(normal,e);basis=np.array([e,f,normal]);uv=w@basis[:2].T
        for inds in itertools.combinations(range(len(obs)),3):
            aa=obs[list(inds)];co=np.cos(aa);si=np.sin(aa)
            A=np.c_[-si[:,None]*uv,co[:,None]*uv]
            _,sv,vh=np.linalg.svd(A)
            if sv[-1]<1e-7:continue
            U=vh[-1].reshape(2,2)
            # For C=[U,h], C C^T=s^2 I. Therefore s is U's largest
            # singular value and h h^T is its positive rank-one complement.
            eig,vec=np.linalg.eigh(U@U.T)
            scale=np.sqrt(eig[1]);h=vec[:,0]*np.sqrt(max(0,eig[1]-eig[0]))
            if eig[0]<1e-10:continue
            assignments+=1
            for sign_u,sign_h in itertools.product([-1,1],repeat=2):
                C=np.c_[sign_u*U,sign_h*h]@basis/scale
                z=np.cross(C[0],C[1]);R=np.vstack([C,z]);raw+=1
                projected=world@C.T
                pred=np.arctan2(projected[:,1],projected[:,0])%np.pi
                loss=angle_distance(obs[:,None],pred).min(axis=1)
                if max(loss)>tolerance:continue
                if any(np.linalg.norm(R-q)<dedup_tolerance for q in candidates):continue
                candidates.append(R)
    return candidates,{'observed_slopes_degrees':np.degrees(obs).tolist(),'world_edge_families':len(world),
                       'coplanar_assignments':assignments,'algebraic_candidates':raw,'screened_candidates':len(candidates),'numerical_dedup_tolerance':dedup_tolerance,
                       'complete_basis':'At least four observed directions, at most one world family off a plane; enumerate all coplanar triples and both metric lifts, both in-plane signs.'}
