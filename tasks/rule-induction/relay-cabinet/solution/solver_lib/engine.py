import numpy as np
from .pixels import parse,PixelError,need
from .process import models,batch,encode
from .visible import matches,matches_encoded

def analyze(images):
 checks=[]
 try:
  s,metrics=parse(images);checks.append({'name':'pixel_coverage','passed':True,'evidence':'Every printed cartridge identity/face/tag (candidate tags absent), contact ring, continuous stem/rail, downward arrow, question number and candidate read from PNG; both pages audited for unexplained ink.','pages':metrics})
  ms=models();trace=[]
  for e in s['examples']+[s['worked']]:
   ms=ms[np.all(batch(e['initial'],e['bridges'],ms)==encode(e['final']),axis=1)];trace.append(len(ms))
  need(len(ms)>0,'No local process fits the completed observations')
  checks.append({'name':'rule_induction','passed':True,'evidence':{'family_size':138240,'cumulative_survivors':trace,'survivors':ms.tolist(),'scope':'Uniform local processes using depicted participants, identities, tags and faces; excludes arbitrary whole-strip lookup functions.'}})
  w=s['worked'];need([c['letter'] for c in w['candidates'] if matches(c['state'],w['final'])]==[w['letter']],'Worked extraction inconsistent')
  predictions=[]
  for m in ms:
   pred=[]
   for r in s['rows']:
    out=batch(r['initial'],r['bridges'],m[None,:])[0];found=[c['letter'] for c in r['candidates'] if matches_encoded(c['state'],out)];need(len(found)==1,'Question lacks a unique matching candidate');pred.append(found[0])
   predictions.append(''.join(pred))
  need(len(set(predictions))==1,'Surviving models disagree on answers')
  checks.append({'name':'unique_answer_and_order','passed':True,'evidence':{'answers':predictions,'numbers':[r['number'] for r in s['rows']],'worked_letter':w['letter'],'worked_letter_excluded':True}})
  checks.append({'name':'text_policy_and_legibility','passed':all(t['min_glyph_height_px']>=19 for p in metrics for t in p['text_regions']),'evidence':'Two path-font headings and thematic ledes, individual labels, no rule prose; minimum required glyph height is 19 pixels (short side 1700; threshold 18.7).'})
  return {'valid':all(c['passed'] for c in checks),'unique':True,'solution_count':1,'answer':predictions[0],'checks':checks,'transcription':s}
 except (ValueError,OSError,IndexError) as e:
  checks.append({'name':'pixel_or_semantic_integrity','passed':False,'evidence':str(e)})
  return {'valid':False,'unique':False,'solution_count':0,'answer':None,'checks':checks}
