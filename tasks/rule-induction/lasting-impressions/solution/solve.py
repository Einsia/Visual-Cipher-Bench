"""PNG reference solver for Lasting Impressions.

Reads only the two supplied PNGs and generic solver/font resources. Fits five
compound observations jointly with the eight capital outputs. The separate
block-letter legend supplies recognition evidence, not an operation example.
No stored rule template, specification or answer is read.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from pixels import parse
from inference import verify

def solve(images):
    data=parse(images)
    report=verify(data)
    report['image_hashes']=data['image_hashes']
    return report,data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    try:
        r,_=solve(a.images)
        out={k:r[k] for k in ('valid','answer','unique','solution_count','image_hashes')}
        out['normalization']='upper_compact'
        out['verification'] = {
            'input': 'PNG pixels only',
            'encodings': [route['name'] for route in r['routes']],
            'geometry_pairs_per_encoding': 64,
            'dictionary_used': False,
            'wall_seconds': r['wall_seconds'],
        }
    except Exception as e:
        out={'valid':False,'unique':False,'solution_count':0,'answer':None,'error':f'{type(e).__name__}: {e}'}
    Path(a.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
    sys.exit(0 if out['valid'] else 1)
