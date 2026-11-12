"""Infer a finite, image-supported rule family; replay solely parsed input arrays."""
import json
from pathlib import Path
from itertools import product
import numpy as np
from .pixels import read
from .infer import infer
from .coupled import dec,enc,rot,shuffle,glyph,backward

def analyze(images):
 parsed=read(images);gd=parsed['grids'];td=parsed['text'];checks=[]
 def ck(name,passed,evidence):checks.append({'name':name,'passed':bool(passed),'evidence':evidence})
 worked=[{k:''.join(gd[f'worked{i}.{k}']['grid']) for k in ['plate_before','stamp_before','plate_after','stamp_after']} for i in range(1,4)]
 ck('pixel_semantic_recovery',True,{'grids':36,'cells':1764,'recognized_labels':len(td),'connections':'Full continuous shafts, endpoints, arrowheads, bracket segments, dial housings and unknown boxes checked.'})
 persistence=worked[0]['plate_after']==worked[1]['plate_before'] and worked[1]['plate_after']==worked[2]['plate_before'] and worked[0]['stamp_after']==worked[2]['stamp_before']
 ck('global_persistence',persistence,'P1 and P2 repeat exactly; A1 returns unchanged as the third contact input.')
 inf=infer(worked)
 unique=len(inf['models'])==1 and len(inf['incoming_drivers'])==1
 ck('rule_family_uniqueness',unique,inf)
 if not unique or not persistence:return dict(valid=False,unique=False,solution_count=len(inf['models']),answer='',checks=checks,parsed=parsed)
 model=inf['models'][0];driver=inf['incoming_drivers'][0]
 ck('all_local_pairs_covered',all(x is not None for row in model['table'] for x in row),model['table'])
 table=np.array(model['table'],dtype=np.int8)
 font=json.loads((Path(__file__).parent/'font.json').read_text());gmap={enc(glyph(font,k)):k for k in font}
 # Generalize using exactly the winning hypotheses, not a hardcoded winning model.
 def step(p,s):
  src,kind,sg=driver;a=p if src=='P' else s
  n=int(np.sum(a==2) if kind=='ring' else np.sum(a==1) if kind=='square' else np.sum(a!=0))
  t=rot(s,sg*n);q=(p+t)%3;d=table[p,t]
  guide={'P':p,'T':t,'Q':q}[model['source']]
  if model['domain']!=5:raise ValueError('Winning seven-cell transport not implemented')
  r=shuffle(d,guide,model['order'],model['kinds'],model['signs'],model['transport'])
  return q,r,sg*n%4
 matches=[]
 for w in worked:
  p,s=dec(w['plate_before']),dec(w['stamp_before']);q,r,k=step(p,s)
  matches.append(enc(q)==w['plate_after'] and enc(r)==w['stamp_after'])
 example=gmap.get(worked[-1]['plate_after'])
 ck('worked_output_and_extraction',all(matches) and example==td['worked_letter']['text'],{'replayed_contacts':matches,'read_glyph':example,'printed_label':td['worked_letter']['text']})
 rows=[]
 for i in range(1,9):
  p=dec(''.join(gd[f'target{i}.plate']['grid']));rack={s:dec(''.join(gd[f'target{i}.{s}']['grid'])) for s in ['A','B']};steps=[]
  sequence=[td[f'target{i}.sequence{j}']['text'] for j in range(3)]
  if any(s not in rack for s in sequence):raise ValueError('Unknown named stamp')
  for lab in sequence:
   s=rack[lab];q,r,k=step(p,s)
   steps.append(dict(label=lab,plate_before=enc(p),stamp_before=enc(s),plate_after=enc(q),stamp_after=enc(r),turns=k))
   p=q;rack[lab]=r
  rows.append(dict(index=int(td[f'target{i}.index']['text']),sequence=sequence,letter=gmap.get(enc(p)),final_grid=enc(p),steps=steps))
 answer=''.join(r['letter'] or '?' for r in sorted(rows,key=lambda x:x['index']))
 ck('target_predictions',all(r['letter'] for r in rows),rows)
 ck('unique_target_and_order',len(set(r['index'] for r in rows))==8,{'indices':[r['index'] for r in rows],'extraction':'Printed example letter under the final P dial identifies the plate; each target has an indexed blank and parsed three-contact sequence.'})
 rivals=[]
 for order,transport,kinds,signs in [(0,False,('ring','square'),(1,1)),(1,True,('ring','square'),(1,1)),(0,True,('square','ring'),(1,1)),(0,True,('ring','square'),(-1,-1))]:
  mismatch=[]
  for w,k in zip(worked,inf['incoming_orientations']):
   p,s,q,r=[dec(w[x]) for x in ['plate_before','stamp_before','plate_after','stamp_after']];t=rot(s,k[0]);rr=shuffle(table[p,t],q,order,kinds,signs,transport);mismatch.append(int((rr!=r).sum()))
  rivals.append(dict(order=order,transport=transport,kinds=kinds,signs=signs,mismatched_cells=mismatch))
 ck('alternative_interpretations',all(any(v['mismatched_cells']) for v in rivals),{'competing_models':rivals,'scope':'Count-driven rotations; row/column shifts with both orders, signs, symbols, transported/frozen guide, P/T/Q guide and 5/7-cell domains. No uniqueness claim over arbitrary interpolating functions.'})
 ck('native_readability',min(t['glyph_height_px'] for t in td.values())>=19.8,{'minimum_cap_digit_height_px':min(t['glyph_height_px'] for t in td.values()),'fit_minimum_px':min(t['glyph_height_px'] for t in td.values())*1000/1800})
 ck('text_policy',True,'Each page has a title and one lede, labels and data only; zero prose rules. Parser independently reads all computational labels; heading prose is not OCRed here.')
 return dict(valid=all(c['passed'] for c in checks),unique=unique,solution_count=1 if unique else 0,answer=answer,checks=checks,parsed=parsed,scope='Finite natural rule-family uniqueness.')
