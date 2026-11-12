#!/usr/bin/env python3
"""Offline PNG-only solver for card-fit, unordered spelling/sound edits.
Picture assignments come from measured frames and the lexical constraints.
No answer constant or fixed coordinate table is used.
"""
import argparse
import json
from pathlib import Path
import sys

# Prevent bytecode writes when the complete /solution directory is read-only.
sys.dont_write_bytecode = True
from solver_lib.vision import read_page
from solver_lib.reasoning import solve


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    status=0
    try:
        pages=sorted(p for p in args.images.iterdir() if p.is_file() and p.suffix.lower()=='.png')
        if len(pages)!=1:
            raise ValueError(f'Expected one PNG page, found {len(pages)}')
        examples,rows,vision=read_page(pages[0])
        answer,reasoning=solve(examples,rows)
        result={'answer':answer}
        # An auditable transcript goes to stderr; output JSON stays minimal.
        print(json.dumps({'vision':vision,'reasoning':reasoning},ensure_ascii=False),file=sys.stderr)
    except Exception as exc:
        result={'error':f'{type(exc).__name__}: {exc}'}
        status=1
    encoded=json.dumps(result,ensure_ascii=False)
    try:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(encoded+'\n',encoding='utf-8')
    except Exception as exc:
        print(json.dumps({'error':f'Cannot write output: {exc}'},ensure_ascii=False))
        return 1
    print(encoded)
    return status


if __name__=='__main__':
    sys.exit(main())
