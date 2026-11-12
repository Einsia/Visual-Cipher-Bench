"""Alternative mapping-family search over the observed runs."""
from itertools import product
from time import perf_counter

def solved_loop(pairs,queue,record):
    p={a:b for a,b in pairs}|{b:a for a,b in pairs};r=list(record)
    for i,j in queue:
        i-=1;j-=1;x,y=r[i],r[j];a,b=p[x],p[y]
        if x!=y and a!=y:
            p[x],p[b]=b,x;p[y],p[a]=a,y
        trans={a:b,b:a};r[i:j+1]=[trans.get(z,z) for z in reversed(r[i:j+1])]
    return dict(pairs=sorted(a+b for a,b in p.items() if a<b),queue=[],record=''.join(r))

def mapping_run(initial,kind,region,other,mp,transport='fixed'):
    p={a:b for a,b in initial['pairs']}|{b:a for a,b in initial['pairs']};r=list(initial['record']);q=[list(c) for c in initial['queue']]
    while q:
        i,j=sorted(k-1 for k in q.pop(0));x,y=r[i],r[j];px,py=p[x],p[y];old=p.copy();vs=[x,y,px,py]
        if x!=y and px!=y:
            links=[(x,y),(px,py)] if kind=='elope' else [(x,py),(y,px)]
            for u,v in links:p[u]=v;p[v]=u
        r[i:j+1]=reversed(r[i:j+1])
        mapping={vs[k]:vs[mp[k]] for k in range(4)}
        for k,z in enumerate(r):
            cond={'all':True,'inclusive':i<=k<=j,'exclusive':i<k<j,'leftopen':i<k<=j,'rightopen':i<=k<j,'outside':k<i or k>j}[region]
            if cond:r[k]=mapping.get(z,z if other=='identity' else old[z])
        if transport=='reflect':q=[[i+j+2-k if i+1<=k<=j+1 else k for k in c] for c in q]
        elif transport=='exchange':q=[[j+1 if k==i+1 else i+1 if k==j+1 else k for k in c] for c in q]
    return dict(pairs=sorted(a+b for a,b in p.items() if a<b),queue=[],record=''.join(r))

def probe(episodes,target,transports=('fixed',)):
    start=perf_counter();tested=0;survivors=[];first=0
    for kind,region,other,mp,transport in product(['elope','exchange'],['all','inclusive','exclusive','leftopen','rightopen','outside'],['identity','partner'],product(range(4),repeat=4),transports):
        tested+=1;params=dict(kind=kind,region=region,other=other,mp=list(mp),transport=transport)
        if mapping_run(episodes[0]['initial'],**params)!=episodes[0]['final']:continue
        first+=1
        if all(mapping_run(ep['initial'],**params)==ep['final'] for ep in episodes[1:]):survivors.append(params)
    return dict(tested=tested,survivors_after_episodes=[first,len(survivors)],survivors=survivors,predictions=sorted({mapping_run(target,**m)['record'] for m in survivors}),seconds=perf_counter()-start,scope='Mapping family; endpoint order normalization is inert on fixed, ascending queues. Transport options are an additional comparison.')
