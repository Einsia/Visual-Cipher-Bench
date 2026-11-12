"""Affine opaque-card relay. Printed geometry and key are the only inputs."""
import copy,time
import numpy as np
from overlap import visible,area
from regions import delta,difference

def turn_point(q,c):return [c[0]-(q[1]-c[1]),c[1]+(q[0]-c[0])]
def initial(cards,stack):return {'polygons':[copy.deepcopy(c['polygon']) for c in cards],'dots':[c['dot'][:] for c in cards],'turns':[0]*len(cards),'stack':stack[:]}
def advance(st,chosen,count,variant=None):
 st=copy.deepcopy(st);n=len(st['dots']);pivot=st['dots'][chosen][:];st['stack'].remove(chosen)
 if not st['stack']:return st,None,[]
 live=sorted(st['stack'],key=lambda i:((chosen-i) if variant=='reverse_count' else (i-chosen))%n)
 visits=[live[j%len(live)] for j in range(count)];target=visits[-1]
 if variant=='own_pivot':pivot=st['dots'][target][:]
 if variant=='fixed_pivot':pivot=[0,0]
 old_dot=st['dots'][target][:]
 if variant!='no_turn':
  turns=3 if variant=='reverse_turn' else 1
  for _ in range(turns):
   st['polygons'][target]=[turn_point(p,pivot) for p in st['polygons'][target]];st['dots'][target]=turn_point(st['dots'][target],pivot)
  st['turns'][target]=(st['turns'][target]+turns)%4
 if variant!='no_raise':st['stack'].remove(target);st['stack'].append(target)
 if len(st['stack'])>=2 and variant!='no_echo':
  echo=st['stack'][-2];ep=old_dot if variant=='old_echo_pivot' else st['dots'][target][:]
  et=1 if variant=='clockwise_echo' else 3
  for _ in range(et):
   st['polygons'][echo]=[turn_point(p,ep) for p in st['polygons'][echo]];st['dots'][echo]=turn_point(st['dots'][echo],ep)
  st['turns'][echo]=(st['turns'][echo]+et)%4
 return st,target,visits

def raster_visible(st,resolution=900):
 q=[v for i in st['stack'] for v in st['polygons'][i]];bounds=[min(v[0] for v in q)-.1,max(v[0] for v in q)+.1,min(v[1] for v in q)-.1,max(v[1] for v in q)+.1]
 x=np.linspace(bounds[0],bounds[1],resolution,endpoint=False)+(bounds[1]-bounds[0])/resolution/2;y=np.linspace(bounds[2],bounds[3],resolution,endpoint=False)+(bounds[3]-bounds[2])/resolution/2
 x,y=np.meshgrid(x,y);cover=np.zeros(x.shape,bool);out={};unit=(bounds[1]-bounds[0])*(bounds[3]-bounds[2])/resolution**2
 for i in st['stack'][::-1]:
  poly=st['polygons'][i];mask=np.ones(x.shape,bool)
  for a,b in zip(poly,poly[1:]+poly[:1]):mask&=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>=0
  out[i]=int(np.count_nonzero(mask&~cover))*unit;cover|=mask
 return out

def simulate(spec,stack,route='polygon',variant=None,resolution=900,initial_quarters=None):
 cards=spec['cards'];key={(e['family'],e['turn']):e for e in spec['key']};st=initial(cards,stack)
 if initial_quarters is None:initial_quarters=spec.get('initial_quarters',[0]*len(cards))
 for i,q in enumerate(initial_quarters):
  for _ in range(q):st['polygons'][i]=[turn_point(p,st['dots'][i]) for p in st['polygons'][i]]
  st['turns'][i]=q
 states=[copy.deepcopy(st)];trace=[]
 for k in range(spec['readings']):
  v=visible(st['polygons'],st['stack']) if route=='polygon' else raster_visible(st,resolution)
  rank=sorted(st['stack'],key=v.get,reverse=True);chosen=rank[0]
  if variant=='top_only':chosen=st['stack'][-1]
  if variant=='whole_area':chosen=max(st['stack'],key=lambda i:area(st['polygons'][i]))
  card=cards[chosen];rot=(card['turn']+st['turns'][chosen])%4
  if variant=='ignore_orientation':rot=card['turn']
  e=key[card['family'],rot];nxt,target,visits=advance(st,chosen,e['count'],variant)
  trace.append({'step':k+1,'selected':chosen+1,'letter':e['letter'],'count':e['count'],'target':target+1 if target is not None else None,'visits':[i+1 for i in visits],'areas':{str(i+1):v[i] for i in st['stack']},'margin':v[rank[0]]-v[rank[1]] if len(rank)>1 else v[rank[0]],'relative_margin':(v[rank[0]]-v[rank[1]])/v[rank[0]] if len(rank)>1 else 1,'stack':[i+1 for i in st['stack']],'turns':st['turns'][:],'pivot':st['dots'][chosen][:],'echo':nxt['stack'][-2]+1 if len(nxt['stack'])>=2 and variant!='no_echo' else None,'echo_pivot':nxt['dots'][target][:] if len(nxt['stack'])>=2 else None})
  st=nxt;states.append(copy.deepcopy(st))
 return {'answer':''.join(t['letter'] for t in trace),'trace':trace,'states':states}

def footprint(st):return [st['polygons'][i] for i in st['stack']]
def changes_for(run,pairs):return [{'from':a,'to':b,'pieces':delta(footprint(run['states'][a]),footprint(run['states'][b]))} for a,b in pairs]
def change_errors(run,obs):
 return [sum(area(p) for p in difference(delta(footprint(run['states'][o['from']]),footprint(run['states'][o['to']])),o['pieces']))+sum(area(p) for p in difference(o['pieces'],delta(footprint(run['states'][o['from']]),footprint(run['states'][o['to']])))) for o in obs]
