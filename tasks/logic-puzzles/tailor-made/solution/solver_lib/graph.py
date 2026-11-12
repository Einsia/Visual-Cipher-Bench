"""Resolve card endpoints by geometric continuity, using recognized node names.
The coordinate plan contains strokes/frames only, never an A/B pair table.
"""
import json,math
from collections import Counter
from pathlib import Path

def read_cards(values):
    plan=json.loads(Path(__file__).with_name('graph.json').read_text())
    def touches(point,frame):
        x,y=point;cx,cy=frame['center'];hx,hy=frame['half_size']
        dx,dy=abs(x-cx),abs(y-cy)
        return dx<=hx+.1 and dy<=hy+.1 and min(abs(dx-hx),abs(dy-hy))<.1
    names=[values[n['field']] for n in plan['nodes']]
    if set(names)!={s+str(i) for s in 'AB' for i in range(1,6)}:raise ValueError('Graph does not name each segment once')
    cards=[];evidence=[]
    for c in plan['cards']:
        counts=Counter()
        for x,y,r,b in c['segments']:
            counts[round(x,4),round(y,4)]+=1;counts[round(r,4),round(b,4)]+=1
        if any(n>2 for n in counts.values()):raise ValueError('Branch inside a card connection')
        ends=[p for p,n in counts.items() if n==1]
        contact=[p for p in ends if touches(p,c)]
        if len(contact)!=2:raise ValueError('Card label must interrupt exactly one connection')
        node_ends=[p for p in ends if p not in contact]
        if len(node_ends)!=2:raise ValueError('Card does not have two geometric endpoints')
        endpoints=[]
        for p in node_ends:
            matched=[values[n['field']] for n in plan['nodes'] if touches(p,n)]
            if len(matched)!=1:raise ValueError('Dangling/ambiguous endpoint')
            endpoints.extend(matched)
        endpoints.sort();a,b=endpoints
        if a[0]!='A' or b[0]!='B':raise ValueError('Card must join opposite tapes')
        letter=values[c['field']]
        cards.append(dict(letter=letter,a=int(a[1])-1,b=int(b[1])-1))
        evidence.append(dict(letter=letter,physical_endpoints=[list(p) for p in node_ends],node_names=endpoints))
    return cards,evidence
