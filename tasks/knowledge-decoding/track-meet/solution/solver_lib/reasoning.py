"""Independent spelled-state enumeration from parsed pictures, words and links."""
from itertools import product
from lexicon import Lexicon
from pixels import ALIASES,need

def word(v):return (''.join(x or '' for x in v).lower() or None) if isinstance(v,list) else (v.lower() if v else None)
# Usual grapheme sounds, not letter-name pronunciations, for printed consonant portions.
CONSONANTS={'b':('B',),'c':('K','S'),'d':('D',),'f':('F',),'g':('G','JH'),'h':('HH',),'j':('JH',),'k':('K',),'l':('L',),'m':('M',),'n':('N',),'p':('P',),'q':('K',),'r':('R',),'s':('S','Z'),'t':('T',),'v':('V',),'w':('W',),'y':('Y',),'z':('Z',)}
def split_fits(L,v,reading,cut,literal):
 if not isinstance(v,list) or not all(v):return True
 pre,suf=(x.lower() for x in v)
 if literal:return tuple(pre)==reading[:cut] and tuple(suf)==reading[cut:]
 pp=set(L.pron.get(pre,()))
 if all(ch in CONSONANTS for ch in pre):pp.update(product(*(CONSONANTS[ch] for ch in pre)))
 sp=set(L.pron.get(suf,()))
 # At least one lexical/consonant side must support the printed cut.
 return bool((pp and reading[:cut] in pp) or (sp and reading[cut:] in sp))

def enumerate_states(L,names,ops,rows,target,literal=False):
 stats={'initial_candidates':0,'states_visited':0,'cuts_tried':0,'terminal_paths':0};finals=set();witnesses={};cache={}
 def exchange(a,b,sa,sb):
  key=(a,b,sa,sb)
  if key in cache:return cache[key]
  out=[]
  for pa,pb in product([tuple(a)] if literal else L.pron[a],[tuple(b)] if literal else L.pron[b]):
   for ca in range(1,len(pa)):
    for cb in range(1,len(pb)):
     stats['cuts_tried']+=1;ap=[pa[:ca],pa[ca:]];bp=[pb[:cb],pb[cb:]];ia=int(sa=='right');ib=int(sb=='right');ap[ia],bp[ib]=bp[ib],ap[ia];x=ap[0]+ap[1];y=bp[0]+bp[1]
     xs=[''.join(x)] if literal and ''.join(x) in L.words else ([] if literal else L.by_sound.get(x,()))
     ys=[''.join(y)] if literal and ''.join(y) in L.words else ([] if literal else L.by_sound.get(y,()))
     for wx,wy in product(xs,ys):out.append((wx,wy,{'readings':[pa,pb],'cuts':[ca,cb],'sounds':[x,y]}))
  cache[key]=out;return out
 def fits(st,row):return all(word(v) in (None,'?',st[j]) for j,v in enumerate(row))
 def rec(st,k,path):
  stats['states_visited']+=1
  if k==len(ops):
   stats['terminal_paths']+=1;finals.add(st);witnesses.setdefault(st[target],path);return
  i,j,sa,sb=ops[k]
  for x,y,detail in exchange(st[i],st[j],sa,sb):
   ns=list(st);ns[i],ns[j]=x,y;ns=tuple(ns)
   valid=all(split_fits(L,rows[k][col],reading,cut,literal)
             for col,reading,cut in zip((i,j),detail['readings'],detail['cuts']))
   if valid and fits(ns,rows[k+1]):rec(ns,k+1,path+[{'before':st,'operation':ops[k],**detail,'after':ns}])
 for st in product(*names):
  if all(w in L.words for w in st) and fits(st,rows[0]):stats['initial_candidates']+=1;rec(st,0,[])
 return {'answers':sorted({s[target] for s in finals}),'final_states':[list(s) for s in sorted(finals)],'witnesses':witnesses,'statistics':stats}

def compute(data):
 L=Lexicon();e=data['example'];p=data['problem']
 en=[]
 for icon,v,printed in zip(e['icons'],e['rows'][0],e['input_words']):
  t=word(printed) or word(v);en.append([t] if t else ALIASES.get(icon,[]))
 need(all(en),'Missing example input')
 ex=enumerate_states(L,en,e['operations'],e['rows'],2)
 need(len(ex['final_states'])==1,'Example has no unique completed state')
 need(ex['statistics']['terminal_paths']==1,'Example hidden states/cuts are ambiguous')
 ex_literal=enumerate_states(L,en,e['operations'],e['rows'],2,literal=True)
 names=[ALIASES[i] for i in p['icons']]
 result=enumerate_states(L,names,p['operations'],p['rows'],p['target'])
 literal=enumerate_states(L,names,p['operations'],p['rows'],p['target'],literal=True)
 return {'example':ex,'example_literal_alternative':ex_literal,'result':result,'literal_alternative':literal,'lexicon_words':len(L.words),'aliases':names}
