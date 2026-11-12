"""Infer finite-state local rules from pixel observations; no puzzle constants."""
import itertools
import numpy as np
from functools import lru_cache

def batch(word,tables,scope,reverse,right):
 n=len(word);m=len(tables);a=np.tile(word,(m,1));length=np.full(m,n);row=np.arange(m)
 for _ in range(n//2):
  equal=(a[:,:-1]==a[:,1:])&(np.arange(n-1)<(length-1)[:,None]);live=equal.any(1)
  if not live.any():break
  pos=n-2-equal[:,::-1].argmax(1) if right else equal.argmax(1)
  deleted=a[row,pos];rule=tables[row,deleted-1];state=rule>>4
  old=a.copy();oldlen=length.copy();length-=live*2
  for j in range(n-2):
   mask=live&(j>=pos)&(j<length);a[:,j]=np.where(mask,old[:,j+2],a[:,j])
  for j in (range(n-1,-1,-1) if reverse else range(n)):
   valid=live&(j<length)
   if scope=='suffix':valid&=j>=pos
   if scope=='prefix':valid&=j<pos
   x=a[:,j].copy();eq=(x==deleted)
   a[:,j]=np.where(valid&(state==1)&~eq,6-x-deleted,x)
   state=np.where(valid,(rule>>(2*state+eq))&1,state)
 return a,length

def infer(examples):
 tables=np.array(list(itertools.product(range(32),repeat=3)),dtype=np.int64);models=[];counts=[0]*len(examples)
 for scope,rev,right in itertools.product(('suffix','prefix','global'),(False,True),(False,True)):
  t=tables
  for i,e in enumerate(examples):
   out,n=batch(e['word'],t,scope,rev,right);end=e['terminal'];ok=(n==len(end))&(out[:,:len(end)]==end).all(1);t=t[ok];counts[i]+=len(t)
   if not len(t):break
  for r in t:models.append({'table':r.tolist(),'scope':scope,'reverse':rev,'right':right})
 return models,counts

def step(word,i,model):
 a=word[i];out=list(word[:i]+word[i+2:]);rule=model['table'][a-1];s=rule>>4
 indices=list(range(i,len(out))) if model['scope']=='suffix' else list(range(i)) if model['scope']=='prefix' else list(range(len(out)))
 if model['reverse']:indices.reverse()
 for j in indices:
  x=out[j];eq=int(x==a)
  if s and not eq:out[j]=6-a-x
  s=(rule>>(2*s+eq))&1
 return tuple(out)

def terminals(word,model):
 visited=set();edges=[]
 def visit(w):
  if w in visited:return set()
  visited.add(w);ids=[i for i in range(len(w)-1) if w[i]==w[i+1]]
  if not ids:return {w}
  result=set()
  for i in ids:
   nxt=step(w,i,model);edges.append([list(w),i,list(nxt)]);result|=visit(nxt)
  return result
 ends=visit(tuple(word));return sorted(ends),edges,len(visited)

def solve(data):
 models,counts=infer(data['examples'])
 if not models:raise ValueError('No rule fits the visible examples in the tested local family')
 answers=set();details=[]
 for m in models:
  row_labels=[];rows=[]
  for q in data['queries']:
   ends,edges,states=terminals(q['word'],m)
   matches=[o['label'] for o in q['options'] if tuple(o['word']) in ends]
   if len(ends)!=1 or len(matches)!=1:raise ValueError('Query does not have one terminal and one matching option')
   row_labels.append(matches[0]);rows.append({'endpoints':[list(t) for t in ends],'label':matches[0],'edges':edges,'state_count':states})
  answers.add(''.join(row_labels));details.append(rows)
 if len(answers)!=1:raise ValueError('Surviving rules predict different answers')
 return {'answer':next(iter(answers)),'models':models,'tested_models':393216,'survivors_after_examples':counts,'query_proof':details[0],'solution_count':1,'unique':True}
