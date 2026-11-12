"""Interpret connected sample/ring diagrams, and replay a simultaneous history."""
import re

def recover(records,images):
 by={r['id']:r['observed'] for r in records};coords={r['id']:(r['x'],r['y']) for r in records}
 def txt(key):return by[key].strip()
 def num(key):
  v=txt(key)
  if not re.fullmatch('[1-8]',v):raise ValueError('Missing digit '+key+': '+v)
  return int(v)
 def state(prefix):
  ws=[txt(f'{prefix}_{j}_word') for j in range(4)];bs=[num(f'{prefix}_{j}_badge') for j in range(4)]
  if len(set(ws))!=4 or sorted(bs)!=[1,2,3,4]:raise ValueError('Malformed calibration state')
  if [num(f'{prefix}_slot{j}') for j in range(4)]!=[1,2,3,4]:raise ValueError('Fixed slots malformed')
  return dict(words=ws,badges=bs)
 states=[state(f'ex{t}') for t in range(5)]
 from .calibration import infer_transfers,infer_extraction,value
 pairs=[]
 for k in range(4):
  if txt(f'ex_step{k}')!='Step '+str(k+1):raise ValueError('Calibration order')
  pairs.append([txt(f'query{k}_{j}_word') for j in range(2)])
 if txt('phase_tubes')!='Exchange tubes' or txt('phase_rings')!='Then: rings':raise ValueError('Missing phase order')
 inference=infer_transfers(states,pairs);traces=inference['traces']
 letters=[];words=[]
 if txt('extract_final')!='Final':raise ValueError('Final extraction order missing')
 for j in range(4):
  word=txt(f'extract{j}_word');badge=num(f'extract{j}_badge');ch=txt(f'extract{j}_letter')
  if num(f'extract{j}_slot')!=j+1 or word!=states[-1]['words'][j] or badge!=states[-1]['badges'][j]:raise ValueError('Final order mismatch')
  words.append(word);letters.append(ch)
 extraction=infer_extraction(states,words,letters)
 tw,dw=txt('obs_time_word'),txt('obs_distance_word')
 if any(txt(key)!='?' for key in ['obs_time_value','obs_distance_value','obs_gap']) or txt('obs_after')!='After ?':raise ValueError('Observation example must leave redundant numbers unfilled')
 sample=state('obs_state');matches=[i for i,st in enumerate(states) if st==sample]
 if len(matches)!=1:raise ValueError('Observation snapshot cannot be recognized uniquely')
 t=matches[0]
 # Read actual bracket arms from raster pixels alongside the four visible rows.
 from pathlib import Path
 from PIL import Image
 import numpy as np
 a=np.asarray(Image.open(Path(images)/'02.png').convert('L'))
 arms=[]
 for j in range(4):
  cy=round(coords[f'obs_state_{j}_badge'][1]-10)
  if np.mean(a[cy-2:cy+3,1800:1860]<200)>.35:arms.append(j)
 if len(arms)!=2:raise ValueError('Observation must have exactly two bracket endpoints')
 d=arms[1]-arms[0]
 if t!=value(states[-1],tw,'ring') or d!=value(states[-1],dw,'ring'):raise ValueError('Final rings disagree with spatially recovered snapshot and interval')
 distance=dict(time=t,distance=d,endpoint_slots=[j+1 for j in arms],
               endpoints=[sample['words'][j] for j in arms],
               method='snapshot equality and raster bracket arms; no printed numeric trace')
 names=[txt(f'inventory{j}_word') for j in range(8)]
 if len(set(names))!=8 or any(not re.fullmatch('[A-Z]{8}',w) for w in names):raise ValueError('Specimen inventory')
 if sorted(num(f'inventory_ring{j}') for j in range(8))!=list(range(1,9)):raise ValueError('Ring inventory')
 if txt('inventory_label')!='Sound specimens ×1' or txt('rings_label')!='Rings ×1':raise ValueError('Use-once inventory')
 program=[]
 for k in range(8):
  if num(f'program{k}_step')!=k+1:raise ValueError('Transfer sequence')
  program.append([names.index(txt(f'program{k}_{side}')) for side in ('a','b')])
 clues=[];sentences=[]
 for k in range(8):
  upper,lower,tw,dw=[txt(f'clue{k}_{s}') for s in ('upper','lower','time','distance')]
  if coords[f'clue{k}_upper'][1]>=coords[f'clue{k}_lower'][1]:raise ValueError('Bracket orientation')
  clues.append([names.index(w) for w in (lower,upper,tw,dw)]+[1]);sentences.append(f'After final({tw}), {lower} is final({dw}) slots below {upper}.')
 return dict(names=names,program=program,clues=clues,clue_sentences=sentences,example_trace=traces,example_extraction=extraction,distance_example=distance,rule_inference=inference)
def replay(names,program,clues,history):
 n=len(names);P,B=history['P'],history['B']
 if len(P)!=n+1 or len(B)!=n+1 or any(sorted(row)!=list(range(n)) for row in P+B):raise ValueError('History is not a sequence of permutations')
 for t,(a,b) in enumerate(program,1):
  order=sorted(range(n),key=lambda w:P[t-1][w]);badge=B[t-1].copy()
  x,y=P[badge[a]+1][a],P[badge[b]+1][b];order[x],order[y]=order[y],order[x]
  u,v=badge[a],badge[b];ca,cb=order[u],order[v];badge[ca],badge[cb]=badge[cb],badge[ca]
  if P[t]!=[order.index(w) for w in range(n)] or B[t]!=badge:raise ValueError('Invalid transition')
 for a,b,tw,dw,sg in clues:
  t=B[-1][tw]+1
  if P[t][a]-P[t][b]!=sg*(B[-1][dw]+1):raise ValueError('Invalid clue')
 order=sorted(range(n),key=lambda w:P[-1][w])
 return ''.join(names[w][B[0][w]] for w in order)
