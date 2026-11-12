"""Rigid letter stencils: infer translations/quarter turns from grid cells, then solve jointly.

No board coordinates, letters, solution words or intended placements are stored in this module.
Blank stencil squares are transparent. Only the letter-bearing squares must hit distinct
non-picture white cells. Reflection is not an allowed operation.
"""
from itertools import product
from . import model as M


def placements(points, cells, reflections=False):
    out = {}
    for flip in range(2 if reflections else 1):
        for turn in range(4):
            rotated = []
            for r, c, ch in points:
                if flip:
                    c = -c
                for _ in range(turn):
                    r, c = c, -r
                rotated.append((r, c, ch))
            r0 = min(r for r, c, ch in rotated)
            c0 = min(c for r, c, ch in rotated)
            rotated = [(r-r0, c-c0, ch) for r, c, ch in rotated]
            for ar, ac in sorted(cells):
                rr, cc, _ = rotated[0]
                dr, dc = ar-rr, ac-cc
                p = {(r+dr, c+dc): ch for r, c, ch in rotated}
                if set(p) <= cells:
                    out[tuple(sorted(p.items()))] = p
    return list(out.values())


def geometry_count(domains, stop=None):
    count = 0
    def rec(i, used):
        nonlocal count
        if stop is not None and count >= stop:
            return
        if i == len(domains):
            count += 1
            return
        for p in domains[i]:
            if not used.intersection(p):
                rec(i+1, used | set(p))
    rec(0, set())
    return count


def solve(model, stencils, limit=1000, reflections=False):
    cells = {c for c,t in model.grid.items() if not t.startswith('#')}
    domains = [placements(s, cells, reflections) for s in stencils]
    stats = {'geometric_placements_per_stencil': list(map(len,domains)),
             'nodes': 0, 'registration_leaves': 0, 'word_search_nodes': 0,
             'solutions_capped': False}
    incidence = {}
    for si, lc in enumerate(model.lcells):
        for j,c in enumerate(lc):
            incidence.setdefault(('letter',c),[]).append((si,j))
        p=model.spic[si]
        if p is not None:
            incidence.setdefault(('picture',p),[]).append((si,None))
    links=[v for v in incidence.values() if len(v)>1]
    def propagate(cands):
        while True:
            changed=False
            if any(not cs for cs in cands):
                return None
            for entries in links:
                common=None
                for si,j in entries:
                    vals={x[2] if j is None else x[4][j] for x in cands[si]}
                    common=vals if common is None else common & vals
                if not common:
                    return None
                for si,j in entries:
                    new=[x for x in cands[si] if (x[2] if j is None else x[4][j]) in common]
                    if len(new)!=len(cands[si]):
                        cands[si]=new;changed=True
            if not changed:
                return cands
    def restrict(cands,p):
        out=[]
        for si,cs in enumerate(cands):
            fixed=[(k,p[c]) for k,c in enumerate(model.lcells[si]) if c in p]
            new=[x for x in cs if all(x[4][k]==ch for k,ch in fixed)] if fixed else cs
            if not new:
                return None
            out.append(new)
        return propagate(out)
    base=propagate(list(model.cands))
    found={};regs=set();oldgrid=dict(model.grid);oldcands=model.cands
    def rec(todo, used, givens, cands, chosen):
        stats['nodes']+=1
        if stats['solutions_capped']:
            return
        if not todo:
            stats['registration_leaves']+=1
            model.grid.update(givens);model.cands=cands
            fills,cap,st=M.distinct_fills(model,set(givens),limit=limit)
            stats['word_search_nodes']+=st['nodes']
            stats['solutions_capped'] |= cap
            for s in fills:
                key=(tuple(sorted(s['letters'].items())),tuple(sorted((p,tuple(sorted(n))) for p,n in s['names'].items())))
                found.setdefault(key,s)
                regs.add(tuple((i,tuple(sorted(p.items()))) for i,p in sorted(chosen.items())))
            if len(found)>=limit:
                stats['solutions_capped']=True
            return
        # Choose the stencil with the fewest presently viable placements, not a stored registration.
        best=None
        for i in todo:
            viable=[]
            for p in domains[i]:
                if used.intersection(p):
                    continue
                cs=restrict(cands,p)
                if cs is not None:
                    viable.append((p,cs))
            if not viable:
                return
            if best is None or len(viable)<len(best[1]):
                best=(i,viable)
        i,viable=best
        for p,cs in viable:
            rec([j for j in todo if j!=i],used|set(p),givens|p,cs,chosen|{i:p})
    try:
        if base is not None:
            rec(list(range(len(domains))),set(),{},base,{})
    finally:
        model.grid=oldgrid;model.cands=oldcands
    stats['distinct_registrations']=len(regs)
    stats['registrations']=[[[[r,c,ch] for (r,c),ch in p] for i,p in reg] for reg in sorted(regs)]
    return list(found.values()),stats['solutions_capped'],stats
