"""Read PNG pixels and solve."""
import argparse,json
from pathlib import Path
from solver_lib.evaluate import evaluate
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--images',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 r=evaluate(a.images,broad=False);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('valid','unique','solution_count','answer')}));raise SystemExit(0 if r['valid'] else 1)
