"""PNG -> geometry and endpoint letters -> hidden arithmetic induction -> exhaustive search.

Runtime input is limited to PNGs and generic font/search code. The parser must
recover exactly one supported transition rule before the target engine runs.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from pixels import parse
from search import solve
from model import evaluate,single_loop

def run(images):
    public=parse(images)
    proof=solve(public['row_totals'],public['column_totals'],public['labels'],workers=4)
    answers=[]
    for s in proof['solutions']:
        if not single_loop(s['masks']):raise ValueError('search returned invalid loop')
        d=evaluate(s['masks'],public['letters'],s['order'])
        if d['row_totals']!=public['row_totals']or d['column_totals']!=public['column_totals']:raise ValueError('independent replay failed')
        answers.append(d['answer'])
    return {'valid':len(answers)==1,'unique':len(answers)==1,'solution_count':len(answers),'answer':answers[0]if len(answers)==1 else None,'answers':answers,'public_data':public,'proof':proof}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    try:result=run(args.images)
    except Exception as e:result={'valid':False,'unique':False,'solution_count':None,'answer':None,'error':str(e)}
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result.get(k)for k in ['valid','unique','solution_count','answer','error']}))

    sys.exit(0 if result.get('valid') else 1)
