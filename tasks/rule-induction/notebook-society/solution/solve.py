"""Standalone raster entry point; reads only PNGs and solver_lib assets."""
import argparse,json
from pathlib import Path
from solver_lib.engine import analyze

def main():
 p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:
  r=analyze(a.images)
  out={k:r[k] for k in ('valid','unique','solution_count','answer')}
 except Exception as e:out=dict(valid=False,unique=False,solution_count=0,answer=None,error=f'{type(e).__name__}: {e}')
 Path(a.output).write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out));return 0 if out['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
