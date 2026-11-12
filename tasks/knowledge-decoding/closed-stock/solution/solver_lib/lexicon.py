"""Language knowledge, independent of seal IDs or page positions."""
from pathlib import Path
from collections import defaultdict
import json
ROOT=Path(__file__).resolve().parent

def load():
    pairs={tuple(p) for p in json.loads((ROOT/'english_pairs.json').read_text())}
    pairs.update(tuple(p['pair']) for p in json.loads((ROOT/'supplement.json').read_text()))
    forward=defaultdict(set);reverse=defaultdict(set)
    for a,b in pairs:forward[a].add(b);reverse[b].add(a)
    return pairs,forward,reverse,set(forward)|set(reverse)
