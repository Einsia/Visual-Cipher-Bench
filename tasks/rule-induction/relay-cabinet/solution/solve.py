"""Infer complete rule from PNG examples; compare only visible candidate bodies."""
from pathlib import Path
import argparse,json
from solver_lib.engine import analyze

def main():
 p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 r=analyze(a.images)
 Path(a.output).write_text(json.dumps({'answer':r['answer'],'valid':r['valid'],'unique':r['unique'],'solution_count':r['solution_count']},indent=2)+'\n')
 if not r['valid']:raise SystemExit(1)
if __name__=='__main__':main()
