"""PNG-only reference solver: glyphs, objects and links precede word-state search.

The incomplete example is solved jointly, including all unprinted words and cuts.
Only the puzzle image and the bundled lexicon/templates are read.
"""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).parent/'solver_lib'))
from pixels import Parser
from reasoning import compute

def run(images):
 files=sorted(Path(images).glob('*.png'))
 if len(files)!=1:raise ValueError('Expected one public page')
 p=Parser(files[0]);data=p.read();proof=compute(data);answers=proof['result']['answers']
 return data,proof,answers
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 try:
  data,proof,answers=run(a.images)
  out={'answer':answers[0].upper() if len(answers)==1 else None,'unique':len(answers)==1,'solution_count':len(answers),'candidates':answers}
 except Exception as e:out={'answer':None,'unique':False,'solution_count':0,'error':str(e)}
 Path(a.output).write_text(json.dumps(out,indent=2));print(json.dumps(out))
 sys.exit(0 if out['unique'] else 1)
