"""Echo Vault: infer calibration addresses from PNGs, then certify uniqueness."""
import argparse
import json
from pathlib import Path
from solver_lib.audit import run


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--images',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--seconds',type=float,default=1000,
                        help='Limit per disjoint partition; timeout never certifies uniqueness')
    args=parser.parse_args()
    result=run(args.images,args.seconds)
    output={k:result[k] for k in ('answer','valid','unique','solution_count','status',
                                 'checks','total_seconds')}
    Path(args.output).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ('answer','unique','status','total_seconds')}),flush=True)
    return 0 if result['valid'] else 2


if __name__=='__main__':
    raise SystemExit(main())
