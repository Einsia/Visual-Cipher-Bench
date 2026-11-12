"""Short route: invert counter losses into possible ordered departures.
Assumes decrement/equality/cycle candidates, but does not know the hop law.
"""
from itertools import product
from time import perf_counter

def solve(examples):
 start=perf_counter();nodes=0;segments=[];hypotheses=[]
 for rotation in [-1,1]:
  batches=[]
  for d in examples:
   for left,right,t0,t1 in zip(d['states'],d['states'][1:],d['times'],d['times'][1:]):
    loss=[a-b for a,b in zip(left['counts'],right['counts'])]
    assert min(loss)>=0 and sum(loss)==t1-t0
    traces=[]
    def walk(counts,letters,p,remaining,moves):
     nonlocal nodes
     nodes+=1
     if not any(remaining):
      if counts==right['counts'] and letters==right['letters'] and p==right['active']:traces.append(moves)
      return
     if counts[p]<=0 or remaining[p]<=0:return
     a=counts[:];a[p]-=1;rem=remaining[:];rem[p]-=1
     group=[i for i,x in enumerate(a) if x==a[p]]
     result=list(letters)
     for j,i in enumerate(group):result[group[(j+rotation)%len(group)]]=letters[i]
     carried=group[(group.index(p)+rotation)%len(group)]
     for target in ([right['active']] if not any(rem) else [i for i,v in enumerate(rem) if v]):
      move=dict(source=p,carried=carried,target=target,population=len(group),changed=sum(x!=y for x,y in zip(result,letters)),distinct=len(set(letters[i] for i in group)),old=counts[p],new=a[p],unchanged=sum(x==y for x,y in zip(result,letters)),n=len(a))
      walk(a,''.join(result),target,rem,moves+[move])
    walk(left['counts'][:],left['letters'],left['active'],loss,[])
    batches.append(traces)
    segments.append(dict(rotation=rotation,times=[t0,t1],example=d['result'],trace_count=len(traces)))
  for origin,quantity,direction in product(['source','carried'],['population','changed','distinct','old','new','unchanged'],[-1,1]):
   if all(any(all((m[origin]+direction*m[quantity])%m['n']==m['target'] for m in trace) for trace in traces) for traces in batches):
    hypotheses.append(dict(rotation=rotation,origin=origin,quantity=quantity,direction=direction))
 return dict(seconds=perf_counter()-start,search_nodes=nodes,hop_hypotheses_tested=48,segments=segments,survivors=hypotheses,skipped_conditions='Assumes decrement-first and updated equality rather than proving them. The broad transition-family check separately tests those alternatives. Uses every printed interval endpoint and reconstructs missing departures from counter losses.')
