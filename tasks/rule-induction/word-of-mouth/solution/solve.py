import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from pixels import read
from reason import infer

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 try:
  s=read(a.images);r=infer(s,ablations=False)
  if not r['unique']:raise ValueError('No unique prediction: '+str(r['predictions']))
  result={'answer':r['answer'],'normalization':'upper_compact'};code=0
 except Exception as e:result={'valid':False,'error':str(e)};code=1
 Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return code
if __name__=='__main__':raise SystemExit(main())
