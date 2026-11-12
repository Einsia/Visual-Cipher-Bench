"""Induce the sign-reading rule from the ringed/struck example boards and apply it.

Rule family (none of it is specific to one page):
  reading   'absolute' (move as drawn) or 'relative' with a turn map: drawn U/R/D/L -> turn 0..3 quarter
            turns clockwise from the current heading; the first sign is read relative to a start heading.
  start     start heading U/R/D/L (relative readings only).
  jump      'exact' n cells; 'nth' = the n-th sign in that direction; 'first_within' = first sign within n;
            'slide' = n cells, then keep sliding over empty cells to the next sign.
  criterion 'land_start' (a trip that lands on its own start), 'same_heading' (lands on start moving as at
            the first move).
A trip ends on an empty cell, off the board, or when a (cell, heading) state repeats.
"""
import itertools

ORDER = ["U", "R", "D", "L"]
DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


def all_rules():
    rules = []
    for jump in ("exact", "nth", "first_within", "slide"):
        for crit in ("land_start", "same_heading"):
            rules.append(("absolute", None, None, jump, crit))
            for tm in itertools.product(range(4), repeat=4):
                for start in ORDER:
                    rules.append(("relative", tm, start, jump, crit))
    return rules


def _step(pos, size, cell, d, n, jump):
    dr, dc = DIRS[d]
    r, c = cell
    if jump == "exact":
        t = (r + dr * n, c + dc * n)
        return t if t in pos else None
    if jump == "nth":
        k = 0
        rr, cc = r + dr, c + dc
        while 0 <= rr < size and 0 <= cc < size:
            if (rr, cc) in pos:
                k += 1
                if k == n:
                    return (rr, cc)
            rr += dr; cc += dc
        return None
    if jump == "first_within":
        for k in range(1, n + 1):
            t = (r + dr * k, c + dc * k)
            if t in pos:
                return t
        return None
    if jump == "slide":
        k = n
        while 0 <= r + dr * k < size and 0 <= c + dc * k < size:
            t = (r + dr * k, c + dc * k)
            if t in pos:
                return t
            k += 1
        return None
    raise ValueError(jump)


def trip(pos, size, start, rule):
    """pos: {(r,c): (dir, n)}. Returns (closed, path_of_cells)."""
    reading, tm, h0, jump, crit = rule
    cur, head, path, seen, first_move = start, h0, [start], set(), None
    while True:
        d, n = pos[cur]
        if reading == "absolute":
            new = d
        else:
            new = ORDER[(ORDER.index(head) + tm[ORDER.index(d)]) % 4]
        if (cur, new) in seen:
            return False, path
        seen.add((cur, new))
        if first_move is None:
            first_move = new
        nxt = _step(pos, size, cur, new, n, jump)
        head = new
        if nxt is None:
            return False, path
        if nxt == start:
            if crit == "land_start" or head == first_move:
                return True, path
        cur = nxt
        path.append(cur)


def board_positions(board):
    return {rc: (s["dir"], s["n"]) for rc, s in board["signs"].items()}


def fits(rule, ex_boards):
    for b in ex_boards:
        pos = board_positions(b)
        for rc, s in b["signs"].items():
            closed, _ = trip(pos, b["size"], rc, rule)
            if closed != (s["mark"] == "ringed"):
                return False
    return True


def induce(ex_boards):
    return [r for r in all_rules() if fits(r, ex_boards)]


def apply(rule, board):
    pos = board_positions(board)
    out = {}
    for rc in sorted(pos):
        closed, path = trip(pos, board["size"], rc, rule)
        if closed:
            out[rc] = path
    return out


def describe(rule):
    reading, tm, h0, jump, crit = rule
    if reading == "absolute":
        return f"absolute/{jump}/{crit}"
    names = ["straight", "right", "back", "left"]
    m = ", ".join(f"{d}={names[t]}" for d, t in zip(ORDER, tm))
    return f"relative[{m}] start={h0} jump={jump} crit={crit}"
