"""Public-data simulators and an explicitly bounded competing-rule family."""
from itertools import product


def swap(seq, p, q):
    return [q if c == p else p if c == q else c for c in seq]


def literal(start, tokens, values, model=None):
    m = dict(direction=1, feedback='visible', trigger='boxed', timing='before',
             wheel_swap=True, rewrite='all', include_new=True, reset=False, amount='feedback')
    if model is not None:
        m.update(model)
    initial = list(start['wheel'])
    wheel, record = initial[:], list(start['record'])
    raw = hole = None
    frames, details = [], []
    for i, token in enumerate(tokens):
        active = bool(record) and (token['boxed'] or m['trigger'] == 'all')
        if m['feedback'] == 'frozen_second':
            p = initial[tokens[1]['slot']] if len(tokens)>1 else initial[tokens[0]['slot']]
        elif m['feedback'] == 'selected':
            p = wheel[token['slot']]
        elif m['feedback'] == 'raw':
            p = raw if raw is not None else record[-1] if record else None
        elif m['feedback'] == 'hole':
            p = initial[hole] if hole is not None else record[-1] if record else None
        elif m['feedback'] == 'first':
            p = record[0] if record else None
        elif m['feedback'] == 'penultimate':
            p = record[max(0,len(record)-2)] if record else None
        elif m['feedback'] == 'top':
            p = wheel[0]
        else:
            p = record[-1] if record else None
        n = values[p] if active else 0
        if active and m['amount'] != 'feedback':
            n = {'slot':token['slot'], 'length':len(record), 'one':1,
                 'current_slot':wheel.index(p)}[m['amount']]
        before = {'wheel': ''.join(wheel), 'record': ''.join(record)}
        if active and m['reset']:
            wheel = initial[:]
        shift = (m['direction']*n) % len(wheel)
        if active and m['timing'] == 'before' and shift:
            wheel = wheel[-shift:]+wheel[:-shift]
        q = wheel[token['slot']]
        record.append(q)
        intermediate = {'wheel': ''.join(wheel), 'record': ''.join(record)}
        if active and m['timing'] == 'after' and shift:
            wheel = wheel[-shift:]+wheel[:-shift]
        if active:
            if m['wheel_swap']:
                wheel = swap(wheel, p, q)
            limit = len(record) if m['include_new'] else len(record)-1
            if m['rewrite'] == 'all':
                record[:limit] = swap(record[:limit], p, q)
            elif m['rewrite'] == 'last_old':
                inds = [len(record)-2] + ([len(record)-1] if m['include_new'] else [])
                for j in inds:
                    record[j] = swap([record[j]], p, q)[0]
            elif m['rewrite'] == 'forward':
                record[:limit] = [q if c==p else c for c in record[:limit]]
            elif m['rewrite'] == 'backward':
                record[:limit] = [p if c==q else c for c in record[:limit]]
            elif m['rewrite'] == 'reverse':
                record[:limit] = record[:limit][::-1]
            elif m['rewrite'] == 'rotate':
                if limit:
                    z=n%limit
                    if z: record[:limit] = record[:limit][-z:]+record[:limit][:-z]
        raw, hole = q, token['slot']
        frame = {'wheel': ''.join(wheel), 'record': ''.join(record)}
        frames.append(frame)
        details.append({'step': i+1, 'slot': hole, 'boxed': token['boxed'],
                        'feedback': p, 'turn': n, 'read': q,
                        'before': before, 'intermediate': intermediate, 'after': frame})
    return {'wheel': ''.join(wheel), 'record': ''.join(record), 'frames': frames, 'steps': details}


def lazy(start, tokens, values):
    """Independent factorization: fixed wheel IDs, offset, and mutable label map.

    The accumulated record contains immutable IDs, not rewritten letters.
    Transposing label-map entries updates every old occurrence in O(alphabet).
    """
    alphabet = list(start['wheel'])
    names = alphabet[:]
    record = [alphabet.index(c) for c in start['record']]
    offset = 0
    frames = []
    for t in tokens:
        if t['boxed']:
            previous = names[record[-1]]
            offset = (offset+values[previous]) % len(alphabet)
        selected_id = (t['slot']-offset) % len(alphabet)
        current = names[selected_id]
        record.append(selected_id)
        if t['boxed']:
            a, b = names.index(previous), names.index(current)
            names[a], names[b] = names[b], names[a]
        frames.append({'wheel': ''.join(names[(i-offset) % len(alphabet)] for i in range(len(alphabet))),
                       'record': ''.join(names[i] for i in record)})
    return {**frames[-1], 'frames': frames, 'stored_ids': record, 'offset': offset, 'label_map': names}


def models():
    keys = ['direction','feedback','trigger','timing','wheel_swap','rewrite','include_new','reset','amount']
    domains = [[1,-1], ['visible','raw','hole','first','penultimate','frozen_second','selected','top'], ['boxed','all'],
               ['before','after','none'], [True,False],
               ['all','none','last_old','forward','backward','reverse','rotate'],
               [True,False], [False,True], ['feedback','slot','length','one','current_slot']]
    return [dict(zip(keys, vals)) for vals in product(*domains)]


def evidence_match(spec, model):
    result={}
    for name,row in [('ordinary_reads',spec['ordinary'])]+[(f'observation_{i+1}',r) for i,r in enumerate(spec['observations'])]:
        a=literal(row['start'],row['tokens'],spec['values'],model)
        result[name]=all(a[k]==row['end'][k] for k in ('wheel','record'))
    return result


def reverse_record(word, boxes):
    """Deterministic inverse on the record; no candidate raw-read enumeration."""
    rec = list(word)
    raw = []
    for box in reversed(boxes):
        if box:
            p, q = rec[-1], rec[-2]
            rec = swap(rec, p, q)
        else:
            q = rec[-1]
        assert rec[-1] == q
        raw.append(rec.pop())
    assert not rec
    return list(reversed(raw))


def encode(raw, boxes, start, values):
    wheel = list(start['wheel'])
    rec = list(start['record'])
    tokens = []
    for q, box in zip(raw, boxes):
        if box:
            p = rec[-1]
            n = values[p] % len(wheel)
            if n:
                wheel = wheel[-n:]+wheel[:-n]
        tokens.append({'slot':wheel.index(q), 'boxed':bool(box)})
        rec.append(q)
        if box:
            wheel, rec = swap(wheel,p,q), swap(rec,p,q)
    return tokens
