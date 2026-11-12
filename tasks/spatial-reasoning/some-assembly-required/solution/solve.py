#!/usr/bin/env python3
"""PNG-only reference solver. Read unruled mixed-grid outlines,
letters and their feet, example, target house and blanks from 01.png. Recover
face boundaries by silhouette-cover enumeration, then hinge signs and angles by closure; pack, enumerate self-symmetries and read the
unique upright wall. No design spec, partition, hinge table or answer is read.
"""
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
        rep = flatsolve.solve(str(img), log=lambda event, detail: print(event, json.dumps(detail, default=str), file=sys.stderr, flush=True))
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
