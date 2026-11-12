"""Read the register and return topology from raster ink.

Coordinates locate the printed form; no solution labels or word
assignments occur here. Missing circles, broken paths, ambiguous heads and a
register inconsistent with the cards are rejected rather than silently assumed.
"""
import numpy as np
from PIL import Image


def number(crop, bank):
    def normalized(a):
        ys, xs = np.where(a < 128)
        if not len(xs):
            raise ValueError('Missing printed numeral')
        a = a[ys.min():ys.max()+1, xs.min():xs.max()+1]
        return np.asarray(Image.fromarray(a).resize((64, 40), Image.Resampling.BILINEAR))
    ink = normalized(crop)
    scores = []
    for label, template in bank:
        if label.startswith('seal_'):
            q = normalized(template[20:65, 30:130])
            scores.append((float(np.abs(ink.astype(float)-q).mean()), label))
    scores.sort()
    if scores[0][0] >= 18 or scores[1][0]-scores[0][0] < 1:
        raise ValueError(f'Ambiguous printed numeral: {scores[:2]}')
    return str(int(scores[0][1][5:]))


def line(a, p, q):
    """Verify contiguous shaft ink, allowing antialiasing at integer positions."""
    x, y = p; xx, yy = q
    n = max(abs(xx-x), abs(yy-y))+1
    samples = []
    for u, v in zip(np.linspace(x, xx, n), np.linspace(y, yy, n)):
        u, v = int(round(u)), int(round(v))
        samples.append(bool((a[v-1:v+2, u-1:u+2] < 160).any()))
    if not all(samples):
        raise ValueError(f'Broken printed connection: {p} -> {q}')


def horizontal_head(a, left, right, y):
    """Infer direction from off-axis triangular ink at either endpoint."""
    strip = a[y-11:y+12, left:right+1] < 160
    strip[8:15, :] = False
    l, r = int(strip[:, :23].sum()), int(strip[:, -23:].sum())
    if max(l, r) < 40 or abs(l-r) < 30:
        raise ValueError('Missing or ambiguous return arrowhead')
    return 1 if r > l else -1


def inspect(register, diagram, bank, seals, start):
    entries = []
    for row in range(3):
        for col in range(5):
            x, y = 100+290*col, 1590+115*row
            entries.append(number(register[y+5:y+48, x-2:x+65], bank))
            line(register, (x+75, y+47), (x+247, y+47))
    if len(set(entries)) != len(entries) or set(entries) != set(seals):
        raise ValueError('Register must provide exactly one entry per seal identity')

    centers = [(220+290*col, 1645+120*row) for row in range(3) for col in range(5)]
    for x, y in centers:
        for angle in np.linspace(0, 2*np.pi, 180, endpoint=False):
            u, v = round(x+43*np.cos(angle)), round(y+43*np.sin(angle))
            if not (diagram[v-2:v+3, u-2:u+3] < 160).any():
                raise ValueError('Incomplete return circle')
    if len(centers) != len(seals):
        raise ValueError('Return slot count differs from seal count')
    if number(diagram[1620:1670, 190:250], bank) != start:
        raise ValueError('Return start does not match identified start')
    edges = []
    for row in range(3):
        for col in range(4):
            i = 5*row+col
            x, y = centers[i]; xx, _ = centers[i+1]
            d = horizontal_head(diagram, x+51, xx-51, y)
            # Stop before the heads, while checking the entire shaft interior.
            line(diagram, (x+70, y), (xx-70, y))
            edges.append((i, i+1) if d == 1 else (i+1, i))
    for i, j in ((4, 9), (5, 10)):
        x, y = centers[i]; _, yy = centers[j]
        # Rotate the crop so the vertical arrow becomes a horizontal one.
        crop = diagram[y+49:yy-48, x-11:x+12].T < 160
        crop[8:15, :] = False
        # This short gap has no room for disjoint endpoint windows. Compare
        # the triangle's broad base with its taper, not two overlapping windows.
        upper, lower = int(crop[:, 5:10].sum()), int(crop[:, -10:-5].sum())
        if max(upper, lower) < 20 or abs(upper-lower) < 15:
            raise ValueError('Missing or ambiguous vertical return arrow')
        d = 1 if upper > lower else -1
        line(diagram, (x, y+49), (x, yy-52))
        edges.append((i, j) if d == 1 else (j, i))
    outer = [(1431, 1885), (1515, 1885), (1515, 1567),
             (110, 1567), (110, 1645), (156, 1645)]
    for p, q in zip(outer, outer[1:]):
        line(diagram, p, q)
    d = horizontal_head(diagram, 125, 169, 1645)
    edges.append((14, 0) if d == 1 else (0, 14))
    successors = {}
    for i, j in edges:
        if i in successors:
            raise ValueError('Return diagram branches')
        successors[i] = j
    walk = [0]
    while len(walk) < len(centers):
        j = successors.get(walk[-1])
        if j is None or j in walk:
            raise ValueError('Return diagram is not one covering cycle')
        walk.append(j)
    if successors.get(walk[-1]) != 0:
        raise ValueError('Return diagram is not closed')
    return {'register': entries, 'slots': len(centers), 'directed_edges': edges,
            'slot_order': walk, 'closed': True,
            'identity_basis': 'Repeated printed IDs, each with one register entry',
            'relation_basis': 'Same directed arrow notation in cards and return'}
