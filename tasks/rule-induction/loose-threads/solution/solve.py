import argparse,json
from pathlib import Path
from solver_lib.pixels import read_images
from solver_lib.reason import solve

def main():
 p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:
  data=read_images(a.images);result=solve(data);out={'answer':result['answer']}
 except Exception as e:
  Path(a.output).write_text(json.dumps({'error':str(e),'valid':False}));raise SystemExit(1)
 Path(a.output).write_text(json.dumps(out,indent=2))
if __name__=='__main__':main()
