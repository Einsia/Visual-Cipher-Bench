"""Read the supplied PNG and compute the answer."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solver_lib.engine import evaluate, images_path  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    r = evaluate(images_path(args.images))
    out = {k: r.get(k) for k in ["valid", "unique", "solution_count", "answer", "image_hashes", "checks"]}
    out["words"] = r.get("words")
    Path(args.output).write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(json.dumps({k: r.get(k) for k in ["valid", "solution_count", "answer"]}))
    if not r["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
