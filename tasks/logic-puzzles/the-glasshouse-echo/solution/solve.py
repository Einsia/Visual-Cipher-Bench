#!/usr/bin/env python3
"""Solve the puzzle from its PNG images."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from solver_lib.vision import read_problem
from solver_lib.search import solve


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    status=0
    try:
        data=read_problem(args.images)
        print(f'Read {data["n"]} inventory tokens, {len(data["rows"])} coupons, count {data["count"]} from pixels',file=sys.stderr,flush=True)
        result={'answer':solve(data)}
    except Exception as exc:
        status=1;result={'error':f'{type(exc).__name__}: {exc}'}
    text=json.dumps(result,ensure_ascii=False)
    try:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+'\n',encoding='utf-8')
    except OSError as exc:
        text=json.dumps({'error':f'Cannot write output: {exc}'},ensure_ascii=False)
        status=1
    print(text,flush=True)
    return status


if __name__=='__main__':
    raise SystemExit(main())
