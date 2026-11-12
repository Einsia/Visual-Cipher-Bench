"""Stress-insensitive CMUdict operations; no puzzle answers or fixed transitions."""
import re
from pathlib import Path
from itertools import product
VOWELS=frozenset('AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW'.split())
def dictionary(path=None):
    entries={}
    for line in Path(path or Path(__file__).with_name('cmudict.dict')).read_text().splitlines():
        word,*sounds=line.split()
        word=word.split('(')[0]
        if not word.isalpha(): continue
        sounds=tuple(re.sub('[012]','',s) for s in sounds)
        entries.setdefault(word,[])
        if sounds not in entries[word]:entries[word].append(sounds)
    return entries

def index(entries):
    inverse={}
    for word,pronunciations in entries.items():
        for p in pronunciations:inverse.setdefault(p,set()).add(word)
    return inverse

def onset(p):
    i=next((i for i,x in enumerate(p) if x in VOWELS),len(p))
    return p[:i],p[i:]

def exchange(a,b):
    oa,ra=onset(a);ob,rb=onset(b)
    return ob+ra,oa+rb

def pronunciations(words,entries):
    for word in words:
        for p in entries.get(word,[]):yield word,p

def phrase_sounds(words,entries):
    for pp in product(*(entries.get(w,[]) for w in words)):
        yield tuple(t for p in pp for t in p)

def joined_pairs(names,entries,inverse):
    outputs=[];trials=0
    for (a,pa),(b,pb) in product(pronunciations(names[0],entries),pronunciations(names[1],entries)):
        trials+=1
        for word in sorted(inverse.get(pa+pb,())):
            outputs.append({'names':[a,b],'word':word,'phones':list(pa+pb)})
    return outputs,trials
