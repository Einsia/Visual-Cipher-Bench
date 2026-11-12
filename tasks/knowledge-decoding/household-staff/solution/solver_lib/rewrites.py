"""Simultaneous substitution, with ambiguity detected rather than resolved silently."""
from functools import lru_cache


def occurrences(s, word):
    return [(i, i + len(word), word) for i in range(len(s)) if s.startswith(word, i)]


def swap(s, a, b):
    matches = sorted(occurrences(s, a) + occurrences(s, b))
    if any(x[1] > y[0] for x, y in zip(matches, matches[1:])):
        return None
    out, pos = [], 0
    for lo, hi, w in matches:
        out.extend((s[pos:lo], b if w == a else a))
        pos = hi
    out.append(s[pos:])
    return ''.join(out)


def preimages(out, a, b):
    """All preimages, not the generally incorrect assumption that swap is an involution.

    Each output token is either an unchanged character or the replacement of a
    whole input name. Enumerate that finite tokenization and forward-check it.
    """
    @lru_cache(None)
    def build(i):
        if i == len(out):
            return ('',)
        terms = {(out[i], i + 1)}
        if out.startswith(a, i):
            terms.add((b, i + len(a)))
        if out.startswith(b, i):
            terms.add((a, i + len(b)))
        return tuple({head + tail for head, j in terms for tail in build(j)})
    return {s for s in build(0) if swap(s, a, b) == out}


def forward(start, pairs, names):
    """Retain global pictogram names across repeated occurrences."""
    states = {(start, ())}
    counts = [1]
    transitions = 0
    overlap_rejections = 0
    for left, right in pairs:
        new = set()
        for s, assigned in states:
            known = dict(assigned)
            for a in ([known[left]] if left in known else names[left]):
                for b in ([known[right]] if right in known else names[right]):
                    transitions += 1
                    t = swap(s, a, b)
                    if t is None:
                        overlap_rejections += 1
                        continue
                    m = dict(known)
                    m[left], m[right] = a, b
                    # Names no longer used can be projected out: only live variables matter.
                    future = {x for pair in pairs[len(counts):] for x in pair}
                    new.add((t, tuple(sorted((k, v) for k, v in m.items() if k in future))))
        states = new
        counts.append(len(states))
    return {s for s, _ in states}, {'frontier_sizes': counts, 'transitions': transitions,
                                   'overlap_rejections': overlap_rejections}


def backward(targets, pairs, names):
    states = {(s, ()) for s in targets}
    counts = [len(states)]
    transitions = 0
    rev = list(reversed(pairs))
    for left, right in rev:
        new = set()
        for s, assigned in states:
            known = dict(assigned)
            for a in ([known[left]] if left in known else names[left]):
                for b in ([known[right]] if right in known else names[right]):
                    transitions += 1
                    m = dict(known)
                    m[left], m[right] = a, b
                    future = {x for pair in rev[len(counts):] for x in pair}
                    assignment = tuple(sorted((k, v) for k, v in m.items() if k in future))
                    new.update((t, assignment) for t in preimages(s, a, b))
        states = new
        counts.append(len(states))
    return {s for s, _ in states}, {'frontier_sizes': counts, 'transitions': transitions}
