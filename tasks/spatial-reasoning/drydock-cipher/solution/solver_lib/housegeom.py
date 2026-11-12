"""Geometry helpers for the flat-pack house (no I/O, numpy only).

Doubled coordinates: unit cell c occupies [2c, 2c+2]^3. A wedge kind [a, b] keeps the points p
(relative to the cell centre) with p.a <= p.b. Faces are returned counter-clockwise seen from outside.
"""
import itertools
import math
import collections
import numpy as np

DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def V(x):
    return np.array(x, dtype=float)


def cell_polys(c, kind):
    ctr = V(c) * 2 + 1
    out = []
    corners = [tuple(int(x) for x in V(c) * 2 + V(o) * 2) for o in itertools.product([0, 1], repeat=3)]
    for n in DIRS:
        fc = [p for p in corners if np.dot(V(p) - ctr, n) == 1]
        if kind is not None:
            a, b = V(kind[0]), V(kind[1])
            keep = [p for p in fc if np.dot(V(p) - ctr, a) <= np.dot(V(p) - ctr, b)]
            if len(keep) < 3:
                continue
            if len(keep) == 3:
                out.append((keep, n, "tri"))
                continue
        out.append((fc, n, "sq"))
    if kind is not None:
        a, b = V(kind[0]), V(kind[1])
        sl = [p for p in corners if np.dot(V(p) - ctr, a) == np.dot(V(p) - ctr, b)]
        out.append((sl, tuple((a - b) / math.sqrt(2)), "slope"))
    res = []
    for vs, n, t in out:
        n = V(n)
        cen = np.mean([V(p) for p in vs], axis=0)
        u = V(vs[0]) - cen
        u /= np.linalg.norm(u)
        w = np.cross(n, u)
        vs = sorted(vs, key=lambda p: math.atan2(np.dot(V(p) - cen, w), np.dot(V(p) - cen, u)))
        res.append((tuple(vs), tuple(float(x) for x in np.round(n, 9)), t))
    return res


def surface(cells):
    allp = []
    for c, k in cells.items():
        allp += cell_polys(c, k)
    key = collections.Counter(frozenset(p[0]) for p in allp)
    return [p for p in allp if key[frozenset(p[0])] == 1]


class View:
    """Parallel axonometric view; `toward` points from the object to the viewer."""

    def __init__(self, toward):
        v = V(toward)
        self.v = v / np.linalg.norm(v)
        up = V((0, 0, 1))
        r = np.cross(up, self.v)
        self.r = r / np.linalg.norm(r)
        self.s = np.cross(self.v, self.r)

    def xy(self, p):
        p = V(p)
        return float(np.dot(p, self.r)), float(np.dot(p, self.s))

    def visible_face(self, normal):
        return float(np.dot(V(normal), self.v)) > 1e-9


def feature_edges(polys):
    """Edges between non-coplanar faces (or boundary); returns list of (p, q, [face ids])."""
    E = collections.defaultdict(list)
    for i, (vs, n, t) in enumerate(polys):
        for m in range(len(vs)):
            E[frozenset((vs[m], vs[(m + 1) % len(vs)]))].append(i)
    feats, seams = [], []
    for e, fs in E.items():
        p, q = tuple(e)
        if len(fs) == 2 and np.allclose(polys[fs[0]][1], polys[fs[1]][1]):
            seams.append((p, q, fs))
        else:
            feats.append((p, q, fs))
    return feats, seams


def occluded(point, polys, view, eps=1e-6):
    """True if the ray from point toward the viewer hits any face (strictly in front)."""
    d = view.v
    x = V(point)
    for vs, n, t in polys:
        P = [V(p) for p in vs]
        for m in range(1, len(P) - 1):
            a, b, c = P[0], P[m], P[m + 1]
            e1, e2 = b - a, c - a
            h = np.cross(d, e2)
            det = np.dot(e1, h)
            if abs(det) < 1e-12:
                continue
            s = x - a
            u = np.dot(s, h) / det
            if u < -1e-9 or u > 1 + 1e-9:
                continue
            q = np.cross(s, e1)
            w = np.dot(d, q) / det
            if w < -1e-9 or u + w > 1 + 1e-9:
                continue
            tt = np.dot(e2, q) / det
            if tt > eps:
                return True
    return False


def split_visibility(p, q, polys, view, samples=24):
    """Split segment pq into runs of (visible?, t0, t1)."""
    p, q = V(p), V(q)
    flags = []
    for k in range(samples):
        t = (k + 0.5) / samples
        x = p + (q - p) * t
        # nudge toward the viewer a hair so the edge is not hidden by its own faces
        flags.append(not occluded(x + view.v * 1e-4, polys, view))
    runs = []
    start = 0
    for k in range(1, samples + 1):
        if k == samples or flags[k] != flags[start]:
            runs.append((flags[start], start / samples, k / samples))
            start = k
    return runs
