"""Compare natural rule alternatives against PNG-transcribed calibration states.

Only the example states shown in the images enter this inference.
The finite family is explicit; this is not a claim about arbitrary invented rules.
"""
from itertools import product


def infer_rules(original, after1, before6, after6, final, labels, endpoints):
    n=len(original['masks'])
    inside=[[bool(original['masks'][r]>>c&1) for c in range(n)] for r in range(n)]
    observed={1:after1,5:before6,6:after6,8:final}
    order=sorted(range(2*n),key=lambda j:labels[j])
    # Every integer affine map on 0..4 preserving that range: constants,
    # identity and complement. Independent maps for same/different membership.
    maps=[(a,b) for a in range(-4,5) for b in range(-16,21)
          if all(0<=a*v+b<=4 for v in range(5))]
    winners=[];tested=0;endpoint_compatible=0
    for sample,clock,rd,cd,moving,same,different in product(
            ['inside','outside','all'],['current','initial'],[1,-1],[1,-1],
            ['whole','sampled'],maps,maps):
        tested+=1
        if any((same if bg1==bg2 else different)[0]*src[0]+
               (same if bg1==bg2 else different)[1]!=dst[0]
               for src,dst,bg1,bg2 in endpoints):continue
        endpoint_compatible+=1
        values=[row[:] for row in original['values']]
        letters=[row[:] for row in original['letters']]
        ok=True;steps=[]
        for step,op in enumerate(order,1):
            coords=[(op//2,c) for c in range(n)] if op%2==0 else [(r,op//2) for r in range(n)]
            selected=[(r,c) for r,c in coords if sample=='all' or inside[r][c]==(sample=='inside')]
            basis=values if clock=='current' else original['values']
            total=sum(basis[r][c] for r,c in selected)
            if (step==1 and selected!=[tuple(c) for c in original['frames']]) or (step==6 and selected!=[tuple(c) for c in before6['frames']]):
                ok=False;break
            cells=coords if moving=='whole' else selected
            if cells:
                shift=(rd if op%2==0 else cd)*total%len(cells)
                old=[(values[r][c],letters[r][c],inside[r][c]) for r,c in cells]
                for j,(r,c) in enumerate(cells):
                    v,ch,bg=old[(j-shift)%len(cells)]
                    a,b=same if bg==inside[r][c] else different
                    values[r][c]=a*v+b;letters[r][c]=ch
            steps.append(total)
            if step in observed:
                g=observed[step]
                if values!=g['values'] or letters!=g['letters']:
                    ok=False;break
        if ok:winners.append({'sample':sample,'clock':clock,'row_direction':rd,'column_direction':cd,'moving':moving,'same':list(same),'different':list(different),'sums':steps})
    if len(winners)!=1:raise ValueError(f'calibration rule ambiguity: {winners}')
    rule=winners[0]
    if (rule['sample'],rule['clock'],rule['row_direction'],rule['column_direction'],rule['moving'],rule['same'],rule['different'])!=('inside','current',1,1,'whole',[1,0],[-1,4]):
        raise ValueError(f'calibration does not establish implemented rules: {rule}')
    return {'candidate_count':tested,'endpoint_compatible':endpoint_compatible,
            'survivor_count':len(winners),'rule':rule,
            'membership_source':'PNG thick edges, exterior flood fill',
            'scope':'sample region × current/initial × row/column signs × whole/sampled movement × two integer affine maps on 0..4'}
