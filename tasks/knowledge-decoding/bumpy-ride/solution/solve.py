#!/usr/bin/env python3
"""Solve the PNGs with solver_lib only, including operation inference.

The pictorial example constrains extraction; the main image constrains wordplay.
The reader also measures comparative illumination and shared-scene regions.
"""
import argparse
import json
from pathlib import Path

from solver_lib.pixel_reader import solve_images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        result = solve_images(args.images)
        output = {key: result[key] for key in
                  ('valid', 'unique', 'solution_count', 'answer')}
    except Exception as error:
        output = {'valid': False, 'unique': False, 'solution_count': 0,
                  'answer': None, 'error': str(error)}
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output))
    return 0 if output['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
