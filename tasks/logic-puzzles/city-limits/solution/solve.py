import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from audit import verify

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    report=verify(args.images)
    result={k:report[k] for k in ('valid','unique','solution_count','answer')}
    result['input_source']='PNG pixels only; infer address, solve partition, allocate unsegmented letters, read loop'
    result['image_hashes']=report.get('image_hashes',{})
    if not report['valid']:result['checks']=report['checks']
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    sys.exit(0 if report['valid'] else 1)
