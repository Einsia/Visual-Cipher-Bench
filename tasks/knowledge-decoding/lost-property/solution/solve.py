#!/usr/bin/env python3
"""Offline reference solver for the diagram with implicit lexical calibration.

Puzzle-specific input consists only of PNG pixels. solver_lib recovers arrow
order from a printed lexical pair and extraction from spatial containment;
no completed extraction example or expected answer is required.
"""
import argparse
import json
from pathlib import Path
import sys

# All support assets live beside this file.
sys.dont_write_bytecode=True
from solver_lib.engine import solve_directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--diagnostics',type=Path,help='Optional pixel-derived recognition trace')
    args=parser.parse_args()
    status=0
    try:
        answer,trace=solve_directory(args.images)
        payload={'answer':answer}
        if args.diagnostics:
            args.diagnostics.parent.mkdir(parents=True,exist_ok=True)
            args.diagnostics.write_text(json.dumps(trace,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except Exception as error:
        payload={'error':f'{type(error).__name__}: {error}'}
        status=1
    encoded=json.dumps(payload,ensure_ascii=False)
    try:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(encoded+'\n',encoding='utf-8')
    except Exception as error:
        encoded=json.dumps({'error':f'Cannot write output: {error}'},ensure_ascii=False)
        status=1
    print(encoded,flush=True)
    return status


if __name__=='__main__':
    raise SystemExit(main())
