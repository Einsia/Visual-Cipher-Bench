"""Extract complete words from all returning trips; no expected word lengths or count.

Only pixel-recovered letters, pixel-recovered optional blanks, and a generic English
word/phrase lexicon are used.
"""
import itertools
from . import words


def extract(target, trips, printed_blanks):
    strings = ["".join(target["signs"][rc]["letter"] for rc in path) for _, path in sorted(trips.items())]
    result = {"trips": strings, "trip_cells": [[list(rc) for rc in path] for _, path in sorted(trips.items())],
              "printed_blanks": list(printed_blanks), "derived_word_lengths": [len(s) for s in strings]}
    if not strings:
        return dict(result, status="no_closed_trip")
    if printed_blanks and sorted(map(len, strings)) != sorted(printed_blanks):
        return dict(result, status="blank_mismatch")
    orders = []
    for perm in itertools.permutations(strings):
        if printed_blanks and list(map(len, perm)) != list(printed_blanks):
            continue
        valid_words = all(words.is_word(s) for s in perm)
        valid_phrase = len(perm) == 2 and words.is_phrase(*perm)
        orders.append((perm, valid_words, valid_phrase))
    result["orders"] = [(list(p), w, ph) for p, w, ph in orders]
    good = {p for p, w, ph in orders if w and (ph or len(strings) == 1)}
    if len(good) != 1:
        return dict(result, status="order_ambiguous" if good else "no_word_order")
    chosen = next(iter(good))
    return dict(result, status="ok", answer="".join(chosen), words=list(chosen))
