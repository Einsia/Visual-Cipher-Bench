"""Recover the omitted address link from observed example relationships.

No question data, answer, or example constants are embedded. This checks a
declared family of elementary readings, not arbitrary possible invented rules.
"""

def infer_letter_order(ids, regions, width, bank, printed):
    """Check natural spatial fill conventions against all observed example cells.

    The full example uses distinct letters, so every bank-to-cell pair is
    observed; no main-grid letters or answer are supplied to this inference.
    """
    import itertools
    scans = {}
    for major in ('rows', 'columns'):
        for down in (True, False):
            for right in (True, False):
                name = major + ('_down' if down else '_up') + ('_columns_right' if right else '_columns_left')
                def key(v, major=major, down=down, right=right):
                    row, col = divmod(v, width)
                    a, b = row * (1 if down else -1), col * (1 if right else -1)
                    return (a, b) if major == 'rows' else (b, a)
                scans[name] = key
    survivors=[]
    trials=0
    ascending=tuple(sorted(range(len(ids)),key=lambda i:ids[i]))
    for order in itertools.permutations(range(len(ids))):
        label='ascending_ids' if order==ascending else str([ids[i] for i in order])
        for name,key in scans.items():
            cells=[v for i in order for v in sorted(regions[i],key=key)]
            trials+=1
            if [printed[v] for v in cells]==bank:
                survivors.append(label+'/'+name)
    if survivors!=['ascending_ids/rows_down_columns_right']:
        raise ValueError(f'Example does not determine the letter allocation: {survivors}')
    return dict(survivors=survivors,conventions_tested=trials,
                bank=''.join(bank),printed_grid=''.join(printed),
                evidence='All example bank-to-cell correspondences; every region permutation and eight axis scan orders.')

def infer_address(ids, regions, rows):
    areas = dict(zip(ids, map(len, regions)))
    successor = {r['source']: r['receiver'] for r in rows}
    if set(successor) != set(ids) or set(successor.values()) != set(ids):
        raise ValueError('Demonstrated arrivals must form a permutation')
    predecessor = {v: k for k, v in successor.items()}
    observed = [r['lookup'] for r in rows]
    candidates = {}
    for role in ('source', 'receiver', 'predecessor'):
        values = [predecessor[r['source']] if role == 'predecessor' else r[role] for r in rows]
        candidates[role + '_id'] = values
        candidates[role + '_area'] = [areas[v] for v in values]
        candidates[role + '_area_indexed_area'] = [areas.get(areas[v]) for v in values]
    candidates['jump_distance'] = [r['distance'] for r in rows]
    survivors = [k for k, v in candidates.items() if v == observed]
    if survivors != ['receiver_area']:
        raise ValueError(f'Omitted address not resolved by example: {survivors}')
    direct = [abs(areas[r['source']] - areas[r['receiver']]) for r in rows]
    signed = [areas[r['source']] - areas[r['lookup']] for r in rows]
    distances = [r['distance'] for r in rows]
    if direct == distances or signed == distances or [-v for v in signed] == distances:
        raise ValueError('Example fails to distinguish direct/signed subtraction')
    return dict(observed_lookup_ids=observed, candidates=candidates,
                survivors=survivors, direct_pairwise_distances=direct,
                signed_lookup_differences=signed, geometric_distances=distances,
                scope='Source/receiver/predecessor identity, area, one further area lookup, and jump distance. No claim over arbitrary interpolated rules.')
