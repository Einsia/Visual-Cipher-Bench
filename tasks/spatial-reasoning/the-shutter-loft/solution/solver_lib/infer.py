"""Recover both motions using only complete opaque PNG checkpoints.

Catalog geometry, setup, and the key are recovered by the PNG Reader.
"""
import copy,itertools
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from relay import initial,turn_point
from overlap import visible,area
from layout_map import CHECK_ORIGINS,CHECK_UNIT


def move(st,i,pivot,q):
    for _ in range(q%4):
        st['polygons'][i]=[turn_point(p,pivot) for p in st['polygons'][i]]
        st['dots'][i]=turn_point(st['dots'][i],pivot)
    st['turns'][i]=(st['turns'][i]+q)%4


def run(example,selection,pivot_kind,q,primary=('departed',1,'top'),pick='max_exposed'):
    st=initial(example['cards'],example['stack']);key={(k['family'],k['turn']):k for k in example['key']}
    for i,t in enumerate(example['initial_quarters']):move(st,i,st['dots'][i][:],t)
    states=[copy.deepcopy(st)];trace=[]
    for step in range(example.get('readings',3)):
        areas=visible(st['polygons'],st['stack'])
        if pick=='max_exposed':chosen=max(st['stack'],key=areas.get)
        elif pick=='min_positive_exposed':chosen=min((i for i in st['stack'] if areas[i]>1e-8),key=areas.get)
        elif pick=='top':chosen=st['stack'][-1]
        elif pick=='whole_area':chosen=max(st['stack'],key=lambda i:area(st['polygons'][i]))
        else:raise ValueError(pick)
        c=example['cards'][chosen];entry=key[c['family'],(c['turn']+st['turns'][chosen])%4]
        departed=st['dots'][chosen][:];st['stack'].remove(chosen)
        live=sorted(st['stack'],key=lambda i:(i-chosen)%len(example['cards']));target=live[(entry['count']-1)%len(live)]
        old=st['dots'][target][:]
        pivot1={'departed':departed,'own':old,'origin':[0,0]}[primary[0]]
        move(st,target,pivot1,primary[1])
        if primary[2]=='top':st['stack'].remove(target);st['stack'].append(target)
        elif primary[2]=='bottom':st['stack'].remove(target);st['stack'].insert(0,target)
        if len(st['stack'])<2 or selection=='none':targets=[]
        elif selection=='below':targets=[st['stack'][-2]]
        elif selection=='bottom':targets=[st['stack'][0]]
        elif selection=='all_below':targets=st['stack'][:-1]
        elif selection=='top':targets=[target]
        elif selection=='all_remaining':targets=st['stack'][:]
        elif selection.startswith('fixed_'):
            i=int(selection.split('_')[1]);targets=[i] if i in st['stack'] else []
        else:
            start=target if selection.startswith('target_') else chosen
            direction=1 if selection.endswith('next') else -1
            candidates=[i for i in st['stack'] if i!=target]
            targets=[min(candidates,key=lambda i:((i-start)*direction)%len(example['cards']))] if candidates else []
        for i in targets:
            pivot={'new_target':st['dots'][target][:],'old_target':old,'departed':departed,'own':st['dots'][i][:],'origin':[0,0]}[pivot_kind]
            move(st,i,pivot,q)
        trace.append({'chosen':chosen,'target':target,'echo':targets,'letter':entry['letter'],'new_target_dot':st['dots'][target][:]})
        states.append(copy.deepcopy(st))
    return states,trace


def paint(st,cards,origin,unit,shape=(400,280)):
    im=Image.new('L',shape,255);d=ImageDraw.Draw(im)
    def xy(p):return (origin[0]+p[0]*unit,origin[1]+p[1]*unit)
    # Registration cross, the only dark non-card graphic in these scene crops.
    x,y=xy((-4,4));d.line((x-7,y,x+7,y),fill=17,width=1);d.line((x,y-7,x,y+7),fill=17,width=1)
    for i in st['stack']:
        pts=[xy(p) for p in st['polygons'][i]];d.polygon(pts,fill=255);d.line(pts+[pts[0]],fill=17,width=4,joint='curve')
        c=cards[i];off=c['stamp_offset'][:]
        for _ in range(st['turns'][i]):off=[-off[1],off[0]]
        dot=st['dots'][i];x,y=xy(dot);d.ellipse((x-4,y-4,x+4,y+4),fill=17)
        glyph=[(-.5,-.5),(-.15,-.5),(-.15,.15),(.5,.15),(.5,.5),(-.5,.5)] if c['family']=='L' else [(-.5,-.5),(-.5,.5),(.5,.5)]
        for _ in range((c['turn']+st['turns'][i])%4):glyph=[(-v,u) for u,v in glyph]
        d.polygon([xy((dot[0]+off[0]+u*.9,dot[1]+off[1]+v*.9)) for u,v in glyph],fill=17)
    return np.array(im)<100


def dilate(a,r=2):return np.asarray(Image.fromarray(a).convert('L').filter(ImageFilter.MaxFilter(2*r+1)))>0


def infer(reader,example):
    """Jointly infer both rigid motions, layer update, and exit selection.

    A finite grammar of simple quarter-turn operations is compared against the
    actual opaque PNG endpoints. No numeric rehearsal areas or motion overlays
    are read, and no main-instance constraint participates in rule selection.
    """
    from functools import lru_cache
    observed=[reader.crop(2,(x-180,638-134,x+180,638+134))<100 for x in [850,1338]]
    extra=reader.checkpoint_example(example)
    observed += [reader.original_pages[2][y-110:y+110,x-110:x+110]<100 for x,y in CHECK_ORIGINS]
    expanded=[dilate(a) for a in observed]
    def state_key(st):
        return tuple((i,tuple(map(tuple,st['polygons'][i])),tuple(st['dots'][i]),st['turns'][i]) for i in st['stack'])
    @lru_cache(maxsize=24000)
    def error(k,sk):
        st={'stack':[row[0] for row in sk],
            'polygons':{r[0]:list(r[1]) for r in sk},
            'dots':{r[0]:list(r[2]) for r in sk},'turns':{r[0]:r[3] for r in sk}}
        pred=paint(st,example['cards'],(180,134) if k<2 else (110,110),
                   24 if k<2 else CHECK_UNIT,(360,268) if k<2 else (220,220))
        return int(np.count_nonzero(pred&~expanded[k]))+int(np.count_nonzero(observed[k]&~dilate(pred)))
    selections=['below','bottom','all_below','top','none','all_remaining',
                'target_next','target_previous','departed_next','departed_previous']
    selections += ['fixed_'+str(i) for i in range(len(example['cards']))]
    echoes=list(itertools.product(selections,['new_target','old_target','departed','own','origin'],range(4)))
    primaries=list(itertools.product(['departed','own','origin'],range(4),['top','stay','bottom']))
    picks=['max_exposed','min_positive_exposed','top','whole_area']
    tested=0;departure_rejected=0;scored=[];first_pass=[]
    # First-round departure is visible in the Exit row; reject incompatible
    # selection rules before making any geometric assumptions about movements.
    init=initial(example['cards'],example['stack'])
    for i,q in enumerate(example['initial_quarters']):move(init,i,init['dots'][i][:],q)
    areas=visible(init['polygons'],init['stack'])
    first_choices={'max_exposed':max(init['stack'],key=areas.get),
                   'min_positive_exposed':min((i for i in init['stack'] if areas[i]>1e-8),key=areas.get),
                   'top':init['stack'][-1],
                   'whole_area':max(init['stack'],key=lambda i:area(init['polygons'][i]))}
    for pick,primary,echo in itertools.product(picks,primaries,echoes):
        tested+=1
        if first_choices[pick]!=example['exit_order'][0]:
            departure_rejected+=1;continue
        states,trace=run(example,*echo,primary=primary,pick=pick)
        if [t['chosen'] for t in trace]!=example['exit_order'][:-1]:
            departure_rejected+=1;continue
        scores=[error(k-1,state_key(states[k])) for k in [1,2]]
        rec={'selection_rule':pick,'primary_rule':list(primary),'rule':list(echo),
             'checkpoint_errors':scores,'pixel_error':sum(scores),
             'departures':[t['chosen'] for t in trace]}
        # A 450-pixel interior discrepancy is already beyond acceptance even
        # if the independent example were perfect; this is safe pruning.
        if sum(scores)>450:continue
        first_pass.append(dict(rec))
        es,et=run(extra,*echo,primary=primary,pick=pick)
        ex=[error(k+2,state_key(st)) for k,st in enumerate(es)]
        rec.update(added_checkpoint_errors=ex,pixel_error=sum(scores+ex),
                   added_second_motion_cards=[i+1 for i in et[0]['echo']])
        scored.append(rec)
    scored.sort(key=lambda r:r['pixel_error'])
    assert scored and scored[0]['pixel_error']<250,('No matching spatial rule',scored[:4])
    best=scored[0]
    winners=[h for h in scored if h['pixel_error']<=best['pixel_error']+200]
    assert len(winners)==1,('Ambiguous rehearsal rule',winners)
    return {'inferred_rule':best['rule'],'inferred_primary_rule':best['primary_rule'],
            'inferred_selection_rule':best['selection_rule'],
            'candidate_rules':[h['rule'] for h in winners],
            'candidate_joint_rules':winners,'tested_hypotheses':tested,
            'departure_rejections':departure_rejected,
            'first_rehearsal_candidates':first_pass,
            'evidence':'Opaque registered checkpoints and existing independent one-round example; both motions inferred jointly before main search',
            'unique_before_main_search':True,
            'added_example_input':{'stack':[i+1 for i in extra['stack']],'initial_quarters':extra['initial_quarters']},
            'uses_area_values_or_post_initial_layer_labels':False,
            'uses_first_motion_overlays':False,'uses_main_data':False,
            'rule_grammar':{'exit_choices':picks,'primary_pivots':['departed','own','origin'],
                            'primary_quarter_turns':[0,1,2,3],'layer_updates':['top','stay','bottom'],
                            'secondary_selections':selections,
                            'secondary_pivots':['new_target','old_target','departed','own','origin'],
                            'secondary_quarter_turns':[0,1,2,3]},
            'ranked_hypotheses':scored,'cached_spatial_comparisons':error.cache_info().currsize}


def resolve(reader,example,main=None,npoints=1000):
    """Require a unique rehearsal interpretation before searching the main PNG."""
    from search import search
    result=infer(reader,example)
    if main is None:main=reader.main(example['key'])
    inp=reader.footprint_input(main,npoints)
    assert result['inferred_primary_rule']==['departed',1,'top'], 'Primary rule unsupported by main engine'
    assert result['inferred_selection_rule']=='max_exposed', 'Exit rule unsupported by main engine'
    rule=result['inferred_rule']
    found=search(main,mode=1,workers=16,npoints=npoints,input_text=inp,rule=rule)
    assert found['lines'],('No main solution for rehearsal-inferred rule',rule)
    return result,found
