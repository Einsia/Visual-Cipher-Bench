"""Finite geometry and local Boolean rules; no answer-dependent logic."""
import itertools

# Readable, ordinary 5x5 capital silhouettes. This is a recognition alphabet,
# not a cipher; every possible capital is available to the verifier.
FONT_RAW = {
'A':'11111/10001/11111/10001/10001',
'B':'11110/10001/11110/10001/11110',
'C':'11111/10000/10000/10000/11111',
'D':'11110/10001/10001/10001/11110',
'E':'11111/10000/11110/10000/11111',
'F':'11111/10000/11110/10000/10000',
'G':'11111/10000/10111/10001/11111',
'H':'10001/10001/11111/10001/10001',
'I':'11111/00100/00100/00100/11111',
'J':'00111/00010/00010/10010/01100',
'K':'10001/10010/11100/10010/10001',
'L':'10000/10000/10000/10000/11111',
'M':'10001/11011/10101/10001/10001',
'N':'10001/11001/10101/10011/10001',
'O':'11111/10001/10001/10001/11111',
'P':'11110/10001/11110/10000/10000',
'Q':'01110/10001/10101/10010/01101',
'R':'11111/10001/11111/10010/10001',
'S':'11111/10000/11111/00001/11111',
'T':'11111/00100/00100/00100/00100',
'U':'10001/10001/10001/10001/01110',
'V':'10001/10001/10001/01010/00100',
'W':'10001/10001/10101/11011/10001',
'X':'10001/01010/00100/01010/10001',
'Y':'10001/01010/00100/00100/00100',
'Z':'11111/00010/00100/01000/11111',
}
FONT = {k: [int(c) for c in v if c != '/'] for k,v in FONT_RAW.items()}
GEOMETRIES = {
 'identity': lambda r,c:(r,c),
 'left_right': lambda r,c:(r,4-c),
 'up_down': lambda r,c:(4-r,c),
 'half_turn': lambda r,c:(4-r,4-c),
 'clockwise': lambda r,c:(4-c,r),
 'anticlockwise': lambda r,c:(c,4-r),
 'transpose': lambda r,c:(c,r),
 'antitranspose': lambda r,c:(4-c,4-r),
}
PERMS = {k:[5*f(r,c)[0]+f(r,c)[1] for r in range(5) for c in range(5)] for k,f in GEOMETRIES.items()}
FUNCTIONS = {'keep':(0,1), 'invert':(1,0), 'white':(0,0), 'black':(1,1)}


def flat(a):
 return [int(c) for row in a for c in row] if len(a)==5 else list(a)


def matrix(a):
 return [''.join(map(str,a[i:i+5])) for i in range(0,25,5)]


def step(a, model):
 p=PERMS[model['geometry']]
 return [FUNCTIONS[f][a[p[i]]] for i,f in enumerate(model['functions'])]


def forward(a, sequence, models):
 trace=[list(a)]
 for s in sequence: trace.append(step(trace[-1],models[s]))
 return trace


def infer_forward(examples):
 models={}; stats={}; rejects={}
 for symbol in sorted({e['symbol'] for e in examples}):
  es=[e for e in examples if e['symbol']==symbol]
  gs=[g for g,p in PERMS.items() if all([flat(e['before'])[p[i]] for i in range(25)]==flat(e['intermediate']) for e in es)]
  candidates=[]
  for i in range(25):
   candidates.append([f for f,t in FUNCTIONS.items() if all(t[flat(e['intermediate'])[i]]==flat(e['after'])[i] for e in es)])
  count=len(gs)
  for c in candidates:count*=len(c)
  stats[symbol]={'geometries_tested':8,'geometries_surviving':gs,'cell_functions_tested':100,'cell_domain_sizes':[len(c) for c in candidates],'model_count':count}
  if count!=1: raise ValueError(f'Nonunique rule for {symbol}: {stats[symbol]}')
  models[symbol]={'geometry':gs[0], 'functions':[c[0] for c in candidates]}
  # Concrete familiar competitor families, checked on all full observations.
  competing={}
  for name, allowed in [('pure_geometry',{'keep'}),('xor_only',{'keep','invert'}),('black_only',{'keep','black'}),('white_only',{'keep','white'})]:
   survivors=[]
   for g,p in PERMS.items():
    if all(any(all(FUNCTIONS[f][flat(e['before'])[p[i]]]==flat(e['after'])[i] for e in es) for f in allowed) for i in range(25)):
     survivors.append(g)
   competing[name]=survivors
  rejects[symbol]=competing
 return models,stats,rejects


def infer_truth_tables(examples):
 # Independent fitting: observed input/output pairs directly fill each truth table.
 models={}; stats={}
 for symbol in sorted({e['symbol'] for e in examples}):
  es=[e for e in examples if e['symbol']==symbol]
  tables=[[None,None] for _ in range(25)]
  for e in es:
   for i,(b,v) in enumerate(zip(flat(e['intermediate']),flat(e['after']))):
    if tables[i][b] not in (None,v): raise ValueError('Conflicting local truth table')
    tables[i][b]=v
  if any(None in t for t in tables):raise ValueError('Unobserved input colour')
  transforms=[]
  for g,p in PERMS.items():
   if all(all(flat(e['before'])[p[i]]==flat(e['intermediate'])[i] for i in range(25)) for e in es):transforms.append(g)
  if len(transforms)!=1:raise ValueError('Nonunique geometric transform')
  names={v:k for k,v in FUNCTIONS.items()}
  models[symbol]={'geometry':transforms[0],'functions':[names[tuple(t)] for t in tables]}
  stats[symbol]={'observed_boolean_entries':50,'geometry_candidates':8,'survivors':len(transforms)}
 return models,stats


def backward(a, sequence, models):
 # Each output pixel follows a dependency backwards until the last opaque write.
 out=[]; visits=0
 for dest in range(25):
  i=dest; invert=0; value=None
  for symbol in reversed(sequence):
   visits+=1
   m=models[symbol]; f=m['functions'][i]
   if f in ('black','white'):
    value=(int(f=='black')^invert); break
   invert ^= int(f=='invert')
   i=PERMS[m['geometry']][i]
  if value is None:value=a[i]^invert
  out.append(value)
 return out,visits


def recognize(a):
 hits=[k for k,v in FONT.items() if list(a)==v]
 if len(hits)!=1:raise ValueError(f'Not a unique capital: {matrix(a)}, candidates={hits}')
 return hits[0]
