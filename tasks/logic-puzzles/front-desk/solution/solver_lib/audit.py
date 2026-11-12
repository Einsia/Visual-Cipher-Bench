from .text_reader import read_text,REGIONS
from .geometry import inspect
from .semantics import recover,replay
from .search import solve
from .wires import read_wires
import time

def run(images,seconds=1000):
 start=time.monotonic();checks=[]
 try:
  inspect(images,REGIONS,check_extra=False)
  text=read_text(images)
  checks.append(dict(name='pixel_text_recovery',passed=True,evidence={'regions':len(text),'minimum_cap_height_px':min(r['glyph_height_px'] for r in text if r.get('must_read'))}))
  geo=inspect(images,text)
  checks.append(dict(name='complete_geometry_and_no_extra_symbols',passed=True,evidence=geo))
  wire_data={f:read_wires(images,f) for f in ('02.png','03.png')}
  checks.append(dict(name='routed_extraction_from_pixels',passed=True,evidence=wire_data))
  data=recover(text,wire_data)
  checks.append(dict(name='worked_example_and_rule_basis',passed=True,evidence={'example_trace':data['example_trace'],'extraction':data['example_extraction'],'distance':data['distance_example'],'alternatives_rejected_at':data['alternative_interpretations_contradicted_at']}))
  checks.append(dict(name='puzzle_data_recovered',passed=True,evidence={k:data[k] for k in ('names','program','clues','clue_sentences','extraction_sources')}))
  proof=solve(data['names'],data['program'],data['clues'],seconds)
  answers=[replay(data['names'],data['program'],data['clues'],h,data['extraction_sources']) for h in proof['solutions']]
  unique=proof['complete'] and proof['exhausted'] and len(answers)==1
  checks.append(dict(name='exhaustive_uniqueness',passed=unique,status='checked' if proof['complete'] else 'incomplete',evidence={'nodes':proof['nodes'],'seconds':proof['seconds'],'complete':proof['complete'],'solutions_found':len(answers),'tasks':proof['tasks'],'tasks_finished':proof['tasks_finished'],'exhausted':proof['exhausted'],'conflicts':proof['conflicts'],'cnf_sha256':proof['cnf_sha256'],'boolean_variables':proof['boolean_variables'],'clauses':proof['clauses'],'task_results':proof['task_results']}))
  return dict(valid=unique,unique=unique if proof['complete'] else None,solution_count=len(answers) if proof['complete'] else None,answer=answers[0] if unique else None,status='valid' if unique else proof['status'],checks=checks,proof=proof,total_seconds=time.monotonic()-start)
 except Exception as e:
  checks.append(dict(name='image_or_program_error',passed=False,evidence=str(e)))
  return dict(valid=False,unique=None,solution_count=None,answer=None,status='rejected',checks=checks,total_seconds=time.monotonic()-start)
