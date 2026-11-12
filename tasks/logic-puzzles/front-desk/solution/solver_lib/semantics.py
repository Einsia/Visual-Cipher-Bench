"""Recover spatial separation constraints and verify the four-card example."""
import re

def recover(records,wire_data):
 by={r['id']:r['observed'] for r in records}
 def txt(page,i):return by[f'text_{page:02d}_{i:03d}']
 def num(page,i):
  v=txt(page,i)
  if not re.fullmatch('[1-8]',v):raise ValueError(f'Expected visible digit: page {page}, label {i}: {v}')
  return int(v)
 def rack(page,start,n=4):
  slots=[num(page,start+3*i) for i in range(n)]
  if slots!=list(range(1,n+1)):raise ValueError('Nonsequential slot labels')
  words=[txt(page,start+3*i+1) for i in range(n)];badges=[num(page,start+3*i+2) for i in range(n)]
  if len(set(words))!=n or sorted(badges)!=list(range(1,n+1)):raise ValueError('Example is not a bijection')
  return {'words':words,'badges':badges}
 states=[rack(1,i) for i in (4,18,32,46,61)]
 middles=[];queries=[];traces=[]
 alternatives={'word_only_card_swap':[],'named_badge_exchange':[],'final_badge_extraction':[],'always_final_snapshot':[]}
 for k,start in enumerate((74,91,106,121),1):
  pair=[txt(1,start),txt(1,start+5)]
  times=[num(1,start+1),num(1,start+6)]
  slots=[num(1,start+4),num(1,start+9)]
  for j,w in enumerate(pair):
   if txt(1,start+2+5*j)!='After '+str(times[j]) or txt(1,start+3+5*j)!=w:raise ValueError('Broken query labels')
   if states[k-1]['badges'][states[k-1]['words'].index(w)]!=times[j]:raise ValueError('Query does not use current named badge')
   if states[times[j]]['words'].index(w)+1!=slots[j]:raise ValueError('Wrong addressed snapshot slot')
   if states[-1]['words'].index(w)+1!=slots[j]:alternatives['always_final_snapshot'].append(k)
  middle=rack(2,4+33*(k-1));after=rack(2,16+33*(k-1));middles.append(middle)
  if after!=states[k]:raise ValueError('Repeated After state differs across pages')
  words=states[k-1]['words'].copy();badges=states[k-1]['badges'].copy();x,y=[s-1 for s in slots]
  words[x],words[y]=words[y],words[x];badges[x],badges[y]=badges[y],badges[x]
  if {'words':words,'badges':badges}!=middle:raise ValueError('Whole-card exchange disagrees with intermediate state')
  if badges!=states[k-1]['badges']:alternatives['word_only_card_swap'].append(k)
  bs=28+33*(k-1)
  if txt(2,bs)!='Swap badges' or [txt(2,bs+1),txt(2,bs+4)]!=pair:raise ValueError('Badge phase pair mismatch')
  if [num(2,bs+2),num(2,bs+5)]!=times or [num(2,bs+3),num(2,bs+6)]!=times:raise ValueError('Badge direct slot labels disagree')
  u,v=[t-1 for t in times];wrong=badges.copy();wa,wb=[words.index(w) for w in pair];wrong[wa],wrong[wb]=wrong[wb],wrong[wa]
  badges[u],badges[v]=badges[v],badges[u]
  if badges!=after['badges']:raise ValueError('Badge-only exchange disagrees with After state')
  if wrong!=after['badges']:alternatives['named_badge_exchange'].append(k)
  traces.append(dict(step=k,pair=pair,read_times=times,card_slots=slots,middle=middle,after=after,badge_slots=times))
 ex_words=[];ex_indices=[];ex_letters=[]
 source_badges=[num(2,136+2*j) for j in range(4)]
 if [num(2,135+2*j) for j in range(4)]!=[1,2,3,4] or source_badges!=states[0]['badges']:
  raise ValueError('Initial-slot badge row does not match initial example')
 routes=wire_data['02.png']['sources']
 alternatives['identity_attached_initial_badge']=[]
 for j in range(4):
  if num(2,144+3*j)!=j+1:raise ValueError('Final extraction slots malformed')
  word=txt(2,145+3*j);letter=txt(2,146+3*j);idx=source_badges[routes[j]-1]
  if word!=states[-1]['words'][j] or word[idx-1]!=letter:raise ValueError('Routed example extraction wrong')
  old=states[0]['badges'][states[0]['words'].index(word)]
  if word[old-1]!=letter:alternatives['identity_attached_initial_badge'].append(j+1)
  final=states[-1]['badges'][j]
  if word[final-1]!=letter:alternatives['final_badge_extraction'].append(j+1)
  ex_words.append(word);ex_indices.append(idx);ex_letters.append(letter)
 time_word=txt(2,157);time=num(2,158);distance_word=txt(2,161);distance=num(2,162)
 if time!=states[-1]['badges'][states[-1]['words'].index(time_word)]:raise ValueError('Distance example time selector wrong')
 if distance!=states[-1]['badges'][states[-1]['words'].index(distance_word)]:raise ValueError('Distance example badge value wrong')
 sample=rack(2,163)
 if sample!=states[time] or txt(2,159)!='After '+str(time):raise ValueError('Distance selected snapshot wrong')
 if num(2,175)!=distance:raise ValueError('Interval bracket count wrong')
 # Two endpoint words are visible above the same straight-line bracket.
 if sample['words'].index(time_word)-sample['words'].index(distance_word)!=distance:raise ValueError('Distance is not the visible nonwrapping slot difference')
 names=[txt(1,i) for i in range(137,145)]
 inventory_badges=[num(1,i) for i in range(145,153)]
 if sorted(inventory_badges)!=list(range(1,9)):raise ValueError('Badge inventory is not 1 through 8 once each')
 if txt(1,135)!='Cards ×1' or txt(1,136)!='Badges ×1':raise ValueError('One-of-each inventory convention missing')
 for j in range(8):
  if num(1,154+3*j)!=j+1 or txt(1,155+3*j)!='?' or txt(1,156+3*j)!='?':raise ValueError('Initial unknown rack malformed')

 program=[]
 for i in range(8):
  if txt(3,2+3*i)!='Step '+str(i+1):raise ValueError('Program step order malformed')
  program.append([names.index(txt(3,k)) for k in (3+3*i,4+3*i)])
 # Spatial observation panels: OCR supplies words; layout supplies orientation.
 page3=[r for r in records if r['image']=='03.png']
 def at(y,x0,x1):
  return sorted([r for r in page3 if abs(r['y']-y)<.1 and x0<=r['x']<x1],key=lambda r:r['x'])
 for center_y,wanted in [(1640,list(map(str,range(1,9)))),(1700,['?']*8),(1924,list(map(str,range(1,9))))]:
  rr=sorted([r for r in page3 if center_y<r['y']<center_y+15],key=lambda r:r['x'])
  # The Final label shares the last row but lies before its first square.
  if center_y==1924:rr=[r for r in rr if r['observed']!='Final']
  if [r['observed'] for r in rr]!=wanted:raise ValueError('Malformed extraction port row')
 clues=[];sentences=[]
 for i in range(8):
  x=136+738*(i%2);y=660+224*(i//2)
  top=at(y+24,x,x+680)
  if len(top)!=2 or top[0]['observed']!='After':raise ValueError('Missing observation time selector')
  tw=top[1]['observed']
  bottom=at(y+180,x,x+680)
  if len(bottom)!=3 or bottom[0]['observed']!='Separation' or bottom[2]['observed']!='slots':raise ValueError('Missing separation selector')
  dw=bottom[1]['observed']
  middle=at(y+92,x,x+680)
  if len(middle)==1 and middle[0]['observed']=='Either order':
   upper=at(y+78,x,x+680);lower=at(y+124,x,x+680)
   if len(upper)!=1 or len(lower)!=1:raise ValueError('Incomplete unordered endpoint pair')
   a,b=upper[0]['observed'],lower[0]['observed'];sg=0
  elif len(middle)==2:
   b,a=[r['observed'] for r in middle];sg=1
  else:raise ValueError('Unrecognized observation geometry')
  clues.append([names.index(w) for w in (a,b,tw,dw)]+[sg])
  sentences.append(dict(time_word=tw,endpoint_a=a,endpoint_b=b,distance_word=dw,relation='absolute separation' if sg==0 else 'a spatially right of b'))
 if not all(alternatives.values()):raise ValueError('Worked example does not discriminate all modeled alternatives')
 return dict(extraction_sources=wire_data['03.png']['sources'],names=names,program=program,clues=clues,clue_sentences=sentences,inventory_badges=inventory_badges,example_states=states,example_trace=traces,example_extraction=dict(words=ex_words,indices=ex_indices,letters=ex_letters),alternative_interpretations_contradicted_at=alternatives,distance_example=dict(time_word=time_word,time=time,distance_word=distance_word,distance=distance,left=distance_word,right=time_word))

def replay(names,program,clues,history,extraction_sources):
 n=len(names);P,B=history['P'],history['B']
 if len(P)!=n+1 or len(B)!=n+1 or any(sorted(row)!=list(range(n)) for row in P+B):raise ValueError('History is not a sequence of permutations')
 for t,(a,b) in enumerate(program,1):
  order=sorted(range(n),key=lambda w:P[t-1][w]);badge=B[t-1].copy()
  x,y=P[badge[a]+1][a],P[badge[b]+1][b];order[x],order[y]=order[y],order[x]
  u,v=badge[a],badge[b];ca,cb=order[u],order[v];badge[ca],badge[cb]=badge[cb],badge[ca]
  if P[t]!=[order.index(w) for w in range(n)] or B[t]!=badge:raise ValueError('Invalid transition')
 for a,b,tw,dw,sg in clues:
  t=B[-1][tw]+1
  gap=P[t][a]-P[t][b];distance=B[-1][dw]+1
  if (gap!=sg*distance if sg else abs(gap)!=distance):raise ValueError('Invalid clue')
 order=sorted(range(n),key=lambda w:P[-1][w])
 initial_order=sorted(range(n),key=lambda w:P[0][w])
 return ''.join(names[w][B[0][initial_order[src-1]]] for w,src in zip(order,extraction_sources))
