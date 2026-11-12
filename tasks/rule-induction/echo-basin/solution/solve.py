import argparse,json
from pathlib import Path
from solver_lib.analysis import analyze

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 try:
  r=analyze(args.images)
  if not r['valid']:raise ValueError('Image conditions do not yield a unique legible answer: '+','.join(c['name'] for c in r['checks'] if not c['passed']))
  out={'answer':r['answer'],'normalization':'upper_compact'};code=0
 except Exception as e:out={'valid':False,'error':str(e)};code=1
 Path(args.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));return code
if __name__=='__main__':raise SystemExit(main())
