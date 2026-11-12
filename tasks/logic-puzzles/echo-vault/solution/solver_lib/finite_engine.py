"""Integer finite-domain model, rebuilt solely from public conditions.

Only the native CP-SAT helper is vendored; no installation, pandas, protobuf
Python package, external data, network or system solver is required.
"""
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
from ortools.sat.python import cp_model_helper as h
from .packing import terminal_rows

class Model:
 def __init__(self,n):self.n=n;self.variables=[];self.constraints=[]
 def var(self,name,hi=None):
  i=len(self.variables);self.variables.append(f'variables {{name: "{name}" domain: 0 domain: {self.n-1 if hi is None else hi}}}');return i
 def constraint(self,body,lit=()):self.constraints.append('constraints {'+' '.join(f'enforcement_literal: {i}' for i in lit)+' '+body+'}')
 @staticmethod
 def expr(v):return f'vars: {v} coeffs: 1'
 def linear(self,vs,cs,domain,lit=()):
  self.constraint('linear {'+' '.join(f'vars: {v}' for v in vs)+' '+' '.join(f'coeffs: {c}' for c in cs)+' '+' '.join(f'domain: {v}' for v in domain)+'}',lit)
 def eq(self,a,b,name):
  e=self.var(name,1);self.linear([a,b],[1,-1],[0,0],[e]);self.linear([a,b],[1,-1],[-self.n,-1,1,self.n],[-e-1]);return e
 def assign(self,a,b,lit=()):self.linear([a,b],[1,-1],[0,0],lit)
 def elem(self,ix,vs,name):
  o=self.var(name);self.constraint('element {linear_index {'+self.expr(ix)+'} linear_target {'+self.expr(o)+'} '+ ' '.join('exprs {'+self.expr(v)+'}' for v in vs)+'}');return o
 def all_diff(self,vs):self.constraint('all_diff {'+' '.join('exprs {'+self.expr(v)+'}' for v in vs)+'}')
 def inverse(self,a,b):self.constraint('inverse {'+' '.join(f'f_direct: {v}' for v in a)+' '+' '.join(f'f_inverse: {v}' for v in b)+'}')
 def table(self,vs,rows,negated=False):
  if not rows:
   if not negated:self.constraint('bool_or {}')
   return
  self.constraint('table {'+('negated: true ' if negated else '')+' '.join('exprs {'+self.expr(v)+'}' for v in vs)+' '+' '.join(f'values: {x}' for row in rows for x in row)+'}')
 def proto(self):
  p=h.CpModelProto();p.parse_text_format('\n'.join(self.variables+self.constraints));return p

def build(n,program,clues,packing=True):
 m=Model(n)
 def row(name):return [m.var(name+str(w)) for w in range(n)]
 P=[row(f'p{t}_') for t in range(n+1)];B=[row(f'b{t}_') for t in range(n+1)];C=[row(f'c{t}_') for t in range(n+1)]
 for t in range(n+1):m.inverse(P[t],C[t]);m.all_diff(B[t])
 for t,(a,b) in enumerate(program,1):
  old=P[t-1];bb=B[t-1];cur=P[t]
  x=m.elem(bb[a],[P[k][a] for k in range(1,n+1)],f'x{t}');y=m.elem(bb[b],[P[k][b] for k in range(1,n+1)],f'y{t}')
  for w in range(n):
   ex=m.eq(old[w],x,f'ex{t}_{w}');ey=m.eq(old[w],y,f'ey{t}_{w}')
   m.assign(cur[w],y,[ex]);m.assign(cur[w],x,[-ex-1,ey]);m.assign(cur[w],old[w],[-ex-1,-ey-1])
  u,v=bb[a],bb[b];ca=m.elem(u,C[t],f'ca{t}');cb=m.elem(v,C[t],f'cb{t}');bu=m.elem(ca,bb,f'bu{t}');bv=m.elem(cb,bb,f'bv{t}')
  for w in range(n):
   eu=m.eq(cur[w],u,f'eu{t}_{w}');ev=m.eq(cur[w],v,f'ev{t}_{w}')
   m.assign(B[t][w],bv,[eu]);m.assign(B[t][w],bu,[-eu-1,ev]);m.assign(B[t][w],bb[w],[-eu-1,-ev-1])
 for i,(a,b,tw,dw,sg) in enumerate(clues):
  pa=m.elem(B[n][tw],[P[k][a] for k in range(1,n+1)],f'cl{2*i}');pb=m.elem(B[n][tw],[P[k][b] for k in range(1,n+1)],f'cl{2*i+1}')
  m.linear([pa,pb,B[n][dw]],[1,-1,-sg],[sg,sg])
 start=time.perf_counter();rows=terminal_rows(n,clues) if packing else None
 if rows is not None:m.table(B[-1],rows)
 meta={'raw_terminal_badge_permutations':__import__('math').factorial(n),'terminal_badge_survivors':len(rows) if rows is not None else None,'packing_seconds':time.perf_counter()-start,'integer_and_boolean_variables':len(m.variables),'constraints':len(m.constraints)}
 return m,P,B,meta

def solve(m,P,B,seconds=600,workers=4,seed=2):
 proto=m.proto();validation=h.CpSatHelper.validate_model(proto)
 if validation:raise ValueError(validation)
 s=h.SolveWrapper();pars=h.SatParameters();pars.max_time_in_seconds=seconds;pars.num_search_workers=workers;pars.random_seed=seed;s.set_parameters(pars)
 start=time.perf_counter();r=s.solve(proto);out={'result':str(r.status).split('.')[-1],'seconds':time.perf_counter()-start,'branches':r.num_branches,'conflicts':r.num_conflicts,'binary_propagations':r.num_binary_propagations,'integer_propagations':r.num_integer_propagations,'deterministic_time':r.deterministic_time,'workers':workers,'statistics':h.CpSatHelper.solver_response_stats(r)}
 if r.status in [h.CpSolverStatus.OPTIMAL,h.CpSolverStatus.FEASIBLE]:out.update(P=[[r.solution[i] for i in row] for row in P],B=[[r.solution[i] for i in row] for row in B])
 return out

def exclude(m,P,B,sol):m.table([v for ar in [P,B] for row in ar for v in row],[[v for key in ['P','B'] for row in sol[key] for v in row]],True)

def check_history(names,program,clues,history):
 n=len(names);P,B=history['P'],history['B'];trace=[]
 assert len(P)==len(B)==n+1
 assert all(sorted(row)==list(range(n)) for row in P+B)
 for t,(a,b) in enumerate(program,1):
  order=sorted(range(n),key=lambda w:P[t-1][w]);badge=B[t-1].copy()
  times=[badge[a]+1,badge[b]+1];slots=[P[times[0]][a],P[times[1]][b]]
  x,y=slots;order[x],order[y]=order[y],order[x]
  mid_badges=[badge[w]+1 for w in order]
  u,v=badge[a],badge[b];left,right=order[u],order[v];badge[left],badge[right]=badge[right],badge[left]
  assert P[t]==[order.index(w) for w in range(n)] and B[t]==badge
  trace.append({'step':t,'pair':[names[a],names[b]],'read_times':times,'card_slots':[x+1,y+1],'middle_words':[names[w] for w in order],'middle_badges':mid_badges,'badge_slots':[u+1,v+1],'badge_recipients':[names[left],names[right]],'words':[names[w] for w in order],'badges':[badge[w]+1 for w in order]})
 observations=[]
 for a,b,tw,dw,sg in clues:
  t=B[-1][tw]+1;gap=P[t][a]-P[t][b];d=B[-1][dw]+1;assert gap==sg*d
  observations.append({'time':t,'left_word':names[b] if sg>0 else names[a],'right_word':names[a] if sg>0 else names[b],'distance':d,'position_a':P[t][a]+1,'position_b':P[t][b]+1})
 order=sorted(range(n),key=lambda w:P[-1][w]);indices=[B[0][w]+1 for w in order]
 answer=''.join(names[w][B[0][w]] for w in order)
 return {'trace':trace,'observations':observations,'final_words':[names[w] for w in order],'initial_indices':indices,'answer':answer}

def group_worker(args):
 n,program,clues,relevant,values,timeout=args
 m,P,B,meta=build(n,program,clues,packing=False)
 for w,v in zip(relevant,values):m.linear([B[-1][w]],[1],[v,v])
 solutions=[];runs=[]
 for _ in range(2):
  r=solve(m,P,B,timeout,1,2);runs.append({k:v for k,v in r.items() if k not in ['P','B']})
  if 'P' not in r:break
  solutions.append({'P':r['P'],'B':r['B']});exclude(m,P,B,r)
 return {'values':list(values),'solutions':solutions,'runs':runs}

def solve_grouped(n,program,clues,workers=2,timeout=120):
 from concurrent.futures import ProcessPoolExecutor
 st=time.perf_counter();rows=terminal_rows(n,clues);relevant=sorted(set(c[3] for c in clues));groups=sorted(set(tuple(row[w] for w in relevant) for row in rows));prep=time.perf_counter()-st
 jobs=[(n,program,clues,relevant,g,timeout) for g in groups]
 with ProcessPoolExecutor(max_workers=workers) as ex:out=list(ex.map(group_worker,jobs))
 solutions=[s for g in out for s in g['solutions']]
 complete=all(g['runs'][-1]['result']=='INFEASIBLE' for g in out)
 return {'solutions':solutions,'complete':complete,'groups':out,'packing':{'raw_terminal_badge_permutations':__import__('math').factorial(n),'terminal_badge_survivors':len(rows),'distance_word_indices':relevant,'distance_groups':len(groups),'packing_seconds':prep},'workers':workers,'seconds':time.perf_counter()-st,'branches':sum(r['branches'] for g in out for r in g['runs']),'conflicts':sum(r['conflicts'] for g in out for r in g['runs']),'sum_solve_seconds':sum(r['seconds'] for g in out for r in g['runs'])}
