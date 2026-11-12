#!/usr/bin/env python3
"""Pixel solver: python solve.py --images DIR --output answer.json (reads only 01.png).
Parses the camera, the four nets (faces, creases, letters, 45-degree branches) and the answer
blanks from the pixels. Continuous uncreased panels are subdivided using their
measured outlines and unit lengths, without a seam table. Folds, packs, and reads
the one blank-shaped wall whose letters all stand upright."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "solver_lib"))
import flatsolve  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", help="Optional full PNG recovery and enumeration evidence")
    a = ap.parse_args()
    img = Path(a.images) / "01.png"
    try:
        rep = flatsolve.solve(str(img), log=lambda *v: print(*v, file=sys.stderr, flush=True))
    except Exception as e:  # unreadable page: reject, never guess
        Path(a.output).write_text(json.dumps({"answer": "", "error": "%s: %s" % (type(e).__name__, e)}))
        print("REJECT:", type(e).__name__, e, file=sys.stderr)
        sys.exit(1)
    ans = rep.get("answer")
    if a.report:
        Path(a.report).write_text(json.dumps(rep, indent=1, default=str))
    out = {"answer": ans or "", "normalization": "upper_compact"}
    if rep.get("error"):
        out["error"] = rep["error"]
    Path(a.output).write_text(json.dumps(out))
    print(json.dumps({k: v for k, v in rep.items() if k in ("answer", "packings", "seconds", "error")}, default=str))
    if not ans:
        sys.exit(1)


if __name__ == "__main__":
    main()
