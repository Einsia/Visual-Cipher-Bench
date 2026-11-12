"""Data-independent exhaustive inverse search plus independent forward replay.

The optional native module is a plain C implementation of the same search.
It receives every instance value as a function argument and reads no files.
"""
import ctypes
import hashlib
import itertools
import json
import os
import platform
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import numpy as np


def replay(data,initial,selected):
    n=data['n']; p=list(initial);w=list(data['record'])
    if sorted(p)!=list(range(n)): raise ValueError('Search returned a non-permutation')
    if len(selected)!=data['count'] or sorted(set(selected))!=selected:
        raise ValueError('Search returned invalid coupon selections')
    if any(v>=0 and initial[i]!=v for i,v in enumerate(data['initial'])):
        raise ValueError('Start clue violated')
    for row in selected:
        a,b,c,d=data['rows'][row]
        x,y,u,v=p[a],p[b],p[c],p[d]
        w[u],w[v]=x,y
        p[u],p[v]=p[v],p[u]
    if any(v>=0 and p[i]!=v for i,v in enumerate(data['finish'])):
        raise ValueError('Finish clue violated')
    if w!=list(initial): raise ValueError('Closure violated')
    return ''.join(f'{v+1:02d}' for v in w)


def python_shard(data,finish):
    """Portable exhaustive fallback. Slow on large instances, no dependencies."""
    n=data['n'];k=data['count'];rows=data['rows'];solutions=[]
    holes=[j for j,v in enumerate(finish) if v<0]
    remaining=sorted(set(range(n))-set(finish))
    def visit(i,p,bindings,chosen):
        rem=k-len(chosen)
        if i+1<rem: return
        targets=[bindings.get(j,data['initial'][j]) for j in range(n)]
        if sum(v>=0 and p[j]!=v for j,v in enumerate(targets))>2*rem: return
        if not rem:
            if any(v>=0 and p[j]!=v for j,v in enumerate(data['initial'])): return
            if any(p[j]!=bindings.get(j,data['record'][j]) for j in range(n)): return
            solutions.append((p[:],list(reversed(chosen))))
            return
        for r in range(i,rem-2,-1):
            a,b,c,d=rows[r]
            for u in range(n):
                for v in range(u+1,n):
                    q=p[:];q[u],q[v]=q[v],q[u]
                    if {q[c],q[d]}!={u,v}: continue
                    new=bindings.copy();used=set(new.values());bad=False
                    for dest,value in ((q[c],q[a]),(q[d],q[b])):
                        if dest in new: continue
                        if value in used or (data['initial'][dest]>=0 and data['initial'][dest]!=value):
                            bad=True;break
                        new[dest]=value;used.add(value)
                    if not bad: visit(r-1,q,new,chosen+[r])
    for values in itertools.permutations(remaining):
        p=finish[:]
        for j,v in zip(holes,values): p[j]=v
        visit(len(rows)-1,p,{},[])
    return len(solutions),solutions[0] if solutions else None


def native_shard(job):
    data,finish,library=job
    if library is None: return python_shard(data,finish)
    n=data['n'];m=len(data['rows']);k=data['count']
    lib=ctypes.CDLL(library)
    I=ctypes.POINTER(ctypes.c_int); U=ctypes.POINTER(ctypes.c_uint64)
    lib.solve_reverse.argtypes=[ctypes.c_int]*3+[I]*4+[ctypes.c_int]*2+[U,I]
    lib.solve_reverse.restype=None
    arrays=[np.asarray(x,dtype=np.int32) for x in (data['rows'],data['initial'],finish,data['record'])]
    stats=np.zeros(7,dtype=np.uint64);out=np.zeros(n+k,dtype=np.int32)
    lib.solve_reverse(n,m,k,*(x.ctypes.data_as(I) for x in arrays),2,0,stats.ctypes.data_as(U),out.ctypes.data_as(I))
    count=int(stats[3])
    return count,(out[:n].tolist(),out[n:].tolist()) if count else None


def solve(data):
    if not 1<=data['n']<=16 or not 0<data['count']<=16 or len(data['rows'])>32:
        raise ValueError('Instance exceeds supported search dimensions')
    here=Path(__file__).resolve().parent
    library=None
    if platform.system()=='Linux' and platform.machine() in ('x86_64','AMD64'):
        manifest=json.loads((here/'native_manifest.json').read_text())
        for name,digest in manifest['sha256'].items():
            if hashlib.sha256((here/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Native search source/binary checksum mismatch')
        library=str(here/'search_linux_x86_64.so')
    holes=[j for j,v in enumerate(data['finish']) if v<0]
    remaining=sorted(set(range(data['n']))-set(data['finish']))
    split=min(2,len(holes));jobs=[]
    for values in itertools.permutations(remaining,split):
        finish=data['finish'][:]
        for j,v in zip(holes,values): finish[j]=v
        jobs.append((data,finish,library))
    workers=min(8,os.cpu_count() or 1,len(jobs))
    count=0;witness=None;done=0
    print(f'Search: {len(jobs)} exhaustive terminal shards, {workers} workers',file=sys.stderr,flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(native_shard,job) for job in jobs]
        for future in as_completed(futures):
            num,result=future.result();count+=num;done+=1
            if result is not None: witness=result
            if done%10==0 or done==len(jobs):
                print(f'Search: {done}/{len(jobs)} shards, {count} solution(s)',file=sys.stderr,flush=True)
    if count!=1: raise ValueError(f'Expected a unique solution; found {count}')
    return replay(data,*witness)
