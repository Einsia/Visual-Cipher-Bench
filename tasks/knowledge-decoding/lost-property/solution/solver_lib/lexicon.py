"""Generic dictionary splitting and arc-consistent compound-word search."""
from pathlib import Path
from collections import defaultdict

DATA=Path(__file__).resolve().parent

def load_relations():
    raw=set((DATA/'wordnet_lexical.txt').read_text().splitlines())
    words={w for w in raw if w.isascii() and w.isalpha() and len(w)>=2}
    compounds={''.join(c for c in w if c.isalpha()) for w in raw if w.isascii()}
    forward=defaultdict(set); backward=defaultdict(set)
    for w in compounds:
        for i in range(2,len(w)-1):
            a,b=w[:i],w[i:]
            if a in words and b in words:
                forward[a].add(b); backward[b].add(a)
    return forward,backward

def solve_domains(entities,edges,forward,backward,limit=100,relaxed=(),phrases=None):
    involved={i for pair in edges for i in pair}
    universe=(set(forward)|set(backward)) & set((DATA/'common_words_20k.txt').read_text().lower().splitlines()) & set((DATA/'wordnet_lexical.txt').read_text().splitlines())
    domains={i:(set(entities[i].get('alternatives',[entities[i]['word']])) if entities[i]['word'] else universe.copy()) for i in involved}
    def propagate(ds):
        changed=True
        while changed:
            changed=False
            for a,b in edges:
                ff,bb=phrases if (a,b) in relaxed else (forward,backward)
                da,db=ds[a],ds[b]
                na={x for x in da if not ff.get(x,set()).isdisjoint(db)}
                nb={y for y in db if not bb.get(y,set()).isdisjoint(na)}
                if not na or not nb: return None
                if na!=da or nb!=db: ds[a]=na; ds[b]=nb; changed=True
        return ds
    solutions=[]
    def search(ds):
        ds=propagate(ds)
        if ds is None:return
        choices=[i for i,d in ds.items() if len(d)>1]
        if not choices:
            solutions.append({i:next(iter(d)) for i,d in ds.items()})
            if len(solutions)>limit: raise ValueError('Dictionary constraints are ambiguous')
            return
        i=min(choices,key=lambda i:len(ds[i]))
        for w in sorted(ds[i]):
            child=ds.copy();child[i]={w};search(child)
    search(domains)
    return solutions


def load_phrases():
    f=defaultdict(set); b=defaultdict(set)
    for line in (DATA/'wordnet_phrases.tsv').read_text().splitlines():
        a,z,n=line.split('\t')
        if int(n)>=2:
            f[a].add(z);b[z].add(a)
    return f,b

class NounTaxonomy:
    """Unabridged WordNet noun hypernyms, used to ground pictured objects."""
    def __init__(self):
        import gzip,json
        with gzip.open(DATA/'wordnet_nouns.json.gz','rt') as f:self.nodes=json.load(f)
        self.senses=defaultdict(set)
        for key,node in self.nodes.items():
            for word in node['words']:
                word=''.join(c for c in word.lower() if c.isalpha())
                self.senses[word].add(key)
        self.cache={}
    def ancestors(self,key):
        if key not in self.cache:
            seen=set(); queue=[key]
            while queue:
                k=queue.pop()
                if k in seen:continue
                seen.add(k);queue.extend(self.nodes[k]['parents'])
            self.cache[key]=seen
        return self.cache[key]
    def is_kind_of(self,compound,object_name):
        target=self.senses.get(object_name,set())
        return any(not self.ancestors(k).isdisjoint(target) for k in self.senses.get(compound,set()))
