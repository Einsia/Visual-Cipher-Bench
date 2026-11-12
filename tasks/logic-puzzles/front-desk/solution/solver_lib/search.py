"""Exhaustive disjoint partitions, solved by the bundled dependency-free CDCL engine."""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from .model import model
from .cnf import build

ENGINE=Path(__file__).with_name('engine')


def partitions(s,clues):
    tables=[(vs,rows) for typ,vs,rows in s.cs if typ=='table' and len(rows)>1]
    vs,rows=min(tables,key=lambda q:len(q[1])) if tables else ([],[()])
    terminal=next(rows for typ,cols,rows in s.cs if typ=='table' and cols==s.final)
    times=sorted(set(c[2] for c in clues))
    added=[w for w in times if s.final[w] not in vs]
    joined=set()
    for row in rows:
        fixed=dict(zip(vs,row))
        for final in terminal:
            if all(fixed.get(v,final[j])==final[j] for j,v in enumerate(s.final)):
                joined.add(tuple(row)+tuple(final[w] for w in added))
    return list(vs)+[s.final[w] for w in added],sorted(joined)


def solve(names,program,clues,seconds=1000,workers=8):
    start=time.monotonic()
    deadline=start+seconds
    s,P,B=model(names,program,clues)
    cnf,xs=build(s)
    columns,rows=partitions(s,clues)
    body='\n'.join(str(len(c))+' '+' '.join(map(str,c)) for c in cnf.cs)+'\n'
    indicators=[x//2 for v in s.core for x in xs[v]]
    block=str(len(indicators))+' '+' '.join(map(str,indicators))+'\n'
    digest=hashlib.sha256(body.encode()).hexdigest()

    def task(job):
        i,row=job
        remaining=deadline-time.monotonic()
        if remaining<=0:
            return dict(task=i,result=-1,second=-2,models=[],conflicts=0,decisions=0,seconds=0)
        units=[xs[v][k] for v,k in zip(columns,row)]
        payload=f'{cnf.n} {len(cnf.cs)+len(units)} {remaining}\n'+body
        payload+=''.join(f'1 {u}\n' for u in units)+block
        tick=time.monotonic()
        try:
            proc=subprocess.run([str(ENGINE)],input=payload,text=True,
                                stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                check=True,timeout=remaining+10)
            result=json.loads(proc.stdout)
        except subprocess.TimeoutExpired:
            result=dict(result=-1,second=-2,models=[],conflicts=0,decisions=0)
        result.update(task=i,seconds=time.monotonic()-tick)
        # Independently verify every returned SAT assignment against the input CNF.
        for values in result['models']:
            if len(values)!=cnf.n or any(v not in (0,1) for v in values):
                raise ValueError('Incomplete native SAT assignment')
            if not all(any(values[l//2]^(l&1) for l in clause) for clause in cnf.cs):
                raise ValueError('Native assignment fails an original clause')
            if not all(values[u//2] for u in units):
                raise ValueError('Native assignment leaves its partition')
        return result

    solutions=[]
    evidence=[]
    complete=True
    exhausted=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(task,job) for job in enumerate(rows)]
        for future in concurrent.futures.as_completed(futures):
            result=future.result()
            decided=result['result']==0 or (result['result']==1 and result['second'] in (0,1))
            complete &= decided
            exhausted += result['result']==0 or (result['result']==1 and result['second']==0)
            for values in result.pop('models'):
                assignment=[next(k for k,x in enumerate(row) if values[x//2]) for row in xs]
                solutions.append({key:[[assignment[v] for v in row] for row in rs]
                                  for key,rs in [('P',P),('B',B)]})
            evidence.append(result)
            if len(evidence)%16==0 or len(evidence)==len(rows):
                print(f'{len(evidence)}/{len(rows)} partitions checked; '
                      f'{len(solutions)} histories; {time.monotonic()-start:.1f}s',
                      file=sys.stderr,flush=True)
    # Auxiliary table/case selectors do not count as separate histories.
    histories={json.dumps(h,sort_keys=True) for h in solutions}
    if len(histories)!=len(solutions):
        raise ValueError('Partitions were not disjoint in history space')
    return dict(complete=complete,exhausted=exhausted==len(rows),solutions=solutions,
                nodes=sum(r['decisions'] for r in evidence),
                conflicts=sum(r['conflicts'] for r in evidence),
                tasks=len(rows),tasks_finished=sum(r['result']==0 or
                    (r['result']==1 and r['second'] in (0,1)) for r in evidence),
                task_results=sorted(evidence,key=lambda r:r['task']),
                cnf_sha256=digest,boolean_variables=cnf.n,clauses=len(cnf.cs),
                seconds=time.monotonic()-start,
                status='complete' if complete else 'incomplete')
