"""Joint rule/metric/reference inference from visible labels and radial relations.
Works from the recognized ring, dial and record values alone.
"""
import time
from core import models,literal,lazy


def value_schemes(alphabet):
    # Coordinates are normalized clockwise. Counterclockwise values with the
    # opposite rotation sign give the identical operation, so are not counted
    # a second time. All ten possible origins are actually searched.
    for offset in range(len(alphabet)):
        yield 'initial_distance_'+str(offset), {c:(i+offset)%len(alphabet)for i,c in enumerate(alphabet)}
    for origin in (0,1):
        yield 'alphabet_'+str(origin), {c:(ord(c)-ord('A')+origin)%len(alphabet)for c in alphabet}


def matches(row, result, reference='end', order=1):
    end=row['end']
    if any(c!='.' and result['wheel'][i]!=c for i,c in enumerate(end['wheel'])):
        return False
    if 'record'in end and result['record']!=end['record']:
        return False
    wheel=result['wheel'] if reference=='end' else row['start']['wheel']
    pos=[wheel.index(c)for c in result['record']]
    return pos[::order]==end['record_positions']


def infer(s, ablations=True):
    began=time.perf_counter()
    alphabet=s['target_start']['wheel']
    rows=[s['ordinary']]+s['observations']
    family=models()
    survivors=[];counts=[0]*len(rows);omitted=[[]for _ in rows]
    examined=0
    for scheme,values in value_schemes(alphabet):
        for m in family:
            results=[literal(row['start'],row['tokens'],values,m) for row in rows]
            for reference in ('end','start'):
                for order in (1,-1):
                    examined+=1
                    flags=[matches(row,result,reference,order)for row,result in zip(rows,results)]
                    h={'metric':scheme,'values':values,'reference':reference,'order':order,'model':m}
                    for i in range(len(rows)):
                        counts[i]+=all(flags[:i+1])
                        if ablations and all(f for j,f in enumerate(flags)if j!=i):
                            omitted[i].append(h)
                    if all(flags):survivors.append(h)
    def prediction(h):
        return literal(s['target_start'],s['target_tokens'],h['values'],h['model'])['record']
    predictions=sorted({prediction(h)for h in survivors})
    recovered=[]
    for row in rows:
        ends=[literal(row['start'],row['tokens'],h['values'],h['model'])for h in survivors]
        recovered.append({'wheels':sorted({e['wheel']for e in ends}),'records':sorted({e['record']for e in ends})})
    result={'valid':len(predictions)==1,'unique':len(predictions)==1,
            'solution_count':len(predictions),'answer':predictions[0]if len(predictions)==1 else None,
            'predictions':predictions,'models_examined':examined,'local_models':len(family),
            'survivors':survivors,'successive_survivors':counts,'recovered_endpoints':recovered,
            'hidden_states_unique':all(len(e['wheels'])==len(e['records'])==1 for e in recovered),
            'seconds':time.perf_counter()-began,
            'scope':'Bounded natural local family: rotation sign, feedback source, trigger, timing, transposition, rewrite scope, include-new, persistence and five turn amounts; twelve value metrics; initial/final record reference; both ordinal orders. Counterclockwise metric/sign conjugates are operationally identical. No finite examples exclude arbitrary lookup rules.'}
    if ablations:
        result['ablations']=[{'omitted_row':i+1,'models':len(hs),'predictions':sorted({prediction(h)for h in hs})}for i,hs in enumerate(omitted)]
    if survivors:
        h=survivors[0]
        result['target_steps']=literal(s['target_start'],s['target_tokens'],h['values'],h['model'])['steps']
        standard=dict(direction=1,feedback='visible',trigger='boxed',timing='before',wheel_swap=True,rewrite='all',include_new=True,reset=False,amount='feedback')
        if h['model']==standard:
            result['independent_factorization_matches']=all(lazy(row['start'],row['tokens'],h['values'])['frames']==literal(row['start'],row['tokens'],h['values'],standard)['frames']for row in rows+[{'start':s['target_start'],'tokens':s['target_tokens']}])
    return result
