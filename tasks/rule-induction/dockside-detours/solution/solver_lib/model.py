"""Movable letters and fixed counters; terminal numbered-slot extraction.
No history/log rule, puzzle transcription or answer is embedded here.
"""
from itertools import product
from collections import Counter

def simulate(counts,start=0,*,rotation=1,carry=True,letters=None,hop_mode="changed"):
    if letters is None: letters=list(range(len(counts)))
    a=list(counts);n=len(a);cards=list(range(n));p=start;states=[];moves=[]
    for _ in range(sum(a)+1):
        states.append(dict(counts=a[:],cards=cards[:],active=p))
        if a[p]==0:return dict(states=states,moves=moves)
        a[p]-=1
        selected=[i for i,v in enumerate(a) if v==a[p]]
        old=cards[:]
        for j,x in enumerate(selected):cards[selected[(j+rotation)%len(selected)]]=old[x]
        moved=selected[(selected.index(p)+rotation)%len(selected)]
        changed=[i for i in range(n) if letters[old[i]]!=letters[cards[i]]]
        hop=len(changed) if hop_mode=="changed" else len(selected)
        q=((moved if carry else p)+hop)%n
        moves.append(dict(source=p,new=a[p],group=selected,carried=moved,hop=hop,target=q,changed=changed))
        p=q
    raise AssertionError('strictly decreasing counter sum')

def independent_simulate(counts,start,letters):
    # Independent inverse mapping, plus an incrementally maintained histogram.
    a=list(counts);n=len(a);location=list(range(n));p=start;states=[];moves=[];bins=Counter(a)
    for _ in range(sum(a)+1):
        inverse=[None]*n
        for card,slot in enumerate(location):inverse[slot]=card
        states.append(dict(counts=a[:],cards=inverse,active=p))
        if not a[p]:return dict(states=states,moves=moves)
        before=a[p];a[p]-=1;bins[before]-=1;bins[before-1]+=1
        positions=sorted(i for i in range(n) if a[i]==a[p]);succ={v:positions[(j+1)%len(positions)] for j,v in enumerate(positions)}
        location=[succ.get(slot,slot) for slot in location]
        after=[None]*n
        for card,slot in enumerate(location):after[slot]=card
        changed=[i for i in range(n) if letters[inverse[i]]!=letters[after[i]]]
        moved=succ[p];h=len(changed);q=(moved+h)%n
        moves.append(dict(source=p,new=a[p],group=positions,carried=moved,hop=h,target=q,changed=changed));p=q
    raise AssertionError()

def visible_states(item,run):
    return [dict(letters=''.join(item['letters'][i] for i in s['cards']),counts=s['counts'],active=s['active']) for s in run['states']]

def answer_for(item,**kwargs):
    run=simulate(item['counts'],item['active'],letters=item['letters'],**kwargs)
    final=run['states'][-1]['cards']
    return ''.join(item['letters'][final[slot-1]] for slot in item['read_slots']),run

def rule_family():
    for state,key,rel,self_count,zeros,rotation,carry,hop,direction,offset in product(
        ['updated','before','initial'],['new','old'],['eq','ne','lt','le','gt','ge'],[True,False],[True,False],[-1,0,1],[False,True],['population','old','new','changed','distinct','unchanged'],[-1,1],[-1,0]):
        yield dict(state=state,key=key,relation=rel,self_count=self_count,zeros=zeros,rotation=rotation,carry=carry,hop=hop,direction=direction,offset=offset)

def predict_transition(rule,counts,cards,p,initial):
    a=list(counts);a[p]-=1
    vals={'updated':a,'before':counts,'initial':initial}[rule['state']];key=a[p] if rule['key']=='new' else counts[p]
    compare={'eq':lambda x:x==key,'ne':lambda x:x!=key,'lt':lambda x:x<key,'le':lambda x:x<=key,'gt':lambda x:x>key,'ge':lambda x:x>=key}[rule['relation']]
    group=[i for i,v in enumerate(vals) if compare(v) and (rule['self_count'] or i!=p) and (rule['zeros'] or v!=0)]
    result=list(cards);moved=p
    for j,x in enumerate(group):
        to=group[(j+rule['rotation'])%len(group)];result[to]=cards[x]
        if x==p:moved=to
    h={'population':len(group),'old':counts[p],'new':a[p],
       'changed':sum(x!=y for x,y in zip(cards,result)),
       'distinct':len(set(cards[i] for i in group)),
       'unchanged':sum(x==y for x,y in zip(cards,result))}[rule['hop']]
    q=((moved if rule['carry'] else p)+rule['direction']*(h+rule['offset']))%len(a)
    return a,result,q

def rule_fits(rule,examples):
    # Reconstruct every intervening round. Printed time labels are data, not
    # adjacent-column indices. Early zero arrival cannot be passed through.
    for e in examples:
        a=list(e['counts']);cards=list(e['letters']);p=e['active']
        observed=dict(zip(e['times'],e['states']))
        if observed[0] != dict(letters=''.join(cards),counts=a,active=p):return False
        for t in range(1,e['times'][-1]+1):
            if a[p]==0:return False
            a,cards,p=predict_transition(rule,a,cards,p,e['counts'])
            if t in observed:
                s=observed[t]
                if a!=s['counts'] or ''.join(cards)!=s['letters'] or p!=s['active']:return False
        if a[p]!=0:return False
    return True
