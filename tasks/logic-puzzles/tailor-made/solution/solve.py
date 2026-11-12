"""PNG-only oracle: infer areas and state transfers, trace card connections, then exhaustively solve."""
import argparse
import json
from pathlib import Path
from solver_lib.recognize import parse
from solver_lib.search import exhaustive


def run(images,workers=8):
    data=parse(Path(images)/'01.png')
    result=exhaustive(data['nums_a'],data['refs_a'],data['nums_b'],data['refs_b'],
                      [[c['a'],c['b']] for c in data['cards']],workers=workers)
    result['answer']=(''.join(data['cards'][i]['letter'] for i in result['models'][0]['schedule']) if result['unique'] else None)
    result['valid']=result['unique']
    result['pixel_data']=data
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True)
    p.add_argument('--workers',type=int,default=8);a=p.parse_args()
    try:result=run(a.images,a.workers)
    except Exception as e:result={'valid':False,'answer':None,'error':str(e)}
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    if not result['valid']:raise SystemExit(1)


if __name__=='__main__':main()
