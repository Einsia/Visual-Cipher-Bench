"""Search a lexicon for a closed chain of pixel-transcribed operations."""
from collections import defaultdict
from functools import lru_cache
from itertools import product
from pathlib import Path
import json
import re
import string

DATA = Path(__file__).parent
# Ordinary names for the recognized physical objects. Every alternative is
# tried; a repeated picture must have the same name throughout the chain.
OBJECT_NAMES = {'string_ball': ('ball', 'cable', 'cord', 'filament', 'fishhook', 'fishinghook', 'fishingline', 'hook', 'lace', 'lasso', 'lead', 'leader', 'leash', 'line', 'lure', 'reel', 'rope', 'snood', 'spool', 'string', 'tackle', 'tether', 'thread', 'twine', 'wire', 'yarn'), 'cereal_ear': ('barley', 'cereal', 'corn', 'ear', 'grain', 'head', 'oat', 'oats', 'rice', 'rye', 'seed', 'spike', 'stalk', 'wheat'), 'ray': ('devilfish', 'fish', 'kite', 'manta', 'mantaray', 'ray', 'skate', 'stingray')}


def edit_sequence(sequence, sign, operand):
    """Delete a contiguous block or insert one, preserving everything else."""
    if sign == '-':
        for i in range(len(sequence)-len(operand)+1):
            if sequence[i:i+len(operand)] == operand:
                yield sequence[:i] + sequence[i+len(operand):]
    elif sign == '+':
        for i in range(len(sequence)+1):
            yield sequence[:i] + operand + sequence[i:]
    else:
        raise ValueError(f'Unknown operation: {sign}')


class Lexicon:
    def __init__(self):
        raw = json.loads((DATA/'lexicon.json').read_text())
        self.words = {w: {tuple(p) for p in pronunciations}
                      for w, pronunciations in raw.items() if w.isalpha()}
        self.cmu = defaultdict(set)
        for line in (DATA/'cmudict.dict').read_text().splitlines():
            fields=line.split()
            if not fields or fields[0].startswith(';;;'):
                continue
            word=re.sub(r'\(\d+\)$','',fields[0]).upper()
            phones=tuple(re.sub(r'\d','',p) for p in fields[1:])
            self.cmu[word].add(phones)
        # Alphabet names are legitimate rebus states, including letters that
        # are absent from a particular release of a general lexical database.
        for ch in string.ascii_uppercase:
            if ch in self.cmu:
                self.words.setdefault(ch,set()).update(self.cmu[ch])
        self.by_sound=defaultdict(set)
        for word, pronunciations in self.words.items():
            for p in pronunciations:
                self.by_sound[p].add(word)

    def pronunciations(self, word):
        word=word.upper()
        return self.cmu.get(word) or self.words.get(word,set())

    @lru_cache(maxsize=100000)
    def transform(self, source, mode, operands):
        if mode=='letters':
            states={tuple(source)}
            for sign,word in operands:
                states={r for state in states for r in edit_sequence(state,sign,tuple(word))}
            return frozenset(''.join(s) for s in states if ''.join(s) in self.words)
        states=set(self.words.get(source,()))
        if len(operands)==2 and tuple(o[0] for o in operands)==('-','+'):
            old,new=operands[0][1],operands[1][1]
            changed=set()
            for state in states:
                for a,b in product(self.pronunciations(old),self.pronunciations(new)):
                    for i in range(len(state)-len(a)+1):
                        if state[i:i+len(a)]==a:changed.add(state[:i]+b+state[i+len(a):])
            return frozenset(w for state in changed for w in self.by_sound.get(state,()))
        for sign,word in operands:
            sounds=self.pronunciations(word)
            states={r for state in states for sound in sounds
                    for r in edit_sequence(state,sign,sound)}
        return frozenset(w for state in states for w in self.by_sound.get(state,()))


def parse_operations(tokens):
    if not tokens or len(tokens)%2:
        raise ValueError('An operation needs alternating signs and operands')
    parsed=[]
    for sign,operand in zip(tokens[::2],tokens[1::2]):
        if sign.kind!='text' or sign.value not in ('+','-'):
            raise ValueError('Unreadable operation direction')
        if operand.kind=='icon' and operand.value not in OBJECT_NAMES:
            raise ValueError(f'Unknown object: {operand.value}')
        if operand.kind=='choice' and any(v not in OBJECT_NAMES for v in operand.value.split('|')):
            raise ValueError('Unknown picture-frame candidate')
        if operand.kind=='slots' and (not operand.value or set(operand.value)!={'?'}):
            raise ValueError('Malformed unfilled letter cells')
        if operand.kind=='text' and not operand.value.isalpha():
            raise ValueError(f'Unreadable operand: {operand.value}')
        parsed.append((sign.value,operand.value,operand.kind))
    return tuple(parsed)


class Search:
    """Generic finite lexical constraint search over an unordered set of edits.

    Empty cells are independent unknown characters, not a substitution code.
    Each block is contiguous. Replacements occupy the removed block's position; standalone additions
    may be inserted anywhere. No word, letter value or edit order is supplied.
    """
    def __init__(self, lexicon, rows):
        self.lex=lexicon
        self.operations=[(r['mode'],parse_operations(r['tokens'])) for r in rows]
        self.required_pictures=set().union(*(set(r.get('required_pictures',())) for r in rows))
        self.insertion_indices={}
        self.visited=0

    def insertions(self,base,length):
        if length not in self.insertion_indices:
            index=defaultdict(set)
            for word in self.lex.words:
                for i in range(len(word)-length+1):
                    index[word[:i]+word[i+length:]].add((word,word[i:i+length]))
            self.insertion_indices[length]=index
        return self.insertion_indices[length].get(base,())

    def letter_results(self,source,parsed,bindings):
        if len(parsed)==2 and tuple(o[0] for o in parsed)==('-','+'):
            (_,old,ok),(_,new,nk)=parsed
            if ok=='icon':old=bindings[old].upper()
            if nk=='icon':new=bindings[new].upper()
            removed=len(old)
            results=[]
            for i in range(len(source)-removed+1):
                a=source[i:i+removed]
                if ok!='slots' and a!=old:continue
                prefix,suffix=source[:i],source[i+removed:]
                candidates=self.insertions(prefix+suffix,len(new)) if nk=='slots' else [(prefix+new+suffix,new)]
                for target,b in candidates:
                    if target==prefix+b+suffix and target in self.lex.words:
                        results.append((target,(('-',a),('+',b))))
            return results
        states={(source,())}
        for sign,value,kind in parsed:
            following=set()
            for word,ops in states:
                if kind=='slots':
                    n=len(value)
                    if sign=='-':
                        candidates={(word[:i]+word[i+n:],word[i:i+n]) for i in range(len(word)-n+1)}
                    else:
                        candidates=self.insertions(word,n)
                    for target,operand in candidates:following.add((target,ops+((sign,operand),)))
                else:
                    operand=bindings[value].upper() if kind=='icon' else value.upper()
                    for result in edit_sequence(tuple(word),sign,tuple(operand)):
                        following.add((''.join(result),ops+((sign,operand),)))
            states=following
        return [(target,ops) for target,ops in states if target in self.lex.words]

    @lru_cache(maxsize=200000)
    def edges(self,source,index,bound):
        mode,parsed=self.operations[index]
        domains=[value.split('|') if kind=='choice' else [value] for _,value,kind in parsed]
        results=set()
        for selected in product(*domains):
            concrete=tuple((sign,value,'icon' if kind=='choice' else kind)
                           for (sign,_,kind),value in zip(parsed,selected))
            for target,b,ops in self.concrete_edges(source,mode,concrete,bound):
                annotated=tuple(op+(value,) if original[2]=='choice' else op
                                for op,(_,value,_),original in zip(ops,concrete,parsed))
                results.add((target,b,annotated))
        return tuple(sorted(results))

    @lru_cache(maxsize=200000)
    def concrete_edges(self,source,mode,parsed,bound):
        bindings=dict(bound)
        icons=sorted({value for _,value,kind in parsed if kind=='icon' and value not in bindings})
        results=set()
        domains={icon:OBJECT_NAMES[icon] for icon in icons}
        # Filter impossible removal names before taking the Cartesian product.
        # This uses the source's pronunciation, never a target answer.
        if mode=='sound' and parsed and parsed[0][0]=='-' and parsed[0][2]=='icon':
            old=parsed[0][1]
            possible=[bindings[old]] if old in bindings else domains[old]
            feasible=tuple(name for name in possible if any(
                p[i:i+len(q)]==q for p in self.lex.words[source]
                for q in self.lex.pronunciations(name) for i in range(len(p)-len(q)+1)))
            if not feasible:return ()
            if old in domains:domains[old]=feasible
        for names in product(*(domains[icon] for icon in icons)):
            updated={**bindings,**dict(zip(icons,names))};b=tuple(sorted(updated.items()))
            if mode=='letters':
                targets=self.letter_results(source,parsed,updated)
            else:
                if any(kind=='slots' for _,_,kind in parsed):raise ValueError('Uncalibrated phonetic cells')
                ops=tuple((sign,updated[value].upper() if kind=='icon' else value.upper()) for sign,value,kind in parsed)
                targets=[(t,ops) for t in self.lex.transform(source,mode,ops)]
            results.update((target,b,ops) for target,ops in targets)
        return tuple(sorted(results))

    def run(self,start,orders=None):
        count=len(self.operations);solutions=[]
        if orders is not None:
            orders={tuple(o) for o in orders}
        def walk(root,word,unused,bound,path,order,edits):
            self.visited+=1
            if not unused:
                if word==root and self.required_pictures<=dict(bound).keys():
                    solutions.append({'words':path,'order':order,'objects':dict(bound),'operations':edits})
                return
            options=[start] if not order else sorted(unused)
            for i in options:
                if i not in unused:continue
                prefix=tuple(order+[i])
                if orders is not None and not any(o[:len(prefix)]==prefix for o in orders):continue
                for target,b,ops in self.edges(word,i,bound):
                    if len(unused)==1 and target!=root:continue
                    walk(root,target,unused-{i},b,path+[target],order+[i],edits+[ops])
        for source in sorted(self.lex.words):
            walk(source,source,set(range(count)),(),[source],[],[])
        # Duplicate phonetic pronunciations are witnesses, not separate answers.
        unique={json.dumps(s,sort_keys=True):s for s in solutions}
        return list(unique.values())


def solve(examples,rows, *, orders=None, require_unique=True):
    lexicon=Lexicon();engine=Search(lexicon,rows)
    calibration=[]
    for ex in examples:
        tokens=ex['tokens'];equals=[i for i,t in enumerate(tokens) if t.value=='=']
        if equals!=[len(tokens)-2]:raise ValueError('Malformed calibration')
        source,target=tokens[0].value.upper(),tokens[-1].value.upper()
        parsed=parse_operations(tokens[1:-2])
        if ex['mode']!='letters' or any(kind=='icon' for _,_,kind in parsed):raise ValueError('Unsupported calibration')
        witnesses=[ops for result,ops in engine.letter_results(source,parsed,{}) if result==target]
        if not witnesses:raise ValueError('Unfilled-cell calibration does not validate')
        calibration.append({'source':source,'target':target,'inferred':witnesses})
    if not calibration:raise ValueError('Missing calibration of letter cells')
    if any(r.get('mode_marker') not in ('speaker','Aa') for r in rows):raise ValueError('Missing mode evidence')
    starts=[i for i,r in enumerate(rows) if r.get('start')]
    if len(starts)!=1:raise ValueError('Expected exactly one start port')
    solutions=engine.run(starts[0],orders)
    answers=sorted({s['words'][0] for s in solutions})
    evidence={'calibration':calibration,'lexicon_size':len(lexicon.words),'search_nodes':engine.visited,
              'start_edit_from_pixels':starts[0],'answers':answers,
              'orders':sorted({tuple(s['order']) for s in solutions}), 'solutions':solutions,
              'required_pictures':sorted(engine.required_pictures),
              'rules':'All edits once; independent letter cells; contiguous blocks; replacement in place; standalone insertion anywhere; picture domains from unrotated unscaled rectangle containment; every bank picture used; shared object names; exact spelling closure'}
    if require_unique and len(answers)!=1:
        raise ValueError(f'Expected one closed-chain answer; found {len(answers)}: {answers[:20]}')
    return answers[0] if len(answers)==1 else None,evidence
