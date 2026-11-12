"""Exact finite-language composition, driven by recovered pixels, with no target answer."""
from pathlib import Path
import json,time
from .finite import Lang,make_trie
from .rewrites import preimages
ROOT=Path(__file__).resolve().parent
# Ordinary names of recognized picture classes, independent of positions or ordering.
ALIASES={
 'CAR':['CAR','AUTO','AUTOMOBILE'], 'COT':['COT','BED'], 'COTTON':['COTTON'], 'KEY':['KEY'],
 'PIE':['PIE','TART','PASTRY'], 'FIR':['FIR','TREE','PINE','SPRUCE'],
 'ROPE':['ROPE','CORD','LINE'], 'EYE':['EYE'], 'CHAIR':['CHAIR','SEAT'],
 'RAIN':['RAIN','SHOWER','DRIZZLE'], 'LANES':['LANES','ROAD','ROADS','PATHS','STREETS','HIGHWAY'],
 'LANE':['LANE','ROAD','PATH','STREET','HIGHWAY'], 'CHARM':['CHARM','PENDANT','AMULET','CLOVER','TALISMAN'],
 'ARM':['ARM','FOREARM','LIMB'], 'AMBER':['AMBER','FOSSIL','GEM','STONE','RESIN'],
 'TEA':['TEA'], 'BOX':['BOX']}
class Engine:
 def __init__(self):
  D=json.loads((ROOT/'pronunciations.json').read_text());self.words=set(json.loads((ROOT/'english_words.json').read_text()))
  phones=sorted({p for v in D.values() for ps in v for p in ps});enc=dict(zip(phones,map(chr,range(65,65+len(phones)))))
  self.dp={w:[''.join(enc[x] for x in ps) for ps in pp] for w,pp in D.items()}
  self.read=make_trie((w,ps) for w,pp in self.dp.items() for ps in pp);self.write=make_trie((ps,w) for w,pp in self.dp.items() for ps in pp)
 def pairs(self,op,broad):
  mode,a,b=op
  for aa in ALIASES.get(a,[a]) if broad else [a]:
   for bb in ALIASES.get(b,[b]) if broad else [b]:
    if mode=='pencil':yield aa,bb
    else:
     for x in self.dp[aa]:
      for y in self.dp[bb]:yield x,y
 def step(self,l,r,op,broad=False):
  if op[0]=='speaker':r=l.transduce(r,self.read);l,r=l.compact(r)
  out=0
  for a,b in self.pairs(op,broad):out=l.union(out,l.rewrite(r,a,b))
  l,r=l.compact(out)
  if op[0]=='speaker':r=l.transduce(r,self.write);l,r=l.compact(r)
  return l,r
 def examples(self,examples):
  records=[]
  for e in examples:
   l=Lang();r=l.literal(e['before'])
   for op in e['operators']:l,r=self.step(l,r,op)
   if any(op[0]=='speaker' for op in e['operators']):
    t=Lang();tr=t.many(self.words);r=l.intersect(r,tr,t)
   outs=list(l.words(r));records.append({'input':e['before'],'computed_outputs':outs,'printed_output':e['after'],'passed':outs==[e['after']]})
  return records
 def solve(self,data,broad=False):
  start=time.monotonic();ops=data['operators'];slots=data['answer_slots'];targets={w for w in self.words if len(w)==slots};stats=[]
  pivots=[i for i,op in enumerate(ops) if op[0]=='speaker'];pivot=max(pivots) if pivots else -1
  if pivot<0:
   l=Lang();r=l.literal(data['start'])
   for op in ops:l,r=self.step(l,r,op,broad)
   t=Lang();tr=t.many(targets);r=l.intersect(r,tr,t)
  else:
   # Exact dictionary-bounded inverse of the trailing spelling operations.
   tail=targets
   for op in reversed(ops[pivot+1:]):tail={s for w in tail for a,b in self.pairs(op,broad) for s in preimages(w,a,b)}
   t=Lang();tr=t.many(tail);tr=t.transduce(tr,self.read);t,tr=t.compact(tr)
   l=Lang();r=l.literal(data['start'])
   for i,op in enumerate(ops[:pivot]):
    l,r=self.step(l,r,op,broad);stats.append({'operator':i+1,'states':len(l.nodes),'distinct_strings':l.count(r)})
   r=l.transduce(r,self.read);l,r=l.compact(r);stats.append({'before_last_sound_states':len(l.nodes)})
   out=0
   for a,b in self.pairs(ops[pivot],broad):
    # Form a complete inverse superset, meet it with the incoming language,
    # then perform the exact obligatory rewrite and target intersection.
    inv=t.loose_preimage(tr,a,b);u,ur=t.compact(inv)
    candidate=l.intersect(r,ur,u)
    transformed=l.rewrite(candidate,a,b)
    transformed=l.intersect(transformed,tr,t)
    out=l.union(out,transformed)
   l,r=l.compact(out);stats.append({'matched_phone_strings':l.count(r),'matched_phone_states':len(l.nodes)})
   r=l.transduce(r,self.write);l,r=l.compact(r)
   u=Lang();ur=u.many(tail);r=l.intersect(r,ur,u);l,r=l.compact(r)
   stats.append({'suffix_spelling_inputs':list(l.words(r))})
   for op in ops[pivot+1:]:l,r=self.step(l,r,op,broad)
   u=Lang();ur=u.many(targets);r=l.intersect(r,ur,u)
  answers=sorted(l.words(r))
  return {'outputs':answers,'unique':len(answers)==1,'solution_count':len(answers),'stats':stats,'broad_aliases':broad,'seconds':time.monotonic()-start,'lexical_entries':len(self.dp),'terminal_forms_before_length':len(self.words),'terminal_forms_at_visible_length':len(targets),'limits':'Finite bundled pronunciation and word domain, all segmentations and no intermediate count/frequency cap; does not quantify all English dialects.'}
