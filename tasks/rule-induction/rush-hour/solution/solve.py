#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from engine import evaluate

def main():
 p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:
  report=evaluate(a.images);out={'answer':report['answer']};code=0
 except (ValueError,AssertionError,OSError) as e:out={'answer':None,'error':str(e)};code=1
 Path(a.output).write_text(json.dumps(out,indent=2)+'\n');return code
if __name__=='__main__':sys.exit(main())
