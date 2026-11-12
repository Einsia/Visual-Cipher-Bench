"""Test ordinary local exchange hypotheses against an incomplete worked grid.

Inputs, slot lengths, crossing indices and visible letters are observations.
There are no stored example output words or expected rule identifiers here.
"""
import itertools
from engine import load_dictionary,onset_swap

def infer(ex, dictionary):
    d,inv=load_dictionary(dictionary)
    inputs=ex['inputs']; slots=ex['slots']; cross=ex['crossing']; candidates=[]
    def fits(words):
        if any(len(w)!=s['length'] or not w.isalpha() or w.lower() not in d for w,s in zip(words,slots)):return False
        if words[0][cross[0]]!=words[1][cross[1]]:return False
        return all(all(w[int(i)].upper()==ch.upper() for i,ch in s['given'].items()) for w,s in zip(words,slots))
    a,b=inputs
    written={
        'unchanged':[(a,b)],
        'exchange_whole_words':[(b,a)],
        'exchange_first_letters':[(b[0]+a[1:],a[0]+b[1:])],
        'exchange_last_letters':[(a[:-1]+b[-1],b[:-1]+a[-1])],
        'reverse_spelling':[(a[::-1],b[::-1])],
    }
    for rule,words in written.items():
        for pair in words:
            if fits(pair):candidates.append({'rule':rule,'outputs':list(pair)})
    for rule in ['exchange_first_sounds','exchange_last_sounds','exchange_sound_tails']:
        pairs=set()
        for ap,bp in itertools.product(d.get(a,()),d.get(b,())):
            if rule=='exchange_first_sounds': phones=onset_swap(ap,bp)
            elif rule=='exchange_last_sounds': phones=(ap[:-1]+bp[-1:],bp[:-1]+ap[-1:])
            else: phones=(ap[:1]+bp[1:],bp[:1]+ap[1:])
            if phones:
                for pair in itertools.product(inv.get(phones[0],()),inv.get(phones[1],())):
                    if fits(pair):pairs.add(pair)
        for pair in sorted(pairs):candidates.append({'rule':rule,'outputs':list(pair)})
    return {'tested_rules':list(written)+['exchange_first_sounds','exchange_last_sounds','exchange_sound_tails'],
            'candidates':candidates,'rules':sorted({c['rule'] for c in candidates})}
