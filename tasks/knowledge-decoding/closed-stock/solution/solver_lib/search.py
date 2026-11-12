"""Joint lexical assignment and directed-cycle search, with no target words."""
from .lexicon import load
import time

def solve(problem):
    started=time.perf_counter();P,F,R,W=load()
    seals=problem['seals'];edges=problem['edges'];start=problem['start']
    D={v:set(W) for v in seals}
    D.update({k:set(v) for k,v in problem['picture_domains'].items()})
    counters={'search_nodes':0,'complete_cycles':0}
    def prop(D):
        changed=True
        while changed:
            changed=False
            for a,b in edges:
                aa={w for w in D[a] if F[w]&D[b]}
                bb={w for w in D[b] if R[w]&aa}
                if not aa or not bb:return None
                if aa!=D[a] or bb!=D[b]:D[a]=aa;D[b]=bb;changed=True
            for k in seals:
                other=set().union(*(D[j] for j in seals if j!=k))
                keep={w for w in D[k] if F[w]&other and R[w]&other}
                if not keep:return None
                if keep!=D[k]:D[k]=keep;changed=True
        return D
    D=prop(D)
    if D is None:return [],{'search_nodes':0,'seconds':time.perf_counter()-started}
    domains={k:sorted(v) for k,v in D.items()}
    results=[]
    def visit(D,path):
        counters['search_nodes']+=1
        if len(path)==len(seals):
            if (path[-1][1],path[0][1]) not in P:return
            counters['complete_cycles']+=1
            # Picture choices are independent after all seal words are fixed:
            # there are no picture-picture edges. Enumerate if that ever changes.
            assert not any(a.startswith('@') and b.startswith('@') for a,b in edges)
            results.append({'route':[v for v,w in path],'assignment':dict(path),'picture_domains':{k:sorted(v) for k,v in D.items() if k.startswith('@')}})
            return
        current=path[-1][1];used={v for v,w in path}
        for j in seals:
            if j in used:continue
            for w in sorted(F[current]&D[j]):
                if len(path)==len(seals)-1 and (w,path[0][1]) not in P:continue
                dd={k:set(v) for k,v in D.items()};dd[j]={w};dd=prop(dd)
                if dd is not None:visit(dd,path+[(j,w)])
    for w in sorted(D[start]):
        dd={k:set(v) for k,v in D.items()};dd[start]={w};dd=prop(dd)
        if dd is not None:visit(dd,[(start,w)])
    counters['seconds']=time.perf_counter()-started;counters['propagated_domains']=domains
    return results,counters
