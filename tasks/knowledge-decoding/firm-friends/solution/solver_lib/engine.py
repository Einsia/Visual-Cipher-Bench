"""Joint reciprocal sound exchange and unlabelled crossword placement.

No fixed source/slot map, expected answer, or intended pairs are used. Two search
implementations share only the enumerated phonetic/placement option relation.
"""
from pathlib import Path
import re,itertools,time
from geometry import pair_conflict,noncrossing_matchings
VOWELS=set('AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW'.split())

def load_dictionary(path):
    d={};inv={}
    for line in Path(path).read_text().splitlines():
        row=line.split('#')[0].split()
        if not row:continue
        w=re.sub(r'\(\d+\)$','',row[0]).lower()
        ph=tuple(re.sub('[0-9]','',x) for x in row[1:])
        d.setdefault(w,set()).add(ph);inv.setdefault(ph,set()).add(w)
    return d,inv

def onset_swap(a,b):
    if not a or not b or a[0] in VOWELS or b[0] in VOWELS:return None
    return b[:1]+a[1:],a[:1]+b[1:]

def cells(e):return [(e['x']+k*e['dx'],e['y']+k*e['dy']) for k in range(e['length'])]

def answer_inventory(dp,n):
    return {w.upper() for w in (Path(dp).parent/'english_words_alpha.txt').read_text().split() if w.isalpha() and len(w)==n}

def pair_options(m,d,inv):
    groups=m['entries'];ss=m['sources'];out=[];trials=0;placements={}
    for i,s in enumerate(ss):
        for k,group in enumerate(groups):
            if s['direction'] not in ('unknown',group['direction']):continue
            for e in group['variants']:
                placements.setdefault((i,e['length']),[]).append((k,e))
    for i,j in itertools.combinations(range(len(ss)),2):
        seen=set()
        for an,bn in itertools.product(ss[i]['names'],ss[j]['names']):
            for ap,bp in itertools.product(sorted(d.get(an,())),sorted(d.get(bn,()))):
                trials+=1;ph=onset_swap(ap,bp)
                if not ph:continue
                for wa,wb in itertools.product(sorted(inv.get(ph[0],())),sorted(inv.get(ph[1],()))):
                    if not wa.isalpha() or not wb.isalpha():continue
                    for (a,ea),(b,eb) in itertools.product(placements.get((i,len(wa)),()),placements.get((j,len(wb)),())):
                        if a==b:continue
                        key=(a,b,tuple(ea.values()),tuple(eb.values()),wa,wb)
                        if key in seen:continue
                        seen.add(key);g={};ok=True
                        for e,w in [(ea,wa.upper()),(eb,wb.upper())]:
                            for p,ch in zip(cells(e),w):
                                if g.get(p,ch)!=ch:ok=False
                                g[p]=ch
                        if ok:out.append({'i':a,'j':b,'source_i':i,'source_j':j,'wi':wa.upper(),'wj':wb.upper(),'entry_i':ea,'entry_j':eb,'names':[an,bn],'phones':[ap,bp],'grid':g})
    return out,trials

def preparation(m,dp):
    t=time.perf_counter();d,inv=load_dictionary(dp);opts,trials=pair_options(m,d,inv)
    words=answer_inventory(dp,m['answer_entry']['length']);target=cells(m['answer_entry']);idx={}
    for w in words:
        for p,ch in zip(target,w):idx.setdefault((p,ch),set()).add(w)
    cache={}
    def possible(g):
        pattern=tuple(g.get(p) for p in target)
        if pattern not in cache:
            subsets=[idx.get((p,g[p]),set()) for p in target if p in g]
            cache[pattern]=bool(set.intersection(*subsets)) if subsets else True
        return cache[pattern]
    return opts,trials,target,possible,time.perf_counter()-t

def record(answer,chosen):
    return {'answer':answer,'pairs':[{k:v for k,v in o.items() if k!='grid'} for o in chosen]}

def pair_first(m,dp):
    opts,trials,target,possible,prep=preparation(m,dp);start=time.perf_counter()
    n=len(m['entries']);ns=len(m['sources']);assert n==ns
    full=(1<<len(opts))-1;resources=[0]*(n+ns);letterbits={};cellbits={}
    for k,o in enumerate(opts):
        bit=1<<k
        for r in [o['i'],o['j'],n+o['source_i'],n+o['source_j']]:resources[r]|=bit
        for p,ch in o['grid'].items():
            letterbits[p,ch]=letterbits.get((p,ch),0)|bit;cellbits[p]=cellbits.get(p,0)|bit
    pairbits={}
    for k,o in enumerate(opts):
        key=(o['source_i'],o['source_j'])
        pairbits[key]=pairbits.get(key,0)|(1<<k)
    spatial_bans={}
    for key in pairbits:
        exemplar={'source_i':key[0],'source_j':key[1]};ban=0
        for other,bits in pairbits.items():
            if pair_conflict(m,exemplar,{'source_i':other[0],'source_j':other[1]}):ban|=bits
        spatial_bans[key]=ban
    allowed=[]
    for o in opts:
        b=spatial_bans[o['source_i'],o['source_j']]
        for r in [o['i'],o['j'],n+o['source_i'],n+o['source_j']]:b|=resources[r]
        for p,ch in o['grid'].items():b|=cellbits[p]^letterbits[p,ch]
        allowed.append(full^b)
    stats={'nodes':0,'answer_pattern_prunes':0};solutions=[]
    def visit(rem,active,g,chosen):
        stats['nodes']+=1
        if not possible(g):stats['answer_pattern_prunes']+=1;return
        if not rem:
            solutions.append(record(''.join(g[p] for p in target),[opts[k] for k in chosen]));return
        count=len(opts)+1;best=0
        for r in sorted(rem):
            b=active&resources[r];num=b.bit_count()
            if not num:return
            if num<count:count=num;best=b
        while best:
            b=best&-best;best^=b;k=b.bit_length()-1;o=opts[k]
            visit(rem-{o['i'],o['j'],n+o['source_i'],n+o['source_j']},active&allowed[k],{**g,**o['grid']},chosen+[k])
    matchings=noncrossing_matchings(m['sources']) if m.get('noncrossing_pairs') else [tuple(pairbits)]
    for matching in matchings:
        if any(key not in pairbits for key in matching):continue
        active=0
        for key in matching:active|=pairbits[key]
        visit(set(range(n+ns)),active,{},[])
    stats['geometric_matchings_searched']=len(matchings)
    return {'route':'joint_source_slot_exact_cover_bitsets','preparation_seconds':prep,'solve_seconds':time.perf_counter()-start,'phone_pair_trials':trials,'pair_word_options':len(opts),'stats':stats,'solutions':solutions,'answers':sorted({s['answer'] for s in solutions})}

def word_first(m,dp):
    """Independent answer-first enumeration with explicit remaining-option lists.

    Enumerate the entire answer vocabulary, then search reciprocal pair covers.
    The bit masks only index initial answer-compatible options. Recursive search
    uses direct source/slot disjointness and explicit cell equality, not the
    pair-first conflict masks or its partial-answer pruning function.
    """
    start=time.perf_counter();d,inv=load_dictionary(dp);opts,trials=pair_options(m,d,inv)
    target=cells(m['answer_entry']);words=sorted(answer_inventory(dp,len(target)))
    n=len(m['entries']);full=(1<<len(opts))-1;cb={};lb={};resources=[0]*(2*n)
    keys=[(o['source_i'],o['source_j']) for o in opts]
    unique_keys=set(keys);spatial={}
    for key in unique_keys:
        exemplar={'source_i':key[0],'source_j':key[1]}
        spatial[key]={other for other in unique_keys if pair_conflict(m,exemplar,{'source_i':other[0],'source_j':other[1]})}
    sets=[]
    for k,o in enumerate(opts):
        bit=1<<k;rs={o['i'],o['j'],n+o['source_i'],n+o['source_j']};sets.append(rs)
        for r in rs:resources[r]|=bit
        for p,ch in o['grid'].items():cb[p]=cb.get(p,0)|bit;lb[p,ch]=lb.get((p,ch),0)|bit
    pairbits={}
    for k,key in enumerate(keys):pairbits[key]=pairbits.get(key,0)|(1<<k)
    matchings=noncrossing_matchings(m['sources']) if m.get('noncrossing_pairs') else None
    blocks=[]
    if matchings is not None:
        for matching in matchings:
            if any(key not in pairbits for key in matching):continue
            union=0
            for key in matching:union|=pairbits[key]
            blocks.append((union,[pairbits[key] for key in matching]))
    else:blocks=[(full,[])]
    letter_allowed={(p,ch):full^(cb.get(p,0)^lb.get((p,ch),0)) for p in target for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
    stats={'nodes':0,'answer_words_tested':len(words),'answer_words_with_nonempty_domains':0};solutions=[]
    def visit(rem,candidates,g,chosen,answer):
        stats['nodes']+=1
        if not rem:
            solutions.append(record(answer,[opts[k] for k in chosen]));return
        domains={r:[] for r in rem}
        for k in candidates:
            for r in sets[k]:domains[r].append(k)
        best=min(domains.values(),key=len)
        for k in best:
            o=opts[k];ng={**g,**o['grid']};remaining=rem-sets[k]
            rest=[j for j in candidates if not sets[j]&sets[k] and keys[j] not in spatial[keys[k]] and all(ng.get(p,ch)==ch for p,ch in opts[j]['grid'].items())]
            visit(remaining,rest,ng,chosen+[k],answer)
    for answer in words:
        active=full
        for p,ch in zip(target,answer):active &= letter_allowed[p,ch]
        if any(not active&b for b in resources):continue
        stats['answer_words_with_nonempty_domains']+=1
        for union,pair_masks in blocks:
            compatible=active&union
            if any(not active&mask for mask in pair_masks):continue
            if any(not compatible&mask for mask in resources):continue
            candidates=[]
            while compatible:
                bit=compatible&-compatible;compatible^=bit;candidates.append(bit.bit_length()-1)
            visit(set(range(2*n)),candidates,dict(zip(target,answer)),[],answer)
    stats['geometric_matchings_searched']=len(blocks)
    return {'route':'answer_first_direct_constraint_search','solve_seconds':time.perf_counter()-start,'phone_pair_trials':trials,'pair_word_options':len(opts),'stats':stats,'solutions':solutions,'answers':sorted({s['answer'] for s in solutions})}
