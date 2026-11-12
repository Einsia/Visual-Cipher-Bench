"""Exhaustive public-constraint search using the bundled offline native helper.

Splitting by distance rings avoids an excessive snapshot cross-product.
Only constraints recovered from the PNGs are used.
"""
from .finite_engine import solve_grouped

def solve(names,program,clues,seconds=180,workers=8):
    result=solve_grouped(len(names),program,clues,workers,seconds)
    groups=result['groups'];complete=result['complete'];solutions=result['solutions']
    return dict(complete=complete,exhausted=complete,solutions=solutions,
                nodes=result['branches'],conflicts=result['conflicts'],seconds=result['seconds'],
                tasks=len(groups),tasks_finished=sum(g['runs'][-1]['result']=='INFEASIBLE' for g in groups),
                task_results=[dict(values=g['values'],runs=g['runs']) for g in groups],
                model_family='finite-domain CP-SAT; all positions and rings; no supplied history',
                packing=result['packing'],
                status='complete' if complete else 'incomplete')
