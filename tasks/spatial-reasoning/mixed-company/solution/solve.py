#!/usr/bin/env python3
"""Read only supplied PNG pixels and write the inferred puzzle answer."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    status = 0
    try:
        from solver_lib.pipeline import solve_directory
        result = {'answer': solve_directory(args.images, Path(args.output).parent / (Path(args.output).stem + '_evidence'))}
    except Exception as exc:
        result = {'error': f'{type(exc).__name__}: {exc}'}
        status = 1
    encoded = json.dumps(result, ensure_ascii=False)
    try:
        Path(args.output).write_text(encoded + '\n', encoding='utf-8')
    except Exception as exc:
        encoded = json.dumps({'error': f'Cannot write output: {exc}'})
        status = 1
    print(encoded, flush=True)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
