"""PNG-only solver: recover spatial silhouettes, folded frames and first-hit traversal.

Only solver_lib code and generic character templates are needed at runtime.
"""
import argparse
import json
from pathlib import Path
from solver_lib.engine import run


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--images',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=run(args.images)
    except (ValueError,AssertionError,StopIteration,OSError) as exc:
        error={'error':str(exc)};args.output.write_text(json.dumps(error)+'\n');print(json.dumps(error));return 2
    answer={'answer':result['answer']}
    args.output.write_text(json.dumps(answer)+'\n');print(json.dumps(answer));return 0


if __name__=='__main__':raise SystemExit(main())
