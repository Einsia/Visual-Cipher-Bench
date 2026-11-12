"""Exhaustive, data-driven interval layouts and mutable-total scheduling.

Only NumPy and the standard library. No precomputed model or answer.
"""
import itertools
import json
import time
import numpy as np


def configurations(numbers, targets, count):
    n = len(numbers)
    pre = np.r_[0, np.cumsum(numbers)]
    ends = np.array([(*c, n) for c in itertools.combinations(range(1, n), count-1)])
    starts = np.c_[np.zeros(len(ends), dtype=int), ends[:, :-1]]
    ls = ends-starts
    ss = pre[ends]-pre[starts]
    rs = np.asarray(targets)[ends-1]
    perms = np.array(list(itertools.permutations(range(count))))
    inv = np.argsort(perms, axis=1)
    return tuple(a[:, inv].reshape(-1, count).astype(np.int16) for a in (ls, ss, rs, ends))


def solve_data(nums_a, refs_a, nums_b, refs_b, edges, count=5, progress=None, a_range=None):
    start = time.monotonic()
    al, ass, ar, ae = configurations(nums_a, refs_a, count)
    bl, bs, br, be = configurations(nums_b, refs_b, count)
    edges = np.array(edges, dtype=np.intp)
    m = len(edges)
    # Trace reduction: disjoint cards commute because each reads/writes only
    # its own two current totals and thresholds never change. Keep one
    # lexicographic representative of every commuting-history class.
    independent = [sum(1 << j for j,(u,v) in enumerate(edges) if u != x and v != y)
                   for x,y in edges]

    def history_count(path):
        # Preserve the exact number of ordinary histories represented by a
        # terminal trace. Dependent cards retain their relative order.
        before = [0]*m
        seen = 0
        for e in path:
            before[e] = seen & ~independent[e]
            seen |= 1 << e
        counts = {0: 1}
        for _ in range(m):
            nxt = {}
            for mask, ways in counts.items():
                for e in range(m):
                    if not mask >> e & 1 and before[e] & mask == before[e]:
                        key = mask | 1 << e
                        nxt[key] = nxt.get(key, 0) + ways
            counts = nxt
        return counts[(1 << m)-1]

    perm_count = np.math.factorial(count) if hasattr(np, 'math') else __import__('math').factorial(count)
    # A swap preserves the multiset of ten initial tokens. Every future
    # threshold must be a sum of two distinct tokens from that multiset.
    max_sum = max(int(ass.max()+bs.max()), int(np.sort(ass,axis=1)[:,-2:].sum(axis=1).max()), int(np.sort(bs,axis=1)[:,-2:].sum(axis=1).max()))
    ca, cb = ass[::perm_count], bs[::perm_count]
    words=max_sum//64+1
    poss_words = np.zeros((len(ca), len(cb),words), dtype=np.uint64)
    def add_possible(sums):
        bit=np.left_shift(np.uint64(1),(sums%64).astype(np.uint64))
        for word in range(words):
            poss_words[:,:,word] |= np.where(sums//64==word,bit,np.uint64(0))
    for i, j in itertools.combinations(range(count), 2):
        add_possible((ca[:, i]+ca[:, j])[:,None])
        add_possible((cb[:, i]+cb[:, j])[None,:])
    for i in range(count):
        for j in range(count):
            add_possible(ca[:, i,None]+cb[None,:,j])
    poss=poss_words[:,:,0] if words==1 else poss_words
    # Compute/filter in batches; preserve every remaining legal branch.
    solutions = []
    begin,end=(0,len(al)) if a_range is None else a_range
    stats = dict(layout_pairs=(end-begin)*len(bl), multiset_survivors=0, schedule_nodes=0)
    b_all = np.arange(len(bl), dtype=np.int32)

    def search_batch(ai, bi, threshold):
        state = np.concatenate([ass[ai], bs[bi]], axis=1)
        ids = np.arange(len(ai), dtype=np.int32)
        masks = np.zeros(len(ai),dtype=np.uint16)
        sleeps = np.zeros(len(ai),dtype=np.uint16)
        paths = np.zeros(len(ai),dtype=np.uint64)
        for depth in range(m+1):
            stats['schedule_nodes'] += len(ids)
            if depth == m:
                for k,path in zip(ids,paths):
                    schedule=[(int(path)>>(4*d))&15 for d in range(m)]
                    solutions.append(dict(history_multiplicity=history_count(schedule), A_ends=ae[ai[k]].tolist(), B_ends=be[bi[k]].tolist(),
                        A_lengths=al[ai[k]].tolist(), B_lengths=bl[bi[k]].tolist(),
                        initial_sums=np.r_[ass[ai[k]],bs[bi[k]]].tolist(),
                        schedule=schedule))
                return
            ni, ns, nm, npth, nsl = [], [], [], [], []
            for e, (x, y0) in enumerate(edges):
                y = count+y0
                ok = (((masks | sleeps) & (1<<e)) == 0) & (state[:, x]+state[:, y] == threshold[ids, e])
                if not np.any(ok):
                    continue
                child = state[ok].copy()
                child[:,[x,y]] = child[:,[y,x]]
                ni.append(ids[ok]);ns.append(child);nm.append(masks[ok]|(1<<e))
                npth.append(paths[ok]|np.uint64(e<<(depth*4)))
                nsl.append((sleeps[ok] | ((1<<e)-1)) & independent[e])
            if not ni: return
            ids,state,masks,paths,sleeps=map(np.concatenate,(ni,ns,nm,npth,nsl))

    for first in range(begin, end, 32):
        a_batch = np.arange(first, min(first+32,end), dtype=np.int32)
        ai = np.repeat(a_batch,len(bl))
        bi = np.tile(b_all,len(a_batch))
        for x,y in edges:
            t = al[ai,x]*al[ai,br[bi,y]] + bl[bi,y]*bl[bi,ar[ai,x]]
            bits=poss[ai//perm_count,bi//perm_count] if words==1 else poss[ai//perm_count,bi//perm_count,np.minimum(t,max_sum)//64]
            keep = (t <= max_sum) & ((np.right_shift(bits, (t%64).astype(np.uint64)) & np.uint64(1)) != 0)
            ai, bi = ai[keep], bi[keep]
            if not len(ai): break
        stats['multiset_survivors'] += len(ai)
        for offset in range(0,len(ai),100000):
            a,b=ai[offset:offset+100000],bi[offset:offset+100000]
            ts = np.stack([al[a,x]*al[a,br[b,y]]+bl[b,y]*bl[b,ar[a,x]] for x,y in edges],axis=1)
            search_batch(a,b,ts)
        if progress and first % 320 == 0:
            progress(dict(completed_A=min(first+32,len(al)), total_A=len(al), seconds=time.monotonic()-start, solutions=len(solutions), **stats))
    stats['seconds']=time.monotonic()-start
    n=sum(s["history_multiplicity"] for s in solutions)
    return dict(solution_count=n, unique=n==1, complete=True, models=solutions, **stats)


def _job(args):
    return solve_data(*args[:5],a_range=args[5])


def exhaustive(nums_a, refs_a, nums_b, refs_b, edges, workers=8):
    import math
    import multiprocessing
    import sys
    start=time.monotonic()
    total=math.comb(len(nums_a)-1,4)*math.factorial(5)
    jobs=[(nums_a,refs_a,nums_b,refs_b,edges,(i,min(i+2048,total))) for i in range(0,total,2048)]
    results=[]
    with multiprocessing.Pool(processes=workers) as pool:
        for result in pool.imap_unordered(_job,jobs):
            results.append(result)
            if len(results)%5==0 or len(results)==len(jobs):
                print(json.dumps({'search_jobs_completed':len(results),'total_jobs':len(jobs),'seconds':round(time.monotonic()-start,2)}),file=sys.stderr,flush=True)
    models=[model for result in results for model in result['models']]
    n=sum(s["history_multiplicity"] for s in models)
    return dict(solution_count=n,unique=n==1,complete=True,models=models,
                seconds=time.monotonic()-start,workers=workers,
                **{key:sum(result[key] for result in results) for key in ['layout_pairs','multiset_survivors','schedule_nodes']})
