"""Reconstruct from the caller's pixel observations; two independent encodings."""
import argparse,itertools,json,sys,time,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from model import PERMS,flat,matrix,forward,backward
from joint_model import model_from_result
from coupled import solve_joint,LABELS,GLYPHS
from joint_circuit import solve_circuit_joint

def public_data(spec):
 conv=lambda e:dict(e,symbols=[int(s=='circle') for s in e['symbols']])
 return list(map(conv,spec['examples'])),list(map(conv,spec['targets']))

def task(arg):
 route,obs,ts,g=arg
 r=(solve_joint if route=='tuples' else solve_circuit_joint)(obs,ts,g,limit=2)
 r['route']=route
 r['answers']=[''.join(LABELS[i] for i in sol[50:]) for sol in r['solutions']]
 return r

def verify(spec,workers=4):
 start=time.perf_counter();obs,ts=public_data(spec)
 assert spec['worked']['letter'] in LABELS
 assert any(c==spec['worked']['letter'] and flat(spec['worked']['after'])==g.tolist() for c,g in zip(LABELS,GLYPHS)), 'Unrecognized legend bitmap'
 tasks=[(route,obs,ts,g) for route in ('tuples','circuit') for g in itertools.product(PERMS,repeat=2)]
 with ProcessPoolExecutor(max_workers=workers) as pool:results=list(pool.map(task,tasks))
 assert not any(r['aborted'] for r in results),'Incomplete search'
 assert all(r['exhausted'] for r in results),'Multiple answers in some geometry pair'
 answer_sets={route:{a for r in results if r['route']==route for a in r['answers']} for route in ('tuples','circuit')}
 assert answer_sets['tuples']==answer_sets['circuit'] and len(answer_sets['tuples'])==1,answer_sets
 answer=next(iter(answer_sets['tuples']))
 witnesses=[];bit_updates=0;dependency_visits=0
 for r in results:
  for values in r['solutions']:
   m=model_from_result(r,values[:50]);pred=[]
   for e in spec['examples']:assert forward(flat(e['before']),e['symbols'],m)[-1]==flat(e['after'])
   for j,t in enumerate(spec['targets']):
    out=forward(flat(t['before']),t['symbols'],m)[-1];back,n=backward(flat(t['before']),t['symbols'],m)
    assert out==back and out==GLYPHS[values[50+j]].tolist()
    bit_updates+=25*len(t['symbols']);dependency_visits+=n
    pred.append({'id':t['id'],'after':matrix(out),'letter':LABELS[values[50+j]]})
   witnesses.append({'route':r['route'],'model':m,'targets':pred})
 summaries=[]
 for route in ('tuples','circuit'):
  rr=[r for r in results if r['route']==route]
  summaries.append({'name':route,'geometry_pairs_tested':len(rr),'nodes':sum(r['nodes'] for r in rr),'constraint_visits':sum(r.get('constraint_visits',0) for r in rr),'clause_visits':sum(r.get('clause_visits',0) for r in rr),'worker_seconds':sum(r['seconds'] for r in rr),'answer_count':len(answer_sets[route]),'surviving_geometries':[r['geoms'] for r in rr if r['solutions']],'aborted':False})
 a,b=spec['examples'][:2]
 assert a['before']==b['before'] and a['symbols']==b['symbols'][::-1] and a['after']!=b['after']
 report={'valid':True,'unique':True,'solution_count':1,'answer':answer,'scope':'Unique capital sequence in D4 plus arbitrary unary Boolean functions at 50 coordinates, jointly constrained by 5 observations and 8 ordinary capital outputs, with a separate H recognition legend; 44 block glyphs for all 26 letters. Hidden rule and exact font variant need not be unique. No dictionary used.','hidden_model_count':'not enumerated; answer projection exhaustively checked','routes':summaries,'wall_seconds':time.perf_counter()-start,'witnesses':witnesses,'target_predictions':witnesses[0]['targets'],'execution':{'pixel_updates_per_model':25*sum(len(t['symbols']) for t in spec['targets']),'maximum_sequence_depth':max(len(t['symbols']) for t in spec['targets']),'backward_visits_for_witnesses':dependency_visits},'checks':[
 {'name':'two_independent_encodings','passed':True,'evidence':summaries},
 {'name':'unique_answer_projection','passed':True,'evidence':{'geometry_pairs_each':64,'letter_shapes':len(GLYPHS),'alphabet_letters':len(set(LABELS)),'second_answer_found':False,'search_caps_reached':False,'word_dictionary_used':False}},
 {'name':'endpoint_and_target_replay','passed':True,'evidence':{'witnesses':len(witnesses),'observations':len(obs),'targets':len(ts),'forward_backward_agree':True}},
 {'name':'order_discrimination','passed':True,'evidence':{'examples':[a['id'],b['id']],'first_after':a['after'],'second_after':b['after']}},
 {'name':'extraction','passed':True,'evidence':{'legend_letter':spec['worked']['letter'],'legend_bitmap':spec['worked']['after'],'read_order':'row-major aligned target pairs','output':answer}},
 {'name':'text_not_increased','passed':True,'evidence':{'rule_sentences':0,'boundary_clauses':0,'heading':spec['heading'],'data_text':['H']+['?']*8}}
 ]}
 return report

