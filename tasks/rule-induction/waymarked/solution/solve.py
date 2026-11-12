#!/usr/bin/env python3
"""Pixel solver for the Waymarked page.

Reads the PNG, recovers every sign (direction, chevrons, ring/strike mark or letter) from pixels, induces the
reading rule from the three marked example boards over a generic rule family, applies the surviving rule(s)
to the lettered board, reads each closed trip's letters from its own start, derives the word count and lengths from the trips themselves, and orders the words as an English phrase.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solver_lib import rules, vision, extract  # noqa: E402


def solve_image(path):
    page = vision.read_page(path)
    ex = [b for b in page["boards"] if b["kind"] == "example"]
    tgt = [b for b in page["boards"] if b["kind"] == "target"][0]
    fitting = rules.induce(ex)
    if not fitting:
        return {"status": "no_rule", "page": page}
    outcomes = {}
    for r in fitting:
        closed = rules.apply(r, tgt)
        key = tuple((rc, tuple(p)) for rc, p in sorted(closed.items()))
        outcomes.setdefault(key, []).append(r)
    if len(outcomes) != 1:
        return {"status": "ambiguous_rule", "fitting": [rules.describe(r) for r in fitting],
                "outcomes": len(outcomes), "page": page}
    key = next(iter(outcomes))
    extraction = extract.extract(tgt, dict(key), page["blanks"])
    return dict(extraction, fitting=[rules.describe(r) for r in fitting], page=page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    img = Path(a.images) / "01.png"
    try:
        res = solve_image(img)
    except vision.ReadError as e:
        res = {"status": "read_error", "error": str(e)}
    res.pop("page", None)
    out = {"answer": res.get("answer"), "status": res["status"],
           "detail": {k: v for k, v in res.items() if k not in ("answer", "status")}}
    Path(a.output).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"answer": out["answer"], "status": out["status"]}))
    return 0 if out["answer"] else 1


if __name__ == "__main__":
    sys.exit(main())
