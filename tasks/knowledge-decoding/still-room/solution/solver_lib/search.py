"""Generic cyclic all-different letter CSP. Inputs come from PNG transcription."""
import random
def candidates(words,loops):
 options=[]
 for loop in loops:
  ds=[]
  for clue,word in words:
   if len(word)!=len(loop):continue
   for direction in [1,-1]:
    for offset in range(len(word)):
     seq=''.join(word[(offset+direction*i)%len(word)] for i in range(len(word)))
     ds.append((clue,word,seq,offset,direction))
  options.append(ds)
 return options

def solve(loops,options,givens={},limit=2,random_seed=None,budget=1000000):
 # Bitset forward checking with arc consistency at every branch.
 rng=random.Random(random_seed);n=len(loops);inc={}
 for i,loop in enumerate(loops):
  for j,cell in enumerate(loop):inc.setdefault(cell,[]).append((i,j))
 edges=[];nei=[[] for _ in loops]
 for c,occ in inc.items():
  if len(occ)==2:
   (i,pi),(j,pj)=occ;edges.extend([(i,pi,j,pj),(j,pj,i,pi)]);nei[i].append((pi,j,pj));nei[j].append((pj,i,pi))
 char_masks=[];clue_masks=[]
 for ds,loop in zip(options,loops):
  cm=[{} for _ in loop];ids={}
  for k,(clue,word,seq,off,d) in enumerate(ds):
   ids[clue]=ids.get(clue,0)|(1<<k)
   for pos,ch in enumerate(seq):cm[pos][ch]=cm[pos].get(ch,0)|(1<<k)
  char_masks.append(cm);clue_masks.append(ids)
 domains=[(1<<len(ds))-1 for ds in options]
 for c,ch in givens.items():
  for i,pos in inc[c]:domains[i]&=char_masks[i][pos].get(ch,0)
 count=0;out=[]
 def bits(mask):
  while mask:
   bit=mask&-mask;yield bit.bit_length()-1;mask-=bit
 def propagate(dom):
  changed=True
  while changed:
   changed=False
   if any(x==0 for x in dom):return False
   # Arc consistency at shared letter cells.
   for i,pi,j,pj in edges:
    mask=0
    for ch,m in char_masks[i][pi].items():
     if m&dom[i]:mask|=char_masks[j][pj].get(ch,0)
    v=dom[j]&mask
    if v!=dom[j]:
     if not v:return False
     dom[j]=v;changed=True
   # A domain with only one clue owns that clue, even before its rotation is fixed.
   owners={}
   for i,d in enumerate(dom):
    cs=[cl for cl,m in clue_masks[i].items() if d&m]
    if len(cs)==1:
     cl=cs[0]
     if cl in owners:return False
     owners[cl]=i
   for cl,i in owners.items():
    for j in range(n):
     if i==j:continue
     v=dom[j]&~clue_masks[j].get(cl,0)
     if v!=dom[j]:
      if not v:return False
      dom[j]=v;changed=True
  return True
 def visit(dom):
  nonlocal count
  count+=1
  if count>budget:raise RuntimeError('search budget exhausted')
  if not propagate(dom):return
  pending=[i for i,d in enumerate(dom) if d.bit_count()>1]
  if not pending:
   sol=[options[i][d.bit_length()-1] for i,d in enumerate(dom)]
   out.append(sol);return
  i=min(pending,key=lambda j:(dom[j].bit_count(),-len(nei[j])))
  vals=list(bits(dom[i]))
  if random_seed is not None:rng.shuffle(vals)
  for k in vals:
   sub=dom.copy();sub[i]=1<<k;visit(sub)
   if len(out)>=limit:return
 visit(domains)
 return out,count
