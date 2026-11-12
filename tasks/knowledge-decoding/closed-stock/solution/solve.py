#!/usr/bin/env python3
"""Reference solver. Inputs: PNG pixels, class templates, English lexical knowledge.
The register and closed return topology are verified from pixels.
"""
import argparse,json,time,os,tempfile
from pathlib import Path
from solver_lib.pixels import read
from solver_lib.search import solve

def atomic_write(path,content):
    fd,tmp=tempfile.mkstemp(prefix=".stock-",dir=path.parent)
    os.fchmod(fd,0o644)
    with os.fdopen(fd,"w") as f:f.write(content)
    os.replace(tmp,path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    t=time.perf_counter();problem,trace=read(args.images)
    if not problem['visual_structure']['closed']:
        raise RuntimeError('PNG does not establish a closed return')
    results,stats=solve(problem)
    answers={''.join(f'{int(v):02}' for v in r['route']) for r in results}
    if len(answers)!=1:raise RuntimeError(f'Expected a unique pixel-derived answer; got {len(answers)}')
    answer=answers.pop();out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    atomic_write(out,json.dumps({'answer':answer},indent=2)+'\n' if out.suffix=='.json' else answer+'\n')
    audit={'input_files':[p.name for p in sorted(Path(args.images).glob('*.png'))],'problem_from_pixels':problem,'recognition':trace,'results':results,'search':stats,'total_seconds':time.perf_counter()-t}
    atomic_write(out.with_name('pixel_trace.json'),json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'answer':answer,'seconds':audit['total_seconds'],'cycles':len(results)}))
if __name__=='__main__':main()
