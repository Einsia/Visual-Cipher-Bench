"""Clue-free picture crossword model used by the pixel solver (own copy; reads only solver_lib/data).

Cells: letters or pictures. Engraved letters are fixed; every other letter cell takes one letter.
Every across / down run of 2+ cells must be a lexicon word. A picture cell holds one spoken name of the
picture (name list); each run through it writes that sound with any CMUdict spelling sharing a pronunciation
(stress ignored). Both runs through a picture use the same name; spellings may differ.
"""
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
_PRON = None
_HOMO = {}
_LEX = None


def pron():
    global _PRON
    if _PRON is None:
        p = {}
        for line in (DATA / "cmudict.dict").read_text(encoding="latin-1").splitlines():
            parts = line.split("#")[0].split()
            if not parts:
                continue
            w = re.sub(r"\(\d+\)", "", parts[0]).upper()
            if not w.isalpha():
                continue
            ph = " ".join(re.sub(r"\d", "", x) for x in parts[1:])
            p.setdefault(w, set()).add(ph)
        _PRON = p
    return _PRON


def homophones(name):
    if name in _HOMO:
        return _HOMO[name]
    p = pron()
    keys = p.get(name, set())
    _HOMO[name] = sorted({w for w, ph in p.items() if ph & keys} | {name})
    return _HOMO[name]


def lexicons():
    """(strict OCR list, broad = strict + CMUdict headwords)"""
    global _LEX
    if _LEX is None:
        strict = {w.strip().upper() for w in (DATA / "english_words.txt").read_text().split() if w.strip().isalpha()}
        broad = strict | {w for w in pron() if w.isalpha()}
        _LEX = (strict, broad)
    return _LEX


def spellings(name):
    strict = lexicons()[0]
    return sorted({sp for sp in homophones(name) if sp in strict} | {name})


def parse_grid(rows):
    grid = {}
    for r, row in enumerate(rows):
        for c, tok in enumerate(row.split()):
            if tok != ".":
                grid[(r, c)] = tok
    return grid


def slots(grid):
    out = []
    for d, (dr, dc) in (("A", (0, 1)), ("D", (1, 0))):
        for (r, c) in sorted(grid):
            if (r - dr, c - dc) in grid or (r + dr, c + dc) not in grid:
                continue
            cells = []
            rr, cc = r, c
            while (rr, cc) in grid:
                cells.append((rr, cc))
                rr, cc = rr + dr, cc + dc
            out.append({"dir": d, "cells": cells})
    return out


def slot_candidates(slot, grid, names, lex):
    cells = slot["cells"]
    pics = [(i, grid[c][1:]) for i, c in enumerate(cells) if grid[c].startswith("#")]
    nlet = len(cells) - len(pics)
    out = []
    if not pics:
        for w in lex:
            if len(w) == nlet:
                out.append((w, None, None, None, w))
        return out
    if len(pics) != 1:
        raise ValueError("a run holds more than one picture cell")
    pi, pic = pics[0]
    spells = [(nm, sp) for nm in names[pic] for sp in spellings(nm)]
    for w in lex:
        for nm, sp in spells:
            if len(w) == nlet + len(sp) and w[pi:pi + len(sp)] == sp:
                out.append((w, pic, nm, sp, w[:pi] + w[pi + len(sp):]))
    return out


class Model:
    """design = {"grid": rows, "pictures": {key: {"names": [...]}}, "circles": [[r,c],...]}; grid tokens:
    '.' block, '?' open letter cell, a letter = engraved, '#key' picture cell."""

    def __init__(self, design, lex):
        self.design = design
        self.grid = parse_grid(design["grid"])
        self.slots = slots(self.grid)
        self.names = {p: v["names"] for p, v in design["pictures"].items()}
        self.lcells = [[c for c in s["cells"] if not self.grid[c].startswith("#")] for s in self.slots]
        self.spic = [next((self.grid[c][1:] for c in s["cells"] if self.grid[c].startswith("#")), None) for s in self.slots]
        self.cands = [slot_candidates(s, self.grid, self.names, lex) for s in self.slots]

    def solve(self, engraved, limit=2):
        g = self.grid
        dom = {}
        for c, t in g.items():
            if t.startswith("#"):
                continue
            dom[c] = {t} if c in engraved else None
        pdom = {p: None for p in self.names}
        cand = []
        for si, cs in enumerate(self.cands):
            lc = self.lcells[si]
            fixed = [(k, g[c]) for k, c in enumerate(lc) if c in engraved]
            cand.append([x for x in cs if all(x[4][k] == ch for k, ch in fixed)])
        stats = {"initial_candidates": [len(c) for c in cand], "nodes": 0, "rounds": 0}
        sols = []

        def propagate(cand, dom, pdom):
            changed = True
            while changed:
                changed = False
                stats["rounds"] += 1
                for si in range(len(cand)):
                    lc = self.lcells[si]
                    p = self.spic[si]
                    new = [x for x in cand[si]
                           if all(dom[c] is None or x[4][k] in dom[c] for k, c in enumerate(lc))
                           and (p is None or pdom[p] is None or x[2] in pdom[p])]
                    if len(new) != len(cand[si]):
                        cand[si] = new
                        changed = True
                    if not new:
                        return False
                    for k, c in enumerate(lc):
                        proj = {x[4][k] for x in new}
                        if dom[c] is None or proj < dom[c]:
                            dom[c] = proj if dom[c] is None else (dom[c] & proj)
                            changed = True
                    if p is not None:
                        proj = {x[2] for x in new}
                        if pdom[p] is None or not (pdom[p] <= proj):
                            pdom[p] = proj if pdom[p] is None else (pdom[p] & proj)
                            changed = True
            return True

        def rec(cand, dom, pdom):
            stats["nodes"] += 1
            if len(sols) >= limit:
                return
            if not propagate(cand, dom, pdom):
                return
            open_ = [si for si in range(len(cand)) if len(cand[si]) > 1]
            if not open_:
                sols.append({"words": [c[0][0] for c in cand], "names": dict(pdom),
                             "letters": {c: next(iter(d)) for c, d in dom.items()}})
                return
            si = min(open_, key=lambda i: len(cand[i]))
            for x in cand[si]:
                c2 = list(cand)
                c2[si] = [x]
                rec(c2, {k: (set(v) if v is not None else None) for k, v in dom.items()},
                    {k: (set(v) if v is not None else None) for k, v in pdom.items()})
                if len(sols) >= limit:
                    return

        rec(cand, dom, pdom)
        return sols, stats

    def extract(self, letters):
        return "".join(letters[tuple(c)] for c in sorted(tuple(c) for c in self.design["circles"]))


def distinct_fills(model, engraved, limit=60):
    """Solutions deduplicated by (letters of all cells, picture names): spelling-only variants are one fill."""
    sols, st = model.solve(engraved, limit=limit)
    keys = {}
    for s in sols:
        k = (tuple(sorted(s["letters"].items())),
             tuple(sorted((p, tuple(sorted(v))) for p, v in s["names"].items())))
        keys.setdefault(k, s)
    return list(keys.values()), len(sols) >= limit, st
