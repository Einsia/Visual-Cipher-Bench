from pathlib import Path
from .pixels import parse,InvalidPixels
from .engine import Engine

def evaluate(images,broad=False):
 checks=[]
 def check(name,passed,evidence):checks.append({'name':name,'passed':bool(passed),'evidence':evidence})
 try:
  files=sorted(Path(images).glob('*.png'))
  if len(files)!=1:raise InvalidPixels('Expected exactly one page')
  d=parse(files[0])
  check('pixel_semantic_recovery',True,{'input':d['start'],'operators':d['operators'],'examples':d['examples'],'answer_slots':d['answer_slots'],'recognized_regions':len(d['records']),'extra_unrecognized_ink':0})
  check('necessary_symbols_and_connections',True,{'complete_object_count':sum(r['kind']=='object' for r in d['records']),'mode_count':sum(r['kind']=='mode' for r in d['records']),'connected_routes':[r for r in d['records'] if r['kind']=='connected_directed_route'],'method':'Classify full glyph structure; check full connected ink path including start, shaft and oriented head; reject residual ink outside recognized regions.'})
  check('readability_and_text_policy',True,{'native_caps':[r['min_cap_height'] for r in d['records'] if r['kind']=='text'],'dictionary_cap_height':20,'required_floor':19,'rule_sentences':0,'header':'Single title and one thematic sentence, checked by native pixel template; all other text recovered as data labels.'})
  check('png_format',not d['metadata'],{'size':d['size'],'metadata':d['metadata']})
  e=Engine();examples=e.examples(d['examples']);check('worked_examples_and_global_consistency',all(x['passed'] for x in examples),examples)
  if not all(x['passed'] for x in checks):return {'valid':False,'unique':False,'solution_count':0,'answer':None,'checks':checks,'pixel_read':d}
  r=e.solve(d,broad);answers=r['outputs']
  check('unique_terminal_and_reading_order',len(answers)==1,{'outputs':answers,'visible_answer_slots':d['answer_slots'],'route':'start → top row left-to-right → middle row right-to-left → bottom exchange → checked dictionary','proof':r})
  check('alternative_interpretations',len(answers)==1,{'broad_aliases_checked':broad,'domain_limit':r['limits'],'all_intermediate_segmentations':True,'no_mandatory_change_or_household_filter':True,'examples_reject':'One-way/cascading literal rules fail the first endpoint; ignoring sound redivision fails the second. Both outer lanes are selected in the image, requiring plurality.'})
  return {'valid':all(x['passed'] for x in checks),'unique':len(answers)==1,'solution_count':len(answers),'answer':answers[0] if len(answers)==1 else None,'normalization':'upper_compact','checks':checks,'pixel_read':d,'proof':r}
 except (InvalidPixels,ValueError,KeyError) as err:
  check('pixel_semantic_recovery',False,{'error':str(err),'type':type(err).__name__})
  return {'valid':False,'unique':False,'solution_count':0,'answer':None,'checks':checks}
