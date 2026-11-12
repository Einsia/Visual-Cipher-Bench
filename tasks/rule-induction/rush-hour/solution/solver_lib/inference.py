"""Finite, explicit natural competitor family; no puzzle instance or answer here."""
from itertools import product, permutations

EDGES=('out','in','none','relabel')
SCOPES=('none','a','b','all','marked','unmarked','shortest','longest')
ORDERS=tuple(''.join(x) for x in permutations('SRM'))

def inverse(p):
    r=[0]*len(p)
    for x,y in enumerate(p):r[y]=x
    return tuple(r)

def orbit(p,x):
    out=[]
    while x not in out:
        out.append(x);x=p[x]
    return out

def components(p):
    seen=set();out=[]
    for x in range(len(p)):
        if x not in seen:
            c=orbit(p,x);seen.update(c);out.append(c)
    return out

def reverse_nodes(p,nodes):
    r=list(p);inv=inverse(p)
    for x in nodes:r[x]=inv[x]
    return tuple(r)

def select(p,a,b,scope):
    cs=components(p)
    if scope=='none':return []
    if scope=='a':return orbit(p,a)
    if scope=='b':return orbit(p,b)
    if scope=='all':return list(range(len(p)))
    if scope=='marked':return sorted(set(orbit(p,a)+orbit(p,b)))
    if scope=='unmarked':return sorted(set(range(len(p)))-set(orbit(p,a)+orbit(p,b)))
    size=(min if scope=='shortest' else max)(map(len,cs))
    return [v for c in cs if len(c)==size for v in c]

def walk(p,x,k):
    if k<0:p=inverse(p)
    for _ in range(abs(k)):x=p[x]
    return x

DISTANCES=tuple(range(-3,4))+('pre_own','pre_other','post_own','post_other','total','pre_cycles','post_cycles')

def distance(code,initial,current,marker):
    if isinstance(code,int):return code
    if code=='total':return len(initial[0])
    when,which=code.split('_');s=initial if when=='pre' else current
    if which=='cycles':return len(components(s[0]))
    index=marker if which=='own' else 3-marker
    return len(orbit(s[0],s[index]))

def candidate_step(state,model):
    p,a,b=state;initial=p;initial_state=state
    edge,scope,order,basis,da,db,swap=model
    for op in order:
        if op=='S':
            q=list(p)
            if edge=='out':q[a],q[b]=q[b],q[a]
            elif edge=='in':
                inv=inverse(p);x,y=inv[a],inv[b];q[x],q[y]=q[y],q[x]
            elif edge=='relabel':
                def t(v):return b if v==a else a if v==b else v
                q=[t(p[t(x)]) for x in range(len(p))]
            p=tuple(q)
        elif op=='R':p=reverse_nodes(p,select(p,a,b,scope))
        else:
            source=p if basis=='current' else initial
            current=(p,a,b)
            ka=distance(da,initial_state,current,1);kb=distance(db,initial_state,current,2)
            a,b=walk(source,a,ka),walk(source,b,kb)
    if swap:a,b=b,a
    return p,a,b

def run(state,count,model):
    for _ in range(count):state=candidate_step(state,model)
    return state

def models():
    return product(EDGES,SCOPES,ORDERS,('current','initial'),DISTANCES,DISTANCES,(False,True))

def encode(record):
    names=sorted(record['arrows']);idx={x:i for i,x in enumerate(names)}
    state=tuple(idx[record['arrows'][x]] for x in names),idx[record['triangle']],idx[record['square']]
    assert sorted(state[0])==list(range(len(names)))
    assert state[1]!=state[2]
    return names,state

def decode(names,state):
    p,a,b=state
    return {'arrows':{x:names[p[i]] for i,x in enumerate(names)},'triangle':names[a],'square':names[b]}

def readout(names,state):return ''.join(names[x] for x in orbit(state[0],state[1]))

def encoded_examples(data):
    result=[]
    for e in data['examples']:
        names,inp=encode(e['input']);outnames,out=encode(e['output'])
        assert names==outnames
        result.append((names,inp,e['operations'],out))
    return result

def filter_models(data,include=None):
    ex=encoded_examples(data)
    if include is not None:ex=[ex[i] for i in include]
    remaining=list(models());counts=[len(remaining)]
    for _,inp,n,out in ex:
        remaining=[m for m in remaining if run(inp,n,m)==out]
        counts.append(len(remaining))
    return remaining,counts


def extraction(names,state,choice):
 start,direction,include,all_components=choice
 p,a,b=state;p=p if direction==1 else inverse(p);node=a if start=='triangle' else b
 seen=orbit(p,node);read=seen if include else seen[1:]
 if all_components:
  used=set(seen)
  for c in components(p):
   if not used.intersection(c):read+=c;used.update(c)
 return ''.join(names[x] for x in read)

def solve_data(data):
 examples=encoded_examples(data);survivors,counts=filter_models(data)
 if not survivors:raise ValueError('No model fits the complete visible examples')
 methods=[]
 for choice in product(('triangle','square'),(1,-1),(True,False),(False,True)):
  if all(extraction(names,out,choice)==e['readout'] for (names,_,_,out),e in zip(examples,data['examples'])):methods.append(choice)
 if len(methods)!=1:raise ValueError('Readout convention is absent or ambiguous')
 names,state=encode(data['target']['input']);histories=[];answers=set()
 for model in survivors:
  s=state;history=[decode(names,s)]
  for _ in range(data['target']['operations']):s=candidate_step(s,model);history.append(decode(names,s))
  answer=extraction(names,s,methods[0])
  if len(answer)==data['target']['answer_length']:
   answers.add(answer);histories.append({'model':model,'states':history,'answer':answer})
 if len(answers)!=1:raise ValueError('Target lacks unique answer consistent with blank count')
 return {'answer':next(iter(answers)),'model_counts':counts,'models':survivors,'extraction':methods[0],'prediction_count':len(answers),'histories':histories,'family_scope':'4 splice operations × 8 reversal scopes × 6 orders × 2 motion bases × 14 distances for each marker × 2 marker swaps. This is bounded natural-family uniqueness, not exclusion of arbitrary functions.'}
