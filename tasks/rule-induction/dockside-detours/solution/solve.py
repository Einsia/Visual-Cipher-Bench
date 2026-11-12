import argparse,json
from pathlib import Path
from solver_lib.pixels import compute

def main():
 p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:
  r=compute(a.images);out={'answer':r['answer'],'unique':True}
 except Exception as e:
  out={'valid':False,'error':str(e)}
  Path(a.output).write_text(json.dumps(out,indent=2));print(json.dumps(out));raise SystemExit(1)
 Path(a.output).write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
