"""Geometry core for the flat-pack house puzzle.

World: unit cells are whole cubes or half-cube wedges (a cube cut on a face-diagonal plane).
Coordinates are doubled so every vertex is an integer: cell c occupies [2c, 2c+2]^3.
A wedge kind (a, b) keeps the points p (relative to the cell centre) with p.a <= p.b;
its sloped face has outward normal (a - b)/sqrt(2).

Packing uses 24 sub-tetrahedra per cell, (f, d): f = face normal, d = an in-face axis.
A cube is all 24, a wedge exactly 12, so packing is an exact cover over (cell, f, d).
"""
import itertools
import math
import collections
import numpy as np

DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def _rots():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product([1, -1], repeat=3):
            M = np.zeros((3, 3), dtype=int)
            for i in range(3):
                M[i, perm[i]] = signs[i]
            if round(np.linalg.det(M)) == 1:
                out.append(M)
    return out


ROTS = _rots()
assert len(ROTS) == 24
MIRROR = np.diag([-1, 1, 1])


def V(x):
    return np.array(x, dtype=float)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


# --------------------------------------------------------------------------- sub-tetrahedra
SUB = [(f, d) for f in DIRS for d in DIRS if sum(x * y for x, y in zip(f, d)) == 0]
assert len(SUB) == 24


def tet_vertices(f, d):
    e = cross(f, d)
    f, d, e = V(f), V(d), V(e)
    return [np.zeros(3), f, f + d + e, f + d - e]


def kept_subs(kind):
    if kind is None:
        return frozenset(SUB)
    a, b = V(kind[0]), V(kind[1])
    out = []
    for s in SUB:
        vals = [np.dot(p, a) - np.dot(p, b) for p in tet_vertices(*s)]
        assert all(v <= 1e-9 for v in vals) or all(v >= -1e-9 for v in vals), "tet straddles cut"
        if all(v <= 1e-9 for v in vals) and any(v < -1e-9 for v in vals):
            out.append(s)
    assert len(out) == 12
    return frozenset(out)


def solid_of(cells):
    """cells: dict cell -> kind (None cube | (a,b) wedge). Returns frozenset of (cell, f, d)."""
    return frozenset((tuple(c), f, d) for c, k in cells.items() for (f, d) in kept_subs(k))


def _T(v, M):
    return tuple(int(x) for x in M @ np.array(v))


def transform_solid(solid, M):
    """Rotate (or reflect) a sub-tet solid; cell index c maps through its centre c+1/2."""
    out = []
    for (c, f, d) in solid:
        cc = M @ (np.array(c) * 2 + 1)  # doubled centre
        out.append((tuple(int(x) for x in cc), _T(f, M), _T(d, M)))
    # re-index: doubled centres are odd; cell = (centre-1)/2 after translation to min
    m = [min(x[0][i] for x in out) for i in range(3)]
    return frozenset((tuple((x[0][i] - m[i]) // 2 for i in range(3)), x[1], x[2]) for x in out)


def placements(solid, target, mirror=False):
    tcells = {x[0] for x in target}
    out = {}
    for M in ROTS:
        MM = M @ MIRROR if mirror else M
        r = transform_solid(solid, MM)
        rc = {x[0] for x in r}
        c0 = min(rc)
        for t in tcells:
            off = tuple(t[i] - c0[i] for i in range(3))
            p = frozenset((tuple(x[0][i] + off[i] for i in range(3)), x[1], x[2]) for x in r)
            if p <= target and p not in out:
                out[p] = (MM, off)
    return out


def exact_cover(pieces, target, mirror=False, limit=1000):
    """Algorithm X over (cell,f,d) items plus one item per piece. Returns (solutions, stats)."""
    pl = [placements(p, target, mirror) for p in pieces]
    rows = []
    for i, P in enumerate(pl):
        for s, info in P.items():
            rows.append((i, s, info))
    cover = collections.defaultdict(list)
    for r, (i, s, info) in enumerate(rows):
        cover[("piece", i)].append(r)
        for e in s:
            cover[e].append(r)
    items = set(target) | {("piece", i) for i in range(len(pieces))}
    sols, nodes = [], [0]
    active = set(range(len(rows)))

    def rec(remaining, chosen, active):
        nodes[0] += 1
        if not remaining:
            sols.append(list(chosen))
            return
        best, bestn = None, None
        for it in remaining:
            n = sum(1 for r in cover[it] if r in active)
            if bestn is None or n < bestn:
                best, bestn = it, n
                if n <= 1:
                    break
        if bestn == 0:
            return
        for r in [r for r in cover[best] if r in active]:
            i, s, info = rows[r]
            cols = set(s) | {("piece", i)}
            removed = set()
            for c in cols:
                for r2 in cover[c]:
                    if r2 in active:
                        removed.add(r2)
            rec(remaining - cols, chosen + [r], active - removed)
            if len(sols) >= limit:
                return

    rec(frozenset(items), [], frozenset(active))
    return [[rows[r] for r in sol] for sol in sols], {"placements": [len(P) for P in pl], "nodes": nodes[0]}


# --------------------------------------------------------------------------- surfaces
def cell_polys(c, kind):
    """Unit faces of one cell: list of (vertices CCW from outside, outward normal, type)."""
    ctr = V(c) * 2 + 1
    out = []
    corners = [tuple(int(x) for x in V(c) * 2 + V(o) * 2) for o in itertools.product([0, 1], repeat=3)]

    def rel(p):
        return V(p) - ctr

    for n in DIRS:
        fc = [p for p in corners if np.dot(rel(p), n) == 1]
        if kind is not None:
            a, b = V(kind[0]), V(kind[1])
            keep = [p for p in fc if np.dot(rel(p), a) <= np.dot(rel(p), b)]
            if len(keep) < 3:
                continue
            if len(keep) == 3:
                out.append((keep, n, "tri"))
                continue
        out.append((fc, n, "sq"))
    if kind is not None:
        a, b = V(kind[0]), V(kind[1])
        sl = [p for p in corners if np.dot(rel(p), a) == np.dot(rel(p), b)]
        nn = (a - b) / math.sqrt(2)
        out.append((sl, tuple(nn), "slope"))
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
        allp += [(p[0], p[1], p[2], tuple(c)) for p in cell_polys(c, k)]
    key = collections.Counter(frozenset(p[0]) for p in allp)
    return [p for p in allp if key[frozenset(p[0])] == 1]


def edges_of(vs):
    return [frozenset((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]


def adjacency(polys):
    E = collections.defaultdict(list)
    for i, p in enumerate(polys):
        for e in edges_of(p[0]):
            E[e].append(i)
    return E


def is_manifold(polys):
    return all(len(v) == 2 for v in adjacency(polys).values())


def dihedral(p, q):
    """Interior dihedral angle in degrees between faces p, q sharing an edge."""
    n1, n2 = V(p[1]), V(q[1])
    ang = math.degrees(math.acos(max(-1, min(1, np.dot(n1, n2)))))
    if abs(ang) < 1e-6:
        return 180
    cq = np.mean([V(x) for x in q[0]], axis=0)
    cp = np.mean([V(x) for x in p[0]], axis=0)
    convex = np.dot(cq - cp, n1) < -1e-9
    return int(round(180 - ang if convex else 180 + ang))


def connected_cells(cells):
    """Cells joined by a shared full polygon (face contact, not edge contact)."""
    cl = list(cells)
    polys = {c: {frozenset(p[0]) for p in cell_polys(c, cells[c])} for c in cl}
    seen, stack = {cl[0]}, [cl[0]]
    while stack:
        c = stack.pop()
        for d in DIRS:
            n = tuple(c[i] + d[i] for i in range(3))
            if n in cells and n not in seen and polys[c] & polys[n]:
                seen.add(n)
                stack.append(n)
    return len(seen) == len(cl)


# --------------------------------------------------------------------------- 2D helpers
def poly_area(P):
    return 0.5 * sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))


def clip(subject, clipper):
    """Sutherland-Hodgman; both convex CCW."""
    out = list(subject)
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12

        def inter(p, q):
            x1, y1, x2, y2 = a[0], a[1], b[0], b[1]
            x3, y3, x4, y4 = p[0], p[1], q[0], q[1]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(q):
                if not inside(p):
                    out.append(inter(p, q))
                out.append(q)
            elif inside(p):
                out.append(inter(p, q))
    return out


def overlap_area(P, Q):
    c = clip(P, Q)
    return abs(poly_area(c)) if len(c) >= 3 else 0.0


def seg_overlap(a, b, c, d, eps=1e-6):
    """Length of collinear overlap of segments ab and cd."""
    a, b, c, d = map(np.array, (a, b, c, d))
    u = b - a
    L = np.linalg.norm(u)
    u = u / L
    for p in (c, d):
        w = p - a
        if abs(u[0] * w[1] - u[1] * w[0]) > eps:
            return 0.0
    t1, t2 = sorted([np.dot(c - a, u), np.dot(d - a, u)])
    return max(0.0, min(L, t2) - max(0.0, t1))


# --------------------------------------------------------------------------- folding a drawn net
def rot_about(axis_p, axis_d, ang):
    k = np.array(axis_d, float)
    k /= np.linalg.norm(k)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    R = np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K
    p = np.array(axis_p, float)
    return R, p - R @ p


def fold_net(faces, links, options, max_solutions=64, node_limit=2_000_000, lattice=True):
    """Fold a net drawn printed-side up.

    faces: list of 2D polygons (CCW, net units).  links: list of (i, j, (A, B)) tree edges where
    A, B are the shared 2D endpoints; parent i must precede child j in a BFS order produced here.
    options[k]: list of interior dihedral angles allowed for link k (180 = flat).
    Returns (list of solutions, nodes) where a solution maps face -> list of 3D vertices.
    Prunes: a 3D edge used by >2 faces, two face centroids coinciding, and (lattice=True) any
    vertex off the unit lattice (blocks are whole cubes and half-cube wedges on a unit grid).
    A solution is kept only if the surface is closed (every edge used exactly twice) and has
    positive volume with the printed side outward.
    """
    n = len(faces)
    child_set = {j for (_, j, _) in links}
    root = [i for i in range(n) if i not in child_set][0]
    # A net may be drawn at any position and turn on the page, and parts of it may lie diagonally.
    # Move the net rigidly in its plane so that the root face has a vertex at the
    # origin and an edge along +x; folding is unchanged by this, and the lattice test below then
    # applies to every correctly folded vertex.
    o = np.array(faces[root][0], float)
    d = np.array(faces[root][1], float) - o
    c_, s_ = d / np.linalg.norm(d)
    Rn = np.array([[c_, s_], [-s_, c_]])
    tr2 = lambda p: tuple(float(v) for v in Rn @ (np.array(p, float) - o))
    faces = [[tr2(p) for p in f] for f in faces]
    links = [(i, j, (tr2(e[0]), tr2(e[1]))) for (i, j, e) in links]
    children = collections.defaultdict(list)
    for k, (i, j, e) in enumerate(links):
        children[i].append((j, e, k))
    order = []
    q = [root]
    while q:
        i = q.pop(0)
        for (j, e, k) in children[i]:
            order.append((i, j, e, k))
            q.append(j)
    assert len(order) == n - 1

    def key(p):
        return tuple(round(x, 4) for x in p)

    sols, nodes = [], [0]
    maps = {root: (np.eye(3), np.zeros(3))}
    pts3 = {root: [np.array([x, y, 0.0]) for x, y in faces[root]]}
    segs = collections.Counter()
    cents = [key(np.mean(pts3[root], axis=0))]
    for m in range(len(pts3[root])):
        segs[frozenset((key(pts3[root][m]), key(pts3[root][(m + 1) % len(pts3[root])])))] += 1

    def rec(t):
        nodes[0] += 1
        if nodes[0] > node_limit or len(sols) >= max_solutions:
            return
        if t == len(order):
            if all(v == 2 for v in segs.values()):
                vol = 0.0
                for j in range(n):
                    P = pts3[j]
                    for m in range(1, len(P) - 1):
                        vol += np.dot(P[0], np.cross(P[m], P[m + 1])) / 6
                if vol > 1e-6:
                    sols.append({j: [tuple(round(x, 6) for x in p) for p in pts3[j]] for j in range(n)})
            return
        i, j, (A, B), k = order[t]
        Ri, ti = maps[i]
        A3, B3 = np.array([A[0], A[1], 0.0]), np.array([B[0], B[1], 0.0])
        # child lies on the left/right of the directed edge in 2D; folding "down" (away from viewer)
        cj = np.mean([np.array([x, y, 0.0]) for x, y in faces[j]], axis=0)
        side = np.sign(np.cross(B3 - A3, cj - A3)[2])
        for ang_deg in options[k]:
            # rotate the child about edge AB so that it turns away from the viewer by (180 - interior)
            turn = math.radians(180 - ang_deg)
            Rl, tl = rot_about(A3, (B3 - A3) * side, -turn)
            R, tr = Ri @ Rl, Ri @ tl + ti
            P = [R @ np.array([x, y, 0.0]) + tr for x, y in faces[j]]
            if lattice and any(abs(v - round(v)) > 1e-4 for p in P for v in p):
                continue
            c = key(np.mean(P, axis=0))
            if c in cents:
                continue
            new = [frozenset((key(P[m]), key(P[(m + 1) % len(P)]))) for m in range(len(P))]
            if any(segs[s] >= 2 for s in new):
                continue
            for s in new:
                segs[s] += 1
            maps[j] = (R, tr)
            pts3[j] = P
            cents.append(c)
            rec(t + 1)
            cents.pop()
            del maps[j]
            del pts3[j]
            for s in new:
                segs[s] -= 1
                if segs[s] == 0:
                    del segs[s]

    rec(0)
    return sols, nodes[0]


def solid_from_faces(face_pts):
    """Recover the cell decomposition (cube / wedge per cell) of a closed folded piece.

    face_pts: list of 3D polygons (any rigid position, axis-aligned up to rotation already applied).
    Returns dict cell -> kind, after snapping to the doubled integer lattice; None if impossible.
    Works by point-in-polyhedron tests at sub-tetrahedron centroids.
    """
    P = [[np.array(p, float) for p in f] for f in face_pts]
    allp = np.array([p for f in P for p in f])
    if np.max(np.abs(allp - np.round(allp))) > 1e-4:
        return None
    allp = np.round(allp)
    mn = allp.min(axis=0)
    P = [[np.round(p) - mn for p in f] for f in P]
    mx = allp.max(axis=0) - mn
    tris = []
    for f in P:
        for m in range(1, len(f) - 1):
            tris.append((f[0], f[m], f[m + 1]))

    def inside(x):
        # ray cast along a generic direction
        d = np.array([0.5772, 0.3141, 0.7539])
        cnt = 0
        for a, b, c in tris:
            e1, e2 = b - a, c - a
            h = np.cross(d, e2)
            det = np.dot(e1, h)
            if abs(det) < 1e-12:
                continue
            s = x - a
            u = np.dot(s, h) / det
            if u < 0 or u > 1:
                continue
            qv = np.cross(s, e1)
            v = np.dot(d, qv) / det
            if v < 0 or u + v > 1:
                continue
            if np.dot(e2, qv) / det > 1e-9:
                cnt += 1
        return cnt % 2 == 1

    if any(int(v) % 2 for v in mx):
        return None
    cells = {}
    for cx in range(int(mx[0]) // 2):
        for cy in range(int(mx[1]) // 2):
            for cz in range(int(mx[2]) // 2):
                ctr = np.array([cx, cy, cz]) * 2 + 1.0
                subs = frozenset(s for s in SUB if inside(ctr + (3 * V(s[0]) + 2 * V(s[1])) / 4 * 0.98))
                if not subs:
                    continue
                kind = KIND_OF_SUBS.get(subs)
                if kind is False:
                    return None
                if subs == frozenset(SUB):
                    cells[(cx, cy, cz)] = None
                elif kind is not None:
                    cells[(cx, cy, cz)] = kind
                else:
                    return None
    return cells


WEDGE_KINDS = []
for _a in DIRS:
    for _b in DIRS:
        if np.dot(_a, _b) == 0:
            WEDGE_KINDS.append((_a, _b))
assert len(WEDGE_KINDS) == 24  # 12 distinct wedges, each listed twice? (a,b) vs (-b,-a)
KIND_OF_SUBS = {}
for _k in WEDGE_KINDS:
    KIND_OF_SUBS.setdefault(kept_subs(_k), _k)
assert len(KIND_OF_SUBS) == 12
