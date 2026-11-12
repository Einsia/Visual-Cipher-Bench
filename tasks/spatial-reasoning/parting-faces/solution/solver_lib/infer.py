"""Recover the second-motion rule from the registered scenes on page 2."""
import copy,itertools
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from relay import initial,turn_point
from overlap import visible,area


def move(st,i,pivot,q):
    for _ in range(q%4):
        st['polygons'][i]=[turn_point(p,pivot) for p in st['polygons'][i]]
        st['dots'][i]=turn_point(st['dots'][i],pivot)
    st['turns'][i]=(st['turns'][i]+q)%4


def run(example,selection,pivot_kind,q,first_pivot='departed',first_q=1,raise_target=True,selection_metric='exposed'):
    st=initial(example['cards'],example['stack']);key={(k['family'],k['turn']):k for k in example['key']}
    for i,t in enumerate(example['initial_quarters']):move(st,i,st['dots'][i][:],t)
    states=[copy.deepcopy(st)];trace=[];middles=[]
    for step in range(3):
        if selection_metric=='exposed':scores=visible(st['polygons'],st['stack'])
        elif selection_metric=='whole':scores={i:area(st['polygons'][i]) for i in st['stack']}
        elif selection_metric=='top':scores={i:j for j,i in enumerate(st['stack'])}
        elif selection_metric=='bottom':scores={i:-j for j,i in enumerate(st['stack'])}
        else:scores={i:-v for i,v in visible(st['polygons'],st['stack']).items()}
        chosen=max(st['stack'],key=scores.get)
        if chosen!=example['exit_order'][step]:return None
        c=example['cards'][chosen];entry=key[c['family'],(c['turn']+st['turns'][chosen])%4]
        departed=st['dots'][chosen][:];st['stack'].remove(chosen)
        live=sorted(st['stack'],key=lambda i:(i-chosen)%len(example['cards']));target=live[(entry['count']-1)%len(live)]
        old=st['dots'][target][:]
        pivot={'departed':departed,'own':old,'origin':[0,0]}[first_pivot]
        move(st,target,pivot,first_q)
        if raise_target:st['stack'].remove(target);st['stack'].append(target)
        middles.append(copy.deepcopy(st))
        if len(st['stack'])<2 or selection=='none':targets=[]
        elif selection=='below':targets=[st['stack'][-2]]
        elif selection=='bottom':targets=[st['stack'][0]]
        elif selection=='all_below':targets=st['stack'][:-1]
        else:targets=[target]
        for i in targets:
            pivot={'new_target':st['dots'][target][:],'old_target':old,'departed':departed,'own':st['dots'][i][:],'origin':[0,0]}[pivot_kind]
            move(st,i,pivot,q)
        trace.append({'chosen':chosen,'target':target,'echo':targets,'letter':entry['letter'],'new_target_dot':st['dots'][target][:]})
        states.append(copy.deepcopy(st))
    return states,trace,middles


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
    # Every operation field is a hypothesis tested against the page.
    # Coordinates below locate the registered scene panels.
    panels=[(850,638,24,1),(1338,638,24,2),(500,1640,30,'middle'),
            (960,1640,30,1),(1370,1640,30,3)]
    observations=[reader.crop(2,(x-180,y-150,x+180,y+150))<100 for x,y,unit,k in panels]
    dilated=[dilate(a) for a in observations]
    titles=[reader.text(2,(x-120,784,x+120,820),['Exposed area','Whole area'],False,'label') for x in [362,850,1338]]
    assert len(set(titles))==1
    scored=[];tested=0;exit_rejections=0;label_rejections=0;score_cache={}
    families=itertools.product(['exposed','whole','top','bottom','smallest_exposed'],
         ['departed','own','origin'],range(4),[False,True],
         ['below','bottom','all_below','top','none'],
         ['new_target','old_target','departed','own','origin'],[1,2,3])
    for metric,fp,fq,raise_target,selection,pivot,q in families:
        tested+=1
        if (titles[0]=='Exposed area' and metric=='whole') or (titles[0]=='Whole area' and metric=='exposed'):
            label_rejections+=1;continue
        result=run(example,selection,pivot,q,fp,fq,raise_target,metric)
        if result is None:exit_rejections+=1;continue
        states,trace,middles=result;scores=[]
        for panel_index,((x,y,unit,k),obs,wide) in enumerate(zip(panels,observations,dilated)):
            state=middles[0] if k=='middle' else states[k]
            sig=(panel_index,tuple((i,tuple(map(tuple,state['polygons'][i])),tuple(state['dots'][i]),state['turns'][i]) for i in state['stack']))
            if sig not in score_cache:
                pred=paint(state,example['cards'],(180,150),unit,(360,300))
                score_cache[sig]=int(np.count_nonzero(pred&~wide))+int(np.count_nonzero(obs&~dilate(pred)))
            scores.append(score_cache[sig])
            if sum(scores)>550:break # rigorous lower bound, never discards a fit
        scored.append({'rule':[selection,pivot,q],
            'first_motion':[fp,fq,raise_target],'selection_metric':metric,
            'pixel_error':sum(scores),'checkpoint_errors':scores,
            'error_is_lower_bound':len(scores)<len(panels),'departures':[t['chosen'] for t in trace]})
    scored.sort(key=lambda r:r['pixel_error']);best=scored[0]
    assert best['pixel_error']<350,scored[:4]
    assert scored[1]['pixel_error']>best['pixel_error']+200,scored[:4]
    assert best['departures']==example['exit_order'][:-1]
    return {'inferred_rule':best['rule'],'first_motion':best['first_motion'],
        'selection_metric':best['selection_metric'],'tested_hypotheses':tested,
        'exit_rejections':exit_rejections,'label_rejections':label_rejections,'area_labels':titles,'ranked_hypotheses':scored[:30],
        'surviving_pixel_hypotheses':sum(r['pixel_error']<350 for r in scored),
        'evidence_panels':panels}
