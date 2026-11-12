"""Infer unprinted transfer addresses and extraction indices from completed visible states.

The finite grammar deliberately includes plausible wrong readings. No specimen
names, numeric trace, fixed extraction indices, or answer is embedded here.
"""
from itertools import product


def value(state,word,kind):
    j=state['words'].index(word)
    return state['badges'][j] if kind=='ring' else j+1


def infer_transfers(states,pairs):
    n=len(pairs)
    def execute(rule,k,pair):
        phase,kind,lookup,offset,cross,ringtarget,carry=rule
        st=states[{'initial':0,'before':k,'after':k+1,'final':n}[phase]]
        uv=[value(st,w,kind) for w in pair]
        selected=uv[::-1] if cross else uv
        if lookup.startswith('selected_'):
            xy=[value(states[t+offset],w,lookup.split('_')[1]) for t,w in zip(selected,pair)]
        elif lookup=='direct':xy=selected
        else:xy=[value(states[{'current_slot':k,'initial_slot':0,'final_slot':n}[lookup]],w,'slot') for w in pair]
        ws=states[k]['words'].copy();bs=states[k]['badges'].copy()
        x,y=[i-1 for i in xy];ws[x],ws[y]=ws[y],ws[x]
        if carry:bs[x],bs[y]=bs[y],bs[x]
        middle=dict(words=ws.copy(),badges=bs.copy())
        if ringtarget=='selectors':ab=uv
        elif ringtarget=='addresses':ab=xy
        elif ringtarget=='named_before':ab=[states[k]['words'].index(w)+1 for w in pair]
        else:ab=[ws.index(w)+1 for w in pair]
        a,b=[i-1 for i in ab];bs[a],bs[b]=bs[b],bs[a]
        return dict(step=k+1,pair=pair,read_times=uv,card_slots=xy,badge_slots=ab,
                    middle=middle,after=dict(words=ws,badges=bs))
    survivors=[];tested=0;reject_counts=[0]*n
    for phase,kind,lookup,offset,cross,target,carry in product(
            ['initial','before','after','final'],['ring','slot'],
            ['selected_slot','selected_ring','direct','current_slot','initial_slot','final_slot'],
            [0,-1],[False,True],['selectors','addresses','named_before','named_after'],[True,False]):
        if lookup not in ['selected_slot','selected_ring'] and offset:continue
        rule=(phase,kind,lookup,offset,cross,target,carry);tested+=1
        traces=[]
        for k,pair in enumerate(pairs):
            trace=execute(rule,k,pair)
            if trace['after']!=states[k+1]:reject_counts[k]+=1;break
            traces.append(trace)
        else:survivors.append((rule,traces))
    if len(survivors)!=1:raise ValueError(f'Calibration transfer rule ambiguous: {len(survivors)} survivors')
    rule,traces=survivors[0]
    # The generic puzzle engine implements this uniquely inferred mechanism.
    expected=('before','ring','selected_slot',0,False,'selectors',True)
    if rule!=expected:raise ValueError('Visible calibration specifies an unsupported transfer rule')
    return dict(candidate_count=tested,survivor_count=1,
                selected=dict(zip(['source_phase','source_kind','lookup','snapshot_offset','cross_selectors','ring_targets','carry_rings'],rule)),
                rejected_by_first_failing_step=reject_counts,traces=traces)


def infer_extraction(states,words,letters):
    survivors=[]
    for t,kind,reverse in product(range(len(states)),['ring','slot'],[False,True]):
        indices=[value(states[t],w,kind) for w in words]
        if reverse:indices=[len(w)+1-i for w,i in zip(words,indices)]
        if [w[i-1] for w,i in zip(words,indices)]==letters:
            survivors.append(dict(snapshot=t,kind=kind,from_right=reverse,indices=indices))
    if len(survivors)!=1:raise ValueError(f'Calibration extraction ambiguous: {survivors}')
    rule=survivors[0]
    if (rule['snapshot'],rule['kind'],rule['from_right'])!=(0,'ring',False):
        raise ValueError('Visible calibration specifies an unsupported extraction')
    return dict(candidate_count=len(states)*4,survivor_count=1,selected=rule,
                indices=rule['indices'],letters=letters)
