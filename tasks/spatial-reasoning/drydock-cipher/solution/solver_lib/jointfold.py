"""Resolve genuine folding alternatives by the common target, never by letters.

Each candidate is produced by closure search. Enumerate every combination, check
volume, and exhaust exact cover. The caller rejects unless exactly one candidate
combination can form the target; no first-solution assumption or word filter.
"""
import itertools
from flatpack import solid_of, exact_cover

def resolve(candidate_sets, target, limit=5000):
    trials=[];survivors=[]
    for ids in itertools.product(*(range(len(c)) for c in candidate_sets)):
        selected=[c[j] for c,j in zip(candidate_sets,ids)]
        if any(c['cells'] is None for c in selected):
            trials.append(dict(fold_indices=list(ids),reason='invalid closed solid',packings=0));continue
        pieces=[solid_of(c['cells']) for c in selected]
        volumes=[len(p)/24 for p in pieces]
        if sum(map(len,pieces))!=len(target):
            trials.append(dict(fold_indices=list(ids),reason='volume mismatch',volumes=volumes,packings=0));continue
        sols,stats=exact_cover(pieces,target,limit=limit)
        if len(sols)>=limit:raise RuntimeError('joint folding/packing enumeration limit reached')
        trials.append(dict(fold_indices=list(ids),volumes=volumes,packings=len(sols),**stats))
        if sols:survivors.append((ids,selected))
    evidence=dict(candidate_counts=[len(c) for c in candidate_sets],combinations_tested=len(trials),
                  target_compatible_combinations=len(survivors),trials=trials,
                  selected_fold_indices=list(survivors[0][0]) if len(survivors)==1 else None)
    return (survivors[0][1] if len(survivors)==1 else None), evidence

def mirror_print_audit(pieces, target_cells, rows, cols, limit=5000):
    """Exhaust every mirror subset. A mirrored sheet has its print on the inside.
    Count complete exterior unit faces that could still have outward ink. This
    is a conservative upper bound: we do not assume split faces form letters.
    """
    import collections
    import numpy as np
    from flatpack import surface, SUB, MIRROR, transform_solid
    target=solid_of(target_cells)
    planes=collections.defaultdict(dict)
    for vs,n,typ,cell in surface(target_cells):
        if typ!='sq' or abs(n[2])>1e-9:continue
        nv=np.array(n);right=np.cross((0,0,1),nv);c=np.mean(vs,axis=0)/2
        plane=(tuple(n),round(float(np.dot(vs[0],nv)),6))
        gridpos=(int(np.floor(c[2])),int(np.floor(np.dot(c,right))))
        face=frozenset((cell,f,d) for f,d in SUB if tuple(f)==tuple(n))
        planes[plane][gridpos]=face
    windows=[]
    for g in planes.values():
        for z,u in g:
            keys=[(z-r,u+c) for r in range(rows) for c in range(cols)]
            if all(k in g for k in keys):windows.append([g[k] for k in keys])
    results=[]
    for mask in itertools.product([0,1],repeat=len(pieces)):
        if not any(mask):continue
        ps=[transform_solid(p,MIRROR) if m else p for p,m in zip(pieces,mask)]
        sols,stats=exact_cover(ps,target,limit=limit)
        if len(sols)>=limit:raise RuntimeError('mirror enumeration limit reached')
        counts=[]
        for sol in sols:
            ink=set().union(*(set(sub) for i,sub,_ in sol if not mask[i]))
            counts.extend(sum(face<=ink for face in w) for w in windows)
        results.append(dict(mask=''.join(map(str,mask)),packings=len(sols),
                            max_fully_printed_cells_in_window=max(counts,default=0),
                            possible_full_printed_window=any(c==rows*cols for c in counts)))
    return dict(valid=not any(r['possible_full_printed_window'] for r in results),
                required_cells=rows*cols,subsets=results,
                scope='All mirrors of the target-selected closed shapes; printed-side-in surfaces supply no outward letters.')
