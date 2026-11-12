from pathlib import Path
from collections import defaultdict
import json
BASE=Path(__file__).parent

def lexicons():
 wn={s.strip('"').upper() for s in (BASE/'wordnik.txt').read_text().splitlines() if s.strip('"').isascii() and s.strip('"').isalpha()}
 cm={s.split()[0].split('(')[0].upper() for s in (BASE/'cmudict.dict').read_text().splitlines() if s and s.split()[0].split('(')[0].isascii() and s.split()[0].split('(')[0].isalpha()}
 return {'wordnik':wn,'cmu':cm}

def relation(s,a,r,aligned=False):
 l,t,rr,b=s;al,at,ar,ab=a
 if r=='above':return b<at and (not aligned or l<=ar and rr>=al)
 if r=='below':return t>ab and (not aligned or l<=ar and rr>=al)
 if r=='inside':return l>al and t>at and rr<ar and b<ab
 if r=='on':return l>=al and rr<=ar and abs(b-at)<=5
 raise ValueError(r)

def build(data,aligned=False):
 tags=[s for s in data['stations'] if s['frame']>=0]; anchors=[]
 for o in data['objects']:
  if o['frame']<0:continue
  if o['kind'] in ['sea','sole','board','note']:
   names={'sea':['sea'],'sole':['sole'],'board':['board'],'note':['tone']}[o['kind']]
   anchors.append({'names':names,'box':o['box'],'frame':o['frame']})
  for part,box in o['parts'].items():
   if part in ['hand','head']:anchors.append({'names':[part],'box':box,'frame':o['frame']})
 knowledge=json.loads((BASE/'english.json').read_text()); graph={}
 for query in set([data['start']]+[t['next'] for t in tags if t['next']]):
  if query not in knowledge:raise ValueError('Unsupported ordinary-language clue '+query)
  dest=set()
  for reading in knowledge[query]:
   for a in anchors:
    if reading['anchor'] not in a['names']:continue
    for i,s in enumerate(tags):
     if s['frame']!=a['frame']:continue
     if reading['subject'] and reading['subject']!=s['kind']:continue
     if relation(s['box'],a['box'],reading['relation'],aligned):dest.add(i)
  graph[query]=sorted(dest)
 return tags,graph

def enumerate_words(start,tags,graph,words,reverse):
 trie={}
 for w in words:
  branch=trie
  for c in w[::-1] if reverse else w:branch=branch.setdefault(c,{})
  branch['$']=True
 found=[];stats=defaultdict(int)
 def walk(q,branch,raw,path):
  stats['query_expansions']+=1
  for i in graph[q]:
   stats['landing_visits']+=1;t=tags[i];child=branch
   for c in t['letter']:child=child.get(c,{})
   if not child:continue
   text=raw+t['letter'];p=path+[i]
   if t['terminal']:
    if '$' in child:found.append({'answer':text[::-1] if reverse else text,'raw':text,'path':p})
   else:walk(t['next'],child,text,p)
 walk(start,trie,'',[])
 return found,dict(stats)

def compute(data):
 raw=data['example_raw'];out=data['example_output']
 if out==raw[::-1] and out!=raw:reverse=True
 elif out==raw and out!=raw[::-1]:reverse=False
 else:raise ValueError('Example does not license a unique orientation')
 tags,graph=build(data);results={};all_answers=set()
 for name,words in lexicons().items():
  paths,stats=enumerate_words(data['start'],tags,graph,words,reverse)
  results[name]={'lexicon_size':len(words),'solutions':paths,'statistics':stats}
  all_answers|={p['answer'] for p in paths}
 unique=len(all_answers)==1 and all(len({p['answer'] for p in r['solutions']})==1 for r in results.values())
 return {'valid':unique,'unique':unique,'solution_count':len(all_answers),'answer':next(iter(all_answers)) if unique else None,'answers':sorted(all_answers),'graph':graph,'tags':tags,'lexical_proof':results,'example':{'raw':raw,'output':out,'orientation':'reverse' if reverse else 'forward'}}
