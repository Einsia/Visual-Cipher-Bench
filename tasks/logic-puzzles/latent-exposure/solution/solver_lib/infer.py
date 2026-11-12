"""Infer hidden arithmetic from endpoint letter positions and printed margins.

Only the parsed endpoint letters, local witnesses and margins are inputs.
We enumerate an explicit natural family, including every permutation of the
five side-count digits: complement-to-four is NOT assumed in that family.
"""
from itertools import product, permutations

DIGIT_MAPS = sorted(set(permutations(range(5))) |
                    {tuple(k-v for v in range(5)) for k in range(9)})
SCOPE = ('current/initial sampling; inside/outside/all; sum/count/max/min; '
         'independent row/column directions; all 16 endpoint membership tables; '
         'all 120 bijections of digits 0..4 plus k-n for k=0..8 (128 distinct maps); '
         'whole/inside/outside transport')


def candidates(masks, initial_letters, counts, order, snapshots):
    n = len(masks)
    inside = [bool(masks[r] >> c & 1) for r in range(n) for c in range(n)]
    initial = sum(counts, [])
    letters = sum([list(row) for row in initial_letters], [])
    lines = [[op // 2 * n + j if op % 2 == 0 else j * n + op // 2
              for j in range(n)] for op in order]
    observed = {step: dict(g, letters=sum([list(row) for row in g['letters']], []))
                for step, g in snapshots.items()}
    survivors = []
    tested = 0
    rejected_at = {}
    # Flip bit index = 2*source_membership + destination_membership.
    for timing, region, aggregate, directions, flips, digit_map, transport in product(
            ['current', 'initial'], ['inside', 'outside', 'all'],
            ['sum', 'count', 'max', 'min'], product([1, -1], repeat=2),
            range(16), DIGIT_MAPS, ['all', 'inside', 'outside']):
        tested += 1
        values = initial[:]
        payloads = letters[:]
        sums = []
        failed = None
        for step, (op, line) in enumerate(zip(order, lines), 1):
            sampled = [i for i in line if region == 'all' or inside[i] == (region == 'inside')]
            field = values if timing == 'current' else initial
            nums = [field[i] for i in sampled]
            amount = (sum(nums) if aggregate == 'sum' else len(nums) if aggregate == 'count'
                      else max(nums, default=0) if aggregate == 'max' else min(nums, default=0))
            sums.append(amount)
            moving = [i for i in line if transport == 'all' or inside[i] == (transport == 'inside')]
            old_values, old_letters = values[:], payloads[:]
            for j, source in enumerate(moving):
                destination = moving[(j + directions[op % 2] * amount) % len(moving)]
                flip = (flips >> (2 * inside[source] + inside[destination])) & 1
                values[destination] = digit_map[old_values[source]] if flip else old_values[source]
                payloads[destination] = old_letters[source]
            if any(v < 0 or v > 4 for v in values):
                failed = step
                break
            if step in observed:
                obs = observed[step]
                mismatch = any(ch is not None and ch != payloads[i] for i,ch in enumerate(obs['letters']))
                if 'values' in obs:
                    mismatch |= values != sum(obs['values'], [])
                if 'row_totals' in obs:
                    mismatch |= [sum(values[r*n:(r+1)*n]) for r in range(n)] != obs['row_totals']
                if 'column_totals' in obs:
                    mismatch |= [sum(values[r*n+c] for r in range(n)) for c in range(n)] != obs['column_totals']
                if mismatch:
                    failed = step
                    break
        if failed is not None:
            rejected_at[failed] = rejected_at.get(failed, 0) + 1
        else:
            survivors.append(dict(timing=timing, region=region, aggregate=aggregate,
                                  directions=list(directions), flip_table=flips,
                                  digit_map=list(digit_map), transport=transport, sums=sums,
                                  final_values=[values[r*n:(r+1)*n] for r in range(n)]))
    return {'candidate_count': tested, 'survivor_count': len(survivors),
            'survivors': survivors, 'rejected_at_step': rejected_at, 'scope': SCOPE}


def infer_rule(masks, initial_letters, counts, order, snapshots):
    report = candidates(masks, initial_letters, counts, order, snapshots)
    if report['survivor_count'] != 1:
        raise ValueError('calibration rule not unique in declared hypothesis family: '
                         f"{report['survivor_count']} candidates")
    winner = report.pop('survivors')[0]
    supported = dict(timing='current', region='inside', aggregate='sum', directions=[1, 1],
                     flip_table=6, digit_map=[4, 3, 2, 1, 0], transport='all')
    if any(winner[k] != v for k, v in supported.items()):
        raise ValueError(f'calibration recovered a rule unsupported by the target engine: {winner}')
    # Derived after selecting the unique map, for compatibility with replay proofs.
    winner['complement'] = 4
    return dict(report, rule=winner,
                observation_steps=sorted(snapshots),
                printed_state_letter_count=sum(ch is not None for g in snapshots.values() for row in g['letters'] for ch in row),
                printed_state_digit_count=sum(len(row) for g in snapshots.values()
                                              for row in g.get('values', [])))
