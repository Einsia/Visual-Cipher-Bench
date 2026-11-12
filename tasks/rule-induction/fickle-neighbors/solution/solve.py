"""Read the puzzle PNG, infer the operator and the example-supported readout."""
from pathlib import Path
import json,sys,argparse
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'solver_lib'))
from pixels import read
from inference import infer
ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);ap.add_argument('--evidence');a=ap.parse_args()
s,details=read(Path(a.images)/'01.png');result=infer(s);answers=set(result['answers'])
if len(answers)!=1:raise ValueError('No unique word from observed conditions: '+str(sorted(answers)))
out={'answer':next(iter(answers)),'normalization':'upper_compact'};Path(a.output).write_text(json.dumps(out)+'\n');print(json.dumps(out))
if a.evidence:
 Path(a.evidence).write_text(json.dumps({'observed':s,'pixels':details,'inference':result},indent=2)+'\n')
