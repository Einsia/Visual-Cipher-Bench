"""Exhaustive fold DFS with fold directions unknown, pruned by (1) unit lattice, (2) no 3-D edge used by
more than two faces, (3) no two faces with the same centroid, (4) sorted bounding-box extents of the
partial piece must fit the house's sorted extents (a piece that does not fit the house cannot be part
of the packing). Pure-Python inner loop (no numpy) for speed."""
import math, collections

def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _mv(M, v): return (M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2], M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2], M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2])
def _mm(A, B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))

def rot(axis, ang):
    n = math.sqrt(sum(x*x for x in axis)); k = [x/n for x in axis]
    c, s = math.cos(ang), math.sin(ang); C = 1-c; x, y, z = k
    return ((c+x*x*C, x*y*C-z*s, x*z*C+y*s), (y*x*C+z*s, c+y*y*C, y*z*C-x*s), (z*x*C-y*s, z*y*C+x*s, c+z*z*C))

def fold(faces, links, options, box=None, max_solutions=64, node_limit=50_000_000):
    """faces: 2D polys (printed side up, net units). links: (i, j, (A, B)). options[k]: interior angles.
    Returns (solutions as {face: [3D vertices]}, nodes)."""
    n = len(faces)
    ch = collections.defaultdict(list)
    for k, (i, j, e) in enumerate(links): ch[i].append((j, e, k))
    cs = {j for _, j, _ in links}; root = [i for i in range(n) if i not in cs][0]
    # nets may sit anywhere on the page and parts may lie at 45 degrees: move the net rigidly so that the root face has
    # a vertex at the origin and its first edge along +x (folding is unchanged; the lattice test then applies)
    ox, oy = faces[root][0]
    dx, dy = faces[root][1][0] - ox, faces[root][1][1] - oy
    L0 = math.hypot(dx, dy); c_, s_ = dx / L0, dy / L0
    tr2 = lambda p: (c_ * (p[0] - ox) + s_ * (p[1] - oy), -s_ * (p[0] - ox) + c_ * (p[1] - oy))
    faces = [[tr2(p) for p in f] for f in faces]
    links = [(i, j, (tr2(e[0]), tr2(e[1]))) for (i, j, e) in links]
    ch = collections.defaultdict(list)
    for k, (i, j, e) in enumerate(links): ch[i].append((j, e, k))
    order = []; q = [root]
    while q:
        i = q.pop(0)
        for (j, e, k) in ch[i]: order.append((i, j, e, k)); q.append(j)
    # per link: rotation candidates in the parent's local (net) frame, precomputed
    pre = []
    for (i, j, (A, B), k) in order:
        A3 = (A[0], A[1], 0.0); B3 = (B[0], B[1], 0.0)
        cj = (sum(p[0] for p in faces[j])/len(faces[j]), sum(p[1] for p in faces[j])/len(faces[j]), 0.0)
        d = _sub(B3, A3); w = _sub(cj, A3)
        side = 1 if d[0]*w[1]-d[1]*w[0] > 0 else -1
        cands = []
        for ang in options[k]:
            R = rot((d[0]*side, d[1]*side, 0.0), -math.radians(180-ang))
            t = _sub(A3, _mv(R, A3))
            cands.append((ang, R, t))
        pre.append((i, j, cands))
    key = lambda p: (round(p[0], 4), round(p[1], 4), round(p[2], 4))
    I = ((1.0, 0, 0), (0, 1.0, 0), (0, 0, 1.0))
    maps = {root: (I, (0.0, 0.0, 0.0))}
    pts = {root: [(x, y, 0.0) for x, y in faces[root]]}
    segs = collections.Counter(); cents = set()
    def addface(P):
        for m in range(len(P)): segs[frozenset((key(P[m]), key(P[(m+1) % len(P)])))] += 1
    addface(pts[root]); cents.add(key(tuple(sum(c)/len(pts[root]) for c in zip(*pts[root]))))
    lo = [min(p[a] for p in pts[root]) for a in range(3)]; hi = [max(p[a] for p in pts[root]) for a in range(3)]
    sols = []; nodes = [0]; boxs = sorted(box) if box else None
    def rec(t, lo, hi):
        nodes[0] += 1
        if nodes[0] > node_limit or len(sols) >= max_solutions: return
        if t == len(pre):
            if all(v == 2 for v in segs.values()):
                vol = 0.0
                for j in range(n):
                    P = pts[j]
                    for m in range(1, len(P)-1):
                        a, b, c = P[0], P[m], P[m+1]
                        vol += (a[0]*(b[1]*c[2]-b[2]*c[1]) - a[1]*(b[0]*c[2]-b[2]*c[0]) + a[2]*(b[0]*c[1]-b[1]*c[0]))/6
                if vol > 1e-6: sols.append({j: [key(p) for p in pts[j]] for j in range(n)})
            return
        i, j, cands = pre[t]
        Ri, ti = maps[i]
        for ang, Rl, tl in cands:
            R = _mm(Ri, Rl); tr = _add(_mv(Ri, tl), ti)
            P = [_add(_mv(R, (x, y, 0.0)), tr) for x, y in faces[j]]
            if any(abs(v-round(v)) > 1e-4 for p in P for v in p): continue
            c = key(tuple(sum(cc)/len(P) for cc in zip(*P)))
            if c in cents: continue
            new = [frozenset((key(P[m]), key(P[(m+1) % len(P)]))) for m in range(len(P))]
            if any(segs[s] >= 2 for s in new): continue
            lo2 = [min(lo[a], min(p[a] for p in P)) for a in range(3)]; hi2 = [max(hi[a], max(p[a] for p in P)) for a in range(3)]
            if boxs and any(e > b + 1e-6 for e, b in zip(sorted(h-l for h, l in zip(hi2, lo2)), boxs)): continue
            for s in new: segs[s] += 1
            maps[j] = (R, tr); pts[j] = P; cents.add(c)
            rec(t+1, lo2, hi2)
            cents.discard(c); del maps[j]; del pts[j]
            for s in new:
                segs[s] -= 1
                if segs[s] == 0: del segs[s]
    rec(0, lo, hi)
    return sols, nodes[0]
