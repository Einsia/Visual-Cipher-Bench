"""Exhaustive joint loop/schedule reconstruction from printed margins and circled labels."""
import concurrent.futures as cf,itertools,json,os,subprocess,tempfile,time
from pathlib import Path
from model import evaluate

def schedules(labels):
 n=len(labels)//2
 if len(labels)!=2*n:raise ValueError('bad label count')
 given=[v for v in labels if v is not None]
 if len(set(given))!=len(given) or any(v<1 or v>2*n for v in given):raise ValueError('invalid circled labels')
 missing=sorted(set(range(1,2*n+1))-set(given));unknown=[i for i,v in enumerate(labels)if v is None]
 out=[]
 for fill in itertools.permutations(missing):
  complete=list(labels)
  for op,k in zip(unknown,fill):complete[op]=k
  out.append(sorted(range(2*n),key=lambda op:complete[op]))
 return sorted(out)

def solve(row_totals,column_totals,labels,route='row',workers=None):
 start=time.perf_counter();workers=min(16,max(1,int(workers or os.environ.get('PUZZLE_WORKERS','2'))))
 if len(row_totals)!=6 or len(column_totals)!=6:raise ValueError('Production is 6 by 6')
 orders=schedules(labels)
 if sum(row_totals)!=sum(column_totals):return {'exhaustive':True,'solution_count':0,'solutions':[],'seconds':time.perf_counter()-start,'reason':'margin masses disagree'}
 data=f'1 {len(orders)}\n'+' '.join(map(str,row_totals+column_totals))+'\n'+'\n'.join(' '.join(map(str,o))for o in orders)+'\n'
 binary=Path(__file__).resolve().parent/'native'/('schedule_rows-linux-x86_64'if route=='row'else'schedule_edges-linux-x86_64')
 reports=[];first=None
 with tempfile.TemporaryDirectory(prefix='loop-schedule-')as td:
  p=Path(td);(p/'input').write_text(data)
  args=[[str(i)]for i in range(64)]if route=='row'else[[str(i),str(k)]for i in range(36)for k in range(64)]
  def job(arg):return json.loads(subprocess.run([str(binary),str(p/'input')]+arg,check=True,capture_output=True,text=True,timeout=590).stdout)
  with cf.ThreadPoolExecutor(max_workers=workers)as ex:
   for f in cf.as_completed([ex.submit(job,a)for a in args]):
    d=f.result();reports.append(d)
    if d['solution_count']and first is None:first=time.perf_counter()-start
 result={'route':route,'exhaustive':True,'workers':workers,'jobs':len(reports),'orders_tested':orders,'solutions':sum([d['solutions']for d in reports],[])}
 for key in reports[0]:
  if key!='solutions':result[key]=sum(d[key]for d in reports)
 if route=='row':
  # A cell with four boundary edges is the entire loop, not a larger-loop component.
  # Interior isolated cells and exterior single-cell holes are excluded by the row engine.
  # Only the 36 single-cell interiors can be legal single loops and are restored here.
  result['single_cell_cases']=36*len(orders)
  for r in range(6):
   for c in range(6):
    masks=[0]*6;masks[r]=1<<c
    for oi,order in enumerate(orders):
     d=evaluate(masks,order=order)
     if d['row_totals']==row_totals and d['column_totals']==column_totals:result['solutions'].append({'target':0,'order_index':oi,'masks':masks})
 result['solution_count']=len(result['solutions'])
 for s in result['solutions']:s['order']=orders[s['order_index']]
 result['seconds']=time.perf_counter()-start;result['first_solution_observed_seconds']=first
 return result
