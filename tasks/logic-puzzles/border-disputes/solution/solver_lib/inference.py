"""Test natural alternative mechanisms against the sparse PNG observations.

A finite falsification check, not a claim of uniqueness among arbitrary invented rules.
Blank cells are unknown, never zero. Final margins constrain the unshown entries.
No expected masks, example numbers, target solution or answer are embedded here.
"""
import itertools

def infer(original, witnesses, order):
    n=len(original['letters']);b=[[bool(m>>c&1)for c in range(n)]for m in original['masks']]
    counts=original['geometry']['counts'];letters=original['letters']
    neighbors=[[sum(b[rr][cc]for rr,cc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]if 0<=rr<n and 0<=cc<n)for c in range(n)]for r in range(n)]
    initials={'incident_sides':counts,'four_minus_incident_sides':[[4-v for v in row]for row in counts],
              'inside_neighbors':neighbors,'outside_neighbors':[[4-v for v in row]for row in neighbors]}
    for k in range(5):initials['constant_'+str(k)]=[[k]*n for _ in range(n)]
    selections=['inside','outside','whole_line','boundary_cells','signed_line']
    updates=['endpoint_complement','identity','always_complement','same_side_complement','enter_only','leave_only','complement_3','complement_5','recount_destination','reset_zero_on_cross','reset_four_on_cross','increment_on_cross']
    survivors=[];failures={};tested=0
    candidates=itertools.product(initials,selections,['current','initial'],['sum','count','max','min','step_number'],[1,-1],[1,-1],updates)
    for initial,select,sample,agg,rd,cd,update in candidates:
        tested+=1;start=initials[initial];values=[row[:]for row in start];ls=[row[:]for row in letters];failed=None
        for step,op in enumerate(order,1):
            i=op//2;coords=[(i,c)for c in range(n)]if op%2==0 else[(r,i)for r in range(n)]
            use=values if sample=='current'else start
            picked=[use[r][c]*(-1 if select=='signed_line' and not b[r][c] else 1)for r,c in coords if select in ['whole_line','signed_line'] or (select=='inside'and b[r][c]) or (select=='outside'and not b[r][c]) or (select=='boundary_cells'and counts[r][c]>0)]
            k=({'sum':sum,'count':len,'max':lambda a:max(a,default=0),'min':lambda a:min(a,default=0),'step_number':lambda a:step}[agg](picked))*(rd if op%2==0 else cd)
            old=[values[r][c]for r,c in coords];chars=[ls[r][c]for r,c in coords]
            for dest,(r,c)in enumerate(coords):
                src=(dest-k)%n;rr,cc=coords[src];val=old[src];different=b[r][c]!=b[rr][cc]
                flip=(different if update in ['endpoint_complement','complement_3','complement_5']else
                      update=='always_complement' or (update=='same_side_complement'and not different)or
                      (update=='enter_only'and different and b[r][c])or(update=='leave_only'and different and not b[r][c]))
                if flip:val=({'complement_3':3,'complement_5':5}.get(update,4))-val
                if update=='recount_destination':val=counts[r][c]
                elif different and update=='reset_zero_on_cross':val=0
                elif different and update=='reset_four_on_cross':val=4
                elif different and update=='increment_on_cross':val=(val+1)%5
                values[r][c]=val;ls[r][c]=chars[src]
            if step in witnesses:
                seen=witnesses[step]
                if any(v is not None and v!=values[r][c] for r,row in enumerate(seen['values']) for c,v in enumerate(row)) or any(v is not None and v!=ls[r][c] for r,row in enumerate(seen['letters']) for c,v in enumerate(row)):failed=step;break
        if failed is None and 'row_totals' in witnesses[max(witnesses)]:
            seen=witnesses[max(witnesses)];z=[[v*(1 if b[r][c] else -1) for c,v in enumerate(row)]for r,row in enumerate(values)]
            if list(map(sum,z))!=seen['row_totals'] or list(map(sum,zip(*z)))!=seen['column_totals']:failed='margins'
        if failed is None:
            survivors.append(dict(initial=initial,selection=select,sample=sample,aggregate=agg,row_direction=rd,column_direction=cd,update=update))
        else:failures[str(failed)]=failures.get(str(failed),0)+1
    expected=dict(initial='incident_sides',selection='inside',sample='current',aggregate='sum',row_direction=1,column_direction=1,update='endpoint_complement')
    return {'tested':tested,'survivors':survivors,'unique_mechanism':survivors==[expected],'first_rejecting_state_counts':failures,
            'scope':'Natural alternatives for initial counts, sampled region, current/initial values, aggregation, directions and number update. Not all conceivable rules.'}
