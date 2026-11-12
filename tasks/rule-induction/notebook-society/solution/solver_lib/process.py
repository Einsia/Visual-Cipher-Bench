"""Position-addressed matching and record process; independent implementations."""
from itertools import product

def matching(pairs):
    return {c:d for a,b in pairs for c,d in [(a,b),(b,a)]}
def pair_list(p):return sorted(a+b for a,b in p.items() if a<b)
def swap(s,a,b):return ''.join(b if c==a else a if c==b else c for c in s)
def run(pairs,queue,record,model=None):
    m=dict(pair='selected',sub='partners',spatial='inclusive',lookup='current',address='current',scope='interval',queue='reflect',mode='swap',paired='normal')
    m.update(model or {});p=matching(pairs);p0=dict(p);r0=record;q=[list(c) for c in queue]
    trace=[dict(pairs=pair_list(p),queue=[list(c) for c in q],record=record)]
    while q:
        i,j=sorted(k-1 for k in q.pop(0));r=record if m['address']=='current' else r0
        x,y=r[i],r[j];was_paired=p[x]==y;lookup=p if m['lookup']=='current' else p0;a,b=lookup[x],lookup[y]
        u,v=(x,y) if m['pair']=='selected' else (a,b) if m['pair']=='partners' else ('','')
        if m['paired']=='skip' and was_paired:
            trace.append(dict(pairs=pair_list(p),queue=[list(c) for c in q],record=record));continue
        if u!=v:p={swap(c,u,v):swap(d,u,v) for c,d in p.items()}
        if m['spatial']=='inclusive':record=record[:i]+record[i:j+1][::-1]+record[j+1:]
        elif m['spatial']=='exclusive':record=record[:i+1]+record[i+1:j][::-1]+record[j:]
        elif m['spatial']=='whole':record=record[::-1]
        elif m['spatial']=='endpoints':
            t=list(record);t[i],t[j]=t[j],t[i];record=''.join(t)
        elif m['spatial']=='rotate_left':record=record[:i]+record[i+1:j+1]+record[i]+record[j+1:]
        elif m['spatial']=='rotate_right':record=record[:i]+record[j]+record[i:j]+record[j+1:]
        u,v=(a,b) if m['sub']=='partners' else (x,y) if m['sub']=='selected' else ('','')
        exchange=lambda txt: swap(txt,u,v) if m['mode']=='swap' else txt.replace(u,v) if m['mode']=='a_to_b' else txt.replace(v,u)
        if m['scope']=='global':record=exchange(record)
        elif m['scope']=='interval':record=record[:i]+exchange(record[i:j+1])+record[j+1:]
        elif m['scope']=='interior':record=record[:i+1]+exchange(record[i+1:j])+record[j:]
        elif m['scope']=='outside':record=exchange(record[:i])+record[i:j+1]+exchange(record[j+1:])
        if m['queue']=='reflect':q=[[i+j+2-k if i+1<=k<=j+1 else k for k in cell] for cell in q]
        elif m['queue']=='exchange':q=[[j+1 if k==i+1 else i+1 if k==j+1 else k for k in cell] for cell in q]
        trace.append(dict(pairs=pair_list(p),queue=[list(c) for c in q],record=record))
    return trace

def independent(pairs,queue,record):
    """Explicit linked-pair rewiring, index gather, and translation (no run helper)."""
    links=[set(p) for p in pairs];r=list(record);out=[]
    pending=[list(c) for c in queue]
    while pending:
        left,right=pending.pop(0)
        lo,hi=sorted((left-1,right-1));x,y=r[lo],r[hi]
        ix=next(i for i,g in enumerate(links) if x in g);iy=next(i for i,g in enumerate(links) if y in g)
        a=next(c for c in links[ix] if c!=x);b=next(c for c in links[iy] if c!=y)
        if ix!=iy:
            links[ix]={x,b};links[iy]={y,a}
        indices=list(range(len(r)));indices[lo:hi+1]=range(hi,lo-1,-1)
        table={a:b,b:a};r=[table.get(r[k],r[k]) if lo<=n<=hi else r[k] for n,k in enumerate(indices)]
        out.append(dict(pairs=sorted(''.join(sorted(g)) for g in links),record=''.join(r)))
        pending=[[lo+hi+2-k if lo+1<=k<=hi+1 else k for k in c] for c in pending]
    return out

def models():
    fields=['pair','sub','spatial','lookup','address','scope','queue','mode','paired']
    choices=[['selected','partners','none'],['partners','selected','none'],['inclusive','exclusive','whole','endpoints','rotate_left','rotate_right','none'],['current','initial'],['current','initial'],['global','interval','interior','outside'],['fixed','reflect','exchange'],['swap','a_to_b','b_to_a'],['normal','skip']]
    for vs in product(*choices):yield dict(zip(fields,vs))

def infer(states):
    survivors=list(models());total=len(survivors);counts=[]
    for n in range(1,len(states)):
        survivors=[m for m in survivors if run(**states[0],model=m)[:n+1]==states[:n+1]]
        counts.append(len(survivors))
    return dict(tested=total,survivors_after_steps=counts,survivors=survivors)

def undo(pairs,record,command):
    """Inverse derived from the visible endpoint relation, not a target lookup."""
    p=matching(pairs);i,j=sorted(k-1 for k in command);u,v=record[i],record[j]
    x,y=(u,v) if u==v or p[u]==v else (v,u)
    oldp={swap(c,x,y):swap(d,x,y) for c,d in p.items()}
    a,b=oldp[x],oldp[y];segment=swap(record[i:j+1],a,b)[::-1]
    return pair_list(oldp),record[:i]+segment+record[j+1:]


def infer_batches(episodes,model_list=None):
    survivors=list(models()) if model_list is None else list(model_list);total=len(survivors);counts=[]
    for episode in episodes:
        survivors=[m for m in survivors if run(**episode['initial'],model=m)[-1]==episode['final']]
        counts.append(len(survivors))
    return dict(tested=total,survivors_after_episodes=counts,survivors=survivors)

def reverse_model_probe(episodes):
    """Reverse-time attack on 84 natural models, with shared-current matching assumed."""
    import time
    from itertools import product
    start=time.perf_counter();survivors=[];attempts=0;states_count=0;max_frontier=0
    def positions(n,i,j,kind):
        indices=list(range(n))
        if kind=='inclusive':indices[i:j+1]=indices[i:j+1][::-1]
        elif kind=='exclusive':indices[i+1:j]=indices[i+1:j][::-1]
        elif kind=='whole':indices.reverse()
        elif kind=='endpoints':indices[i],indices[j]=indices[j],indices[i]
        elif kind=='rotate_left':indices[i:j+1]=indices[i+1:j+1]+indices[i:i+1]
        elif kind=='rotate_right':indices[i:j+1]=indices[j:j+1]+indices[i:j]
        return indices
    for spatial,scope,transport in product(['inclusive','exclusive','whole','endpoints','rotate_left','rotate_right','none'],['global','interval','interior','outside'],['fixed','reflect','exchange']):
        good=True
        for episode in episodes:
            initial=episode['initial'];final=episode['final'];alphabet=''.join(initial['pairs']);frontier={(tuple(final['pairs']),final['record'])}
            for cmd in reversed(executed_queue(initial['queue'], transport)):
                lo,hi=sorted(c-1 for c in cmd);nxt=set()
                for links,record in frontier:
                    pnew=matching(links);states_count+=1
                    for x,y in product(alphabet,repeat=2):
                        attempts+=1
                        pold={swap(a,x,y):swap(b,x,y) for a,b in pnew.items()};a,b=pold[x],pold[y]
                        mask=lambda k: scope=='global' or scope=='interval' and lo<=k<=hi or scope=='interior' and lo<k<hi or scope=='outside' and not lo<=k<=hi
                        intermediate=''.join(swap(c,a,b) if mask(k) else c for k,c in enumerate(record))
                        index=positions(len(record),lo,hi,spatial);old=['']*len(record)
                        for newidx,oldidx in enumerate(index):old[oldidx]=intermediate[newidx]
                        old=''.join(old)
                        if old[lo]==x and old[hi]==y:nxt.add((tuple(pair_list(pold)),old))
                frontier=nxt;max_frontier=max(max_frontier,len(frontier))
                if not frontier:break
            if (tuple(initial['pairs']),initial['record']) not in frontier:good=False;break
        if good:survivors.append(dict(spatial=spatial,scope=scope,queue=transport))
    return dict(tested_models=84,survivors=survivors,endpoint_pair_hypotheses=attempts,expanded_states=states_count,maximum_frontier=max_frontier,seconds=time.perf_counter()-start,assumptions='Current matching and selected-letter rewiring supplied; reverse inference tests seven spatial actions, four substitution scopes and three queue transport hypotheses. This is a narrower attack, not the full-family uniqueness proof.')


def executed_queue(queue, transport='reflect'):
    """Numerical transport can be compiled before looking at any letters."""
    pending=[list(c) for c in queue];out=[]
    while pending:
        i,j=sorted(pending.pop(0));out.append([i,j])
        if transport=='reflect':pending=[[i+j-k if i<=k<=j else k for k in c] for c in pending]
        elif transport=='exchange':pending=[[j if k==i else i if k==j else k for k in c] for c in pending]
    return out
