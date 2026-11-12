"""Convex clipping and independent raster geometry."""
import math
import numpy as np

def rotate(poly,turn):
    p=[tuple(v) for v in poly]
    for _ in range(turn%4):p=[(-y,x) for x,y in p]
    return p

def area(p):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))/2 if len(p)>2 else 0.

def clip(subject,cutter):
    p=subject
    for a,b in zip(cutter,cutter[1:]+cutter[:1]):
        old=p;p=[]
        if not old:break
        def side(v):return (b[0]-a[0])*(v[1]-a[1])-(b[1]-a[1])*(v[0]-a[0])
        prev=old[-1];sp=side(prev)
        for curr in old:
            sc=side(curr)
            if (sc>=-1e-12)!=(sp>=-1e-12):
                t=sp/(sp-sc);p.append((prev[0]+t*(curr[0]-prev[0]),prev[1]+t*(curr[1]-prev[1])))
            if sc>=-1e-12:p.append(curr)
            prev=curr;sp=sc
    return p

def visible(polys,stack,work=None):
    out={}
    for j,i in enumerate(stack):
        total=area(polys[i]);above=stack[j+1:]
        def subtract(p,k,sign):
            nonlocal total
            for b in range(k,len(above)):
                q=clip(p,polys[above[b]])
                if work is not None:work['polygon_intersections']+=1
                ar=area(q)
                if ar>1e-11:
                    total+=sign*ar;subtract(q,b+1,-sign)
        subtract(polys[i],0,-1);out[i]=max(0,total)
    return out

def raster_masks(cards,n=800):
    limit=max(abs(z) for c in cards for p in c['polygon'] for z in p)+.1
    a=(np.arange(n)+.5)*2*limit/n-limit;x,y=np.meshgrid(a,a)
    result=[]
    for c in cards:
        turns=[]
        for t in range(4):
            p=rotate(c['polygon'],t);m=np.ones(x.shape,dtype=bool)
            for (u,v),(w,z) in zip(p,p[1:]+p[:1]):m&=(w-u)*(y-v)-(z-v)*(x-u)>=0
            turns.append(m)
        result.append(turns)
    return result,(2*limit/n)**2

def run(spec,instance,route='polygon',variant=None,resolution=800):
    cards=instance['cards'];n=len(cards);turns=instance.get('initial_turns',[0]*n)[:];stack=instance['stack'][:]
    if variant=='reverse_stack':stack.reverse()
    key={(e['family'],e['turn']):e for e in spec['key']}
    work={'states':0,'polygon_intersections':0,'pixel_layers':0,'effective_trajectories':1,'branches':0}
    masks=None
    if route=='raster':masks,unit=raster_masks(cards,resolution)
    trace=[]
    for step in range(instance['readings']):
        polys=[rotate(c['polygon'],turns[i]) for i,c in enumerate(cards)]
        if route=='raster':
            cover=np.zeros_like(masks[0][0]);areas={}
            for i in stack[::-1]:
                m=masks[i][turns[i]];areas[i]=int(np.count_nonzero(m&~cover))*unit;cover|=m;work['pixel_layers']+=1
        else:areas=visible(polys,stack,work)
        order=sorted(stack,key=lambda i:areas[i],reverse=True)
        selected=order[0]
        if variant=='top_only':selected=stack[-1]
        if variant=='whole_area':selected=max(stack,key=lambda i:area(polys[i]))
        if variant=='smallest_visible':selected=min((i for i in stack if areas[i]>1e-8),key=areas.get)
        c=cards[selected];reading=key[(c['family'],(c['turn']+turns[selected])%4)]
        record={'step':step+1,'selected':selected+1,'stack_bottom_to_top':[i+1 for i in stack],'turns':turns[:],
                'visible_areas':{str(i+1):float(a) for i,a in areas.items()},'letter':reading['letter'],'count':reading['count'],
                'margin':float(areas[order[0]]-areas[order[1]]) if len(order)>1 else float(areas[order[0]]),
                'relative_margin':float((areas[order[0]]-areas[order[1]])/areas[order[0]]) if len(order)>1 else 1}
        stack.remove(selected)
        if stack:
            live=sorted(stack,key=lambda i:((selected-i) if variant=='counterclockwise_count' else (i-selected))%n)
            target=live[(reading['count']-1)%len(live)];record['target']=target+1
            if variant!='no_turn':turns[target]=(turns[target]+(-1 if variant=='counterclockwise_turn' else 1))%4
            if variant!='no_raise':stack.remove(target);stack.append(target)
        trace.append(record);work['states']+=1
    return {'answer':''.join(t['letter'] for t in trace),'trace':trace,'work':work}
