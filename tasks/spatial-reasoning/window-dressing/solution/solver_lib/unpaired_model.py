"""Recover unlabeled views by coverage, then infer their correspondence.
No coordinates, answers, selected alphabet, or instance permutation is stored.
Repeated glyphs are permitted and their distinct matchings are enumerated.
"""
from collections import defaultdict
import itertools
import time
import numpy as np
from joint_model import reconstruct, ABC, bitset


def pairings(a, b):
    """All bijections preserving glyph identity, including repeated letters."""
    groups = [(tuple(i for i,c in enumerate(a) if c == ch),
               tuple(i for i,c in enumerate(b) if c == ch)) for ch in sorted(set(a))]
    if sorted(a) != sorted(b):
        return
    for choices in itertools.product(*(itertools.permutations(js) for _,js in groups)):
        mapping = [-1] * len(a)
        for (ids,_), js in zip(groups,choices):
            for i,j in zip(ids,js):
                mapping[i] = j
        yield mapping


def infer(raw, masks, target, tolerance=0):
    """raw's second-view positions are independent, never paired to view A."""
    started = time.perf_counter()
    views = [reconstruct(raw[:,:,v:v+1], masks[v:v+1], target[v:v+1], tolerance)
             for v in range(2)]
    index = defaultdict(list)
    for seq in views[0]['solutions']:
        index[''.join(sorted(seq))].append(seq)
    solutions = []
    for b in views[1]['solutions']:
        for a in index[''.join(sorted(b))]:
            fitted = np.array([np.logical_or.reduce([raw[i,ABC.index(ch),v]
                               for i,ch in enumerate(seq)]) for v,seq in enumerate([a,b])]) & masks
            error = int(np.count_nonzero(fitted != target))
            if error > tolerance:
                continue
            for mapping in pairings(a,b):
                solutions.append({'a':a, 'b':b, 'mapping':mapping, 'pixel_error':error})
    return {'solutions':solutions, 'solution_count':len(solutions), 'views':views,
            'seconds':time.perf_counter()-started,
            'method':'Independent full-alphabet scene coverage; multiset join; all glyph-preserving bijections'}


def permutation_crosscheck(raw, masks, target, a_solutions):
    """Independent exhaustive B-permutation check; no B scene solver results."""
    started = time.perf_counter()
    n = raw.shape[0]
    expected = bitset(target[1])
    visible = [[bitset(raw[i,k,1] & masks[1]) for k in range(26)] for i in range(n)]
    good = [[not (visible[i][k] & ~expected) for k in range(26)] for i in range(n)]
    solutions = []
    tested = 0
    for a in a_solutions:
        for b in sorted(set(itertools.permutations(a))):
            tested += 1
            have = 0
            for i,ch in enumerate(b):
                k = ABC.index(ch)
                if not good[i][k]:
                    break
                have |= visible[i][k]
            else:
                if have == expected:
                    for mapping in pairings(a,b):
                        solutions.append({'a':a,'b':''.join(b),'mapping':mapping,'pixel_error':0})
    return {'solutions':solutions,'tested_permutations':tested,'seconds':time.perf_counter()-started}


def swap_witnesses(raw, masks, target, sequence):
    """Measure every two-position exchange in the inferred second view."""
    witnesses=[]
    for i,j in itertools.combinations(range(len(sequence)),2):
        if sequence[i]==sequence[j]:
            continue
        changed=list(sequence);changed[i],changed[j]=changed[j],changed[i]
        predicted=np.logical_or.reduce([raw[k,ABC.index(ch),1] for k,ch in enumerate(changed)]) & masks[1]
        diff=predicted!=target[1];ys,xs=np.where(diff)
        witnesses.append({'positions':[i,j],'b':''.join(changed),'different_pixels':int(diff.sum()),
                          'box_local_to_b':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None})
    return sorted(witnesses,key=lambda q:q['different_pixels'])
