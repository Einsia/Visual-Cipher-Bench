"""Exhaustive small checks. Run python -m solver_lib.selftest from the solution directory."""
import itertools
import json
import random
import subprocess
from .cnf import CNF,build
from .model import model
from .search import ENGINE,solve


def native(c,block=()):
    text=c.text(20)+str(len(block))+' '+' '.join(map(str,block))+'\n'
    return json.loads(subprocess.run([str(ENGINE)],input=text,text=True,
                                    capture_output=True,check=True,timeout=25).stdout)


def brute(program,clues):
    n=len(program)
    permutations=list(itertools.permutations(range(n)))
    swaps=[(0,0)]+list(itertools.combinations(range(n),2))
    found=set()
    def walk(P,B):
        if len(P)==n+1:
            for t,(a,b) in enumerate(program,1):
                x,y=P[B[t-1][a]+1][a],P[B[t-1][b]+1][b]
                expected=[y if z==x else x if z==y else z for z in P[t-1]]
                if P[t]!=expected:return
            for a,b,tw,dw,sign in clues:
                if P[B[-1][tw]+1][a]-P[B[-1][tw]+1][b]!=sign*(B[-1][dw]+1):return
            found.add(json.dumps(dict(P=P,B=B),sort_keys=True));return
        a,b=program[len(P)-1]
        for x,y in swaps:
            p=[y if z==x else x if z==y else z for z in P[-1]]
            badges=list(B[-1]);ca,cb=p.index(badges[a]),p.index(badges[b])
            badges[ca],badges[cb]=badges[cb],badges[ca]
            walk(P+[p],B+[badges])
    for p in permutations:
        for b in permutations:walk([list(p)],[list(b)])
    return found


def main():
    rng=random.Random(73)
    for case in range(300):
        n=rng.randrange(1,10);c=CNF()
        for _ in range(n):c.var()
        for _ in range(rng.randrange(1,60)):
            c.clause(*[2*rng.randrange(n)+rng.randrange(2) for _ in range(rng.randrange(6))])
        expected={v for v in itertools.product([0,1],repeat=n)
                  if all(any(v[l//2]^(l&1) for l in cl) for cl in c.cs)}
        out=native(c,list(range(n)))
        assert out['result']==bool(expected),(case,out)
        assert len(out['models'])==min(2,len(expected))
        assert {tuple(v) for v in out['models']}<=expected
        if expected:assert out['second']==(len(expected)>1)
    print('300 random CNFs: satisfiability and second-model exclusion agree with brute force',flush=True)
    counts={'zero':0,'one':0,'many':0}
    for case in range(40):
        n=3;names=['ABC','DEF','GHI']
        pairs=list(itertools.combinations_with_replacement(range(n),2))
        program=[list(rng.choice(pairs)) for _ in range(n)]
        candidates=brute(program,[]);clues=[]
        if candidates:
            h=json.loads(rng.choice(sorted(candidates)))
            for _ in range(rng.randrange(1,9)):
                a,b=rng.sample(range(n),2);tw=rng.randrange(n)
                t=h['B'][-1][tw]+1;diff=h['P'][t][a]-h['P'][t][b]
                dw=h['B'][-1].index(abs(diff)-1)
                clues.append([a,b,tw,dw,1 if diff>0 else -1])
        expected=brute(program,clues)
        s,P,B=model(names,program,clues);c,xs=build(s);found=set()
        while True:
            out=native(c)
            assert out['result']>=0
            if out['result']==0:break
            values=out['models'][0]
            assignment=[next(k for k,z in enumerate(row) if values[z//2]) for row in xs]
            h={key:[[assignment[v] for v in row] for row in rows] for key,rows in [('P',P),('B',B)]}
            found.add(json.dumps(h,sort_keys=True))
            c.clause(*[xs[v][assignment[v]]^1 for v in s.core])
        assert found==expected,(case,len(found),len(expected))
        proof=solve(names,program,clues,20,2)
        found={json.dumps(h,sort_keys=True) for h in proof['solutions']}
        assert proof['complete'] and found<=expected
        assert (len(found)==len(expected) if len(expected)<2 else len(found)>=2)
        if len(expected)==1:assert proof['exhausted']
        counts['zero' if not expected else 'one' if len(expected)==1 else 'many']+=1
    assert all(counts.values()),counts
    print('40 complete n=3 solution sets and partitioned uniqueness decisions agree:',counts,flush=True)
    timed=solve(names,program,clues,0,2)
    assert not timed['complete'] and not timed['exhausted']
    print('An expired deadline cannot certify uniqueness',flush=True)


if __name__=='__main__':main()
