"""General lexicon loader. No instance data or expected answers."""
from pathlib import Path
from collections import defaultdict
import gzip,json,re

class Lexicon:
    def __init__(self, root=None, broad=False):
        root=Path(root or Path(__file__).parent)
        self.pron=defaultdict(set)
        for line in (root/'cmudict.dict').read_text().splitlines():
            fields=line.split('#',1)[0].split()
            if not fields or fields[0].startswith(';;;'):continue
            word=re.sub(r'\(\d+\)$','',fields[0]).lower()
            if word.isalpha():
                self.pron[word].add(tuple(re.sub(r'\d','',p) for p in fields[1:]))
        self.senses=defaultdict(list)
        for sid,lemmas,gloss,ptrs in json.load(gzip.open(root/'wordnet.json.gz','rt')):
            for w in lemmas:
                if w.isalpha():self.senses[w.lower()].append(gloss)
        self.words=set(self.pron) if broad else set(self.pron)&set(self.senses)
        self.by_sound=defaultdict(set)
        for w in self.words:
            for p in self.pron[w]:self.by_sound[p].add(w)
        self.cache={}
        self.pairs=0
        self.cuts=0

    def exchange(self,a,b,side,other_side=None):
        other_side=other_side or side
        key=(a,b,side,other_side)
        if key in self.cache:return self.cache[key]
        self.pairs+=1
        outs={}
        for ca in range(1,len(a)):
            for cb in range(1,len(b)):
                self.cuts+=1
                ap=[a[:ca],a[ca:]];bp=[b[:cb],b[cb:]]
                ia=int(side=='right');ib=int(other_side=='right')
                ap[ia],bp[ib]=bp[ib],ap[ia]
                x,y=ap[0]+ap[1],bp[0]+bp[1]
                if x in self.by_sound and y in self.by_sound:
                    outs.setdefault((x,y),[]).append((ca,cb))
        self.cache[key]=outs
        return outs

    def starts(self,names):
        from itertools import product
        return set(product(*[set(p for n in ns for p in self.pron.get(n,())) for ns in names]))

    def advance(self,states,op):
        i,j,side,*tail=op
        new={}
        for state in states:
            for (a,b),cuts in self.exchange(state[i],state[j],side,tail[0] if tail else side).items():
                s=list(state);s[i]=a;s[j]=b;s=tuple(s)
                new.setdefault(s,(state,cuts[0]))
        return new

    def solve(self,names,ops,target=0,cap=None):
        states=self.starts(names);layers=[{s:None for s in states}];stats=[]
        for op in ops:
            inputs=len(states);new=self.advance(states,op)
            stats.append({'input_states':inputs,'output_states':len(new)})
            layers.append(new);states=new
            if cap is not None and len(new)>cap:return None,stats,layers
        answers=sorted({w for s in states for w in self.by_sound[s[target]]})
        return answers,stats,layers

    def witness(self,layers,final):
        states=[final];cuts=[]
        for layer in reversed(layers[1:]):
            prev,cut=layer[states[-1]];states.append(prev);cuts.append(cut)
        return {'sounds':list(reversed(states)),'cuts':list(reversed(cuts)),
                'words':[[sorted(self.by_sound.get(p,())) for p in s] for s in reversed(states)]}
