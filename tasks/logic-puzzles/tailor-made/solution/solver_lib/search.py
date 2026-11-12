"""Complete search over values recognized from the supplied PNG.

The static engine is generic C++.
It contains neither this instance nor its answer. Cap=2 distinguishes unique
from multiple solutions; complete=True certifies full enumeration.
"""
import json,subprocess,tempfile
from pathlib import Path

def exhaustive(nums_a,refs_a,nums_b,refs_b,edges,workers=8):
    codes=sorted(5*a+b for a,b in edges)
    rows=[nums_a,refs_a,nums_b,refs_b,codes]
    data=f'{len(nums_a)} {len(nums_b)} {len(edges)}\n'+'\n'.join(' '.join(map(str,row)) for row in rows)+'\n'
    with tempfile.TemporaryDirectory(prefix='tailor-pixel-') as d:
        p=Path(d)/'observed.txt';p.write_text(data)
        engine=Path(__file__).resolve().parent/'native/exact5'
        result=json.loads(subprocess.run([str(engine),str(p),'2','0'],capture_output=True,text=True,check=True).stdout)
    models=[]
    for model in result['models']:
        A,B=model['A'],model['B'];L=A['lengths']+B['lengths'];V=A['sums']+B['sums'];R=[5+x for x in A['targets']]+B['targets'];trace=[]
        for code in model['schedule']:
            a,b=code//5,5+code%5;rhs=L[a]*L[R[b]]+L[b]*L[R[a]]
            assert V[a]+V[b]==rhs
            before=V.copy();V[a],V[b]=V[b],V[a]
            trace.append(dict(edge=code,lhs=before[a]+before[b],rhs=rhs,before=before,after=V.copy()))
        assert sorted(model['schedule'])==codes
        models.append(dict(A_ends=A['ends'],B_ends=B['ends'],A_lengths=A['lengths'],B_lengths=B['lengths'],initial_sums=A['sums']+B['sums'],
                           schedule=[edges.index([c//5,c%5]) for c in model['schedule']],trace=trace))
    return dict(solution_count=result['solutions'],unique=result['complete'] and result['solutions']==1,complete=result['complete'],models=models,
                seconds=result['seconds'],layout_pairs=result['pairs_seen'],multiset_survivors=result['multiset_pass'],schedule_nodes=result['schedule_nodes'],engine='generic exhaustive static C++')
