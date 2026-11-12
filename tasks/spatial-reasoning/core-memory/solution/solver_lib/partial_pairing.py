"""Generic same-glyph, two-view reconstruction with partially observed matching.
"""
import itertools, math, time
import numpy as np
from joint_model import ABC, bitset


def reconstruct_matching(raw, masks, target, fixed, tolerance=0):
    start = time.perf_counter()
    n = raw.shape[0]
    if len(set(fixed.values())) != len(fixed):
        raise ValueError('Given traces are not injective')
    # Index i denotes an A position, j independently denotes a sorted B position.
    ink, extras, costs = {}, {}, {}
    for view in range(2):
        for i in range(n):
            for k in range(len(ABC)):
                visible = raw[i, k, view] & masks[view]
                outside = visible & ~target[view]
                costs[view, i, k] = int(outside.sum())
                ink[view, i, k] = bitset(visible & target[view])
                extras[view, i, k] = bitset(outside)
    taken = set(fixed.values())
    destinations = {i: [fixed[i]] if i in fixed else [j for j in range(n) if j not in taken] for i in range(n)}
    domains = []
    for i in range(n):
        domains.append([(j, ABC[k], ink[0, i, k], ink[1, j, k], extras[0, i, k], extras[1, j, k])
                        for j in destinations[i] for k in range(len(ABC))
                        if costs[0, i, k] + costs[1, j, k] <= tolerance])
    targets = [bitset(v) for v in target]
    order = sorted(range(n), key=lambda i: len(domains[i]))
    suffix = [[0, 0] for _ in range(n + 1)]
    for d in range(n - 1, -1, -1):
        suffix[d] = suffix[d + 1].copy()
        for j, ch, a, b, ea, eb in domains[order[d]]:
            suffix[d][0] |= a
            suffix[d][1] |= b
    solutions, pick, nodes = [], [None] * n, 0

    def dfs(depth, used, a, b, ea, eb):
        nonlocal nodes
        nodes += 1
        missing = (targets[0] & ~(a | suffix[depth][0])).bit_count() + (targets[1] & ~(b | suffix[depth][1])).bit_count()
        if missing + ea.bit_count() + eb.bit_count() > tolerance:
            return
        if depth == n:
            solutions.append({'screen_order': ''.join(x[1] for x in pick),
                              'pairing': [x[0] for x in pick],
                              'pixel_error': missing + ea.bit_count() + eb.bit_count()})
            return
        i = order[depth]
        for j, ch, va, vb, vea, veb in domains[i]:
            if used & (1 << j):
                continue
            pick[i] = (j, ch)
            dfs(depth + 1, used | (1 << j), a | va, b | vb, ea | vea, eb | veb)

    dfs(0, 0, 0, 0, 0, 0)
    unknown = [i for i in range(n) if i not in fixed]
    remaining = [j for j in range(n) if j not in taken]
    white_pairs = []
    for perm in itertools.permutations(remaining):
        pair = dict(fixed)
        pair.update(zip(unknown, perm))
        if all(any(q[0] == pair[i] for q in domains[i]) for i in range(n)):
            white_pairs.append([pair[i] for i in range(n)])
    return {'solutions': solutions, 'solution_count': len(solutions), 'visited_nodes': nodes,
            'fixed_pairs': [[i, j] for i, j in sorted(fixed.items())],
            'unresolved_positions': unknown, 'permutations_before_ink': math.factorial(len(unknown)),
            'pairings_after_white_space': white_pairs,
            'candidate_pairs_and_glyphs': [[[q[0], q[1]] for q in ds] for ds in domains],
            'seconds': time.perf_counter() - start}
