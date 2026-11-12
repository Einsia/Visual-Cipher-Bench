"""Pixel parsing helpers for the flat-pack page: connected components, net faces, creases, letters, house, blanks.
Standard library + NumPy + Pillow only."""
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
S2 = math.sqrt(2) / 2


def load_gray(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.int32)
    return a, a.mean(axis=2)


# ------------------------------------------------------------------ connected components (run based union-find)
def label(mask, conn=4):
    H, W = mask.shape
    parent = []
    runs_prev = []
    lab = np.zeros((H, W), np.int32)
    runs_all = []

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for y in range(H):
        row = mask[y]
        d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
        st = np.where(d == 1)[0]
        en = np.where(d == -1)[0]
        cur = []
        j = 0
        for s, e in zip(st, en):
            idx = len(parent)
            parent.append(idx)
            cur.append((s, e, idx))
            runs_all.append((y, s, e, idx))
            lo, hi = (s - 1, e + 1) if conn == 8 else (s, e)
            for (ps, pe, pi) in runs_prev:
                if ps < hi and pe > lo:
                    a, b = find(pi), find(idx)
                    if a != b:
                        parent[b] = a
        runs_prev = cur
    roots = {}
    for (y, s, e, idx) in runs_all:
        r = find(idx)
        roots.setdefault(r, len(roots) + 1)
        lab[y, s:e] = roots[r]
    return lab, len(roots)


def comp_stats(lab, n):
    out = {}
    ys, xs = np.nonzero(lab)
    ls = lab[ys, xs]
    order = np.argsort(ls, kind="stable")
    ys, xs, ls = ys[order], xs[order], ls[order]
    bounds = np.searchsorted(ls, np.arange(1, n + 2))
    for k in range(1, n + 1):
        a, b = bounds[k - 1], bounds[k]
        if a == b:
            continue
        y, x = ys[a:b], xs[a:b]
        out[k] = dict(x0=int(x.min()), y0=int(y.min()), x1=int(x.max()), y1=int(y.max()), n=int(b - a),
                      cx=float(x.mean()), cy=float(y.mean()))
    return out


def dilate(mask, r):
    m = mask
    H, W = m.shape
    p = np.pad(m, r)
    out = np.zeros_like(m)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[dy:dy + H, dx:dx + W]
    return out


# ------------------------------------------------------------------ geometry
def convex_hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) <= 2:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def rdp_closed(poly, eps):
    """Simplify a closed convex polygon: repeatedly drop the vertex with the smallest triangle height."""
    P = [np.array(p, float) for p in poly]
    while len(P) > 3:
        best, bi = None, None
        for i in range(len(P)):
            a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
            ac = c - a
            L = np.linalg.norm(ac)
            h = abs(ac[0] * (b - a)[1] - ac[1] * (b - a)[0]) / L if L > 0 else 0
            if best is None or h < best:
                best, bi = h, i
        if best > eps:
            break
        P.pop(bi)
    return P


def offset_poly(P, s):
    """Offset a convex polygon (any orientation) outward by s px."""
    P = [np.array(p, float) for p in P]
    n = len(P)
    area = sum(P[i][0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * P[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    lines = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([d[1], -d[0]]) * sgn      # outward normal
        lines.append((a + nrm * s, d))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        M = np.array([d1, -d2]).T
        t = np.linalg.solve(M, p2 - p1)
        out.append(p1 + d1 * t[0])
    return out


def snap_coord(v, tol=0.06):
    """v = a + b*S2 with small integers; returns (value, error)."""
    best = None
    for b in range(-4, 5):
        a = round(v - b * S2)
        e = abs(a + b * S2 - v)
        if best is None or e < best[1] - 1e-9:
            best = (a + b * S2, e)
    return best


# ------------------------------------------------------------------ glyph templates
_CAPS = None


def caps():
    global _CAPS
    if _CAPS is None:
        _CAPS = json.loads((HERE / "caps.json").read_text())
    return _CAPS


def _contours(d):
    cs, cur = [], None
    toks = d.replace("M", " M ").replace("L", " L ").replace("Q", " Q ").replace("Z", " Z ").split()
    i = 0
    mode = None
    nums = []
    pending = []
    for t in toks:
        if t in "MLQZ":
            mode = t
            if t == "M":
                cur = []
                cs.append(cur)
            continue
        pending.append(float(t))
        if mode in ("M", "L") and len(pending) == 2:
            cur.append(tuple(pending))
            pending = []
        elif mode == "Q" and len(pending) == 4:
            x0, y0 = cur[-1]
            cx, cy, x1, y1 = pending
            for k in range(1, 9):
                u = k / 8
                cur.append(((1 - u) ** 2 * x0 + 2 * u * (1 - u) * cx + u * u * x1,
                            (1 - u) ** 2 * y0 + 2 * u * (1 - u) * cy + u * u * y1))
            pending = []
    return cs


_TPL = {}


def letter_template(ch, size=28.0, ss=4):
    """Antialiased darkness (0..1) of a capital at `size` px em, cropped to its ink box, plus nothing else."""
    key = (ch, size)
    if key in _TPL:
        return _TPL[key]
    c = caps()
    sc = size / c["units_per_em"] * ss
    g = c["glyphs"][ch]
    w = int(g["adv"] * sc) + 8 * ss
    h = int(c["cap_height"] * sc) + 8 * ss
    acc = np.zeros((h, w), np.uint8)
    for cont in _contours(g["d"]):
        im = Image.new("1", (w, h), 0)
        ImageDraw.Draw(im).polygon([(4 * ss + x * sc, 4 * ss + (c["cap_height"] - y) * sc) for x, y in cont], fill=1)
        acc ^= np.asarray(im, np.uint8)
    f = acc.astype(float)
    f = f[: h // ss * ss, : w // ss * ss].reshape(h // ss, ss, w // ss, ss).mean(axis=(1, 3))
    ys, xs = np.nonzero(f > 0.02)
    f = f[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    _TPL[key] = f
    return f


def match_letter(crop_dark):
    """crop_dark: float array 0..1 (ink darkness) tightly cropped to the glyph. Returns (best_letter, score, second)."""
    best = []
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        t = letter_template(ch)
        h = max(t.shape[0], crop_dark.shape[0]) + 2
        w = max(t.shape[1], crop_dark.shape[1]) + 2
        bs = -1
        for dy in range(0, 3):
            for dx in range(0, 3):
                A = np.zeros((h, w))
                B = np.zeros((h, w))
                A[1:1 + t.shape[0], 1:1 + t.shape[1]] = t
                B[dy:dy + crop_dark.shape[0], dx:dx + crop_dark.shape[1]] = crop_dark
                s = 2 * np.minimum(A, B).sum() / (A.sum() + B.sum() + 1e-9)
                bs = max(bs, s)
        best.append((bs, ch))
    best.sort(reverse=True)
    return best[0][1], best[0][0], best[1][0]


# ------------------------------------------------------------------ nets
R_CLOSE = 4          # dilation radius that closes the dotted creases
OFFSET = 6.7         # px from the white-region boundary back out to the line centre (r + half line width)


def find_net_components(gray):
    """Large dark connected components that could be nets (not the 3-D house); returns bboxes (x0,y0,x1,y1)."""
    ink = gray < 200
    lab, n = label(ink, 8)
    st = comp_stats(lab, n)
    out = []
    for k, s in st.items():
        w, h = s["x1"] - s["x0"] + 1, s["y1"] - s["y0"] + 1
        if s["n"] > 1500 and w >= 100 and h >= 40:
            out.append((s["x0"], s["y0"], s["x1"], s["y1"], s["n"]))
    return out


def edge_ink(gray, p, q, margin=9):
    """Look along the segment p->q (px coords) in a +-2.5 px band; return (min value, coverage<110, coverage<215)."""
    p, q = np.array(p, float), np.array(q, float)
    L = np.linalg.norm(q - p)
    d = (q - p) / L
    nrm = np.array([-d[1], d[0]])
    vals = []
    t = margin
    while t < L - margin:
        best = 255
        for o in (-2, -1, 0, 1, 2):
            x, y = p + d * t + nrm * o
            xi, yi = int(round(x)), int(round(y))
            best = min(best, gray[yi, xi])
        vals.append(best)
        t += 1.0
    vals = np.array(vals)
    return float(vals.min()), float((vals < 110).mean()), float((vals < 215).mean())


def parse_net(gray, bbox):
    x0, y0, x1, y1 = bbox[:4]
    X0, Y0 = max(0, x0 - 12), max(0, y0 - 12)
    X1, Y1 = min(gray.shape[1], x1 + 13), min(gray.shape[0], y1 + 13)
    g = gray[Y0:Y1, X0:X1]
    ink = g < 215
    barrier = dilate(ink, R_CLOSE)
    lab, n = label(~barrier, 4)
    st = comp_stats(lab, n)
    faces_px = []
    for k, s in st.items():
        if s["x0"] == 0 or s["y0"] == 0 or s["x1"] == g.shape[1] - 1 or s["y1"] == g.shape[0] - 1:
            continue
        if s["n"] < 600:
            continue
        m = lab == k
        pts = []
        for y in range(s["y0"], s["y1"] + 1):
            xs = np.nonzero(m[y])[0]
            if len(xs):
                pts.append((xs.min(), y))
                pts.append((xs.max(), y))
        hull = convex_hull(pts)
        poly = rdp_closed(hull, 2.2)
        poly = offset_poly(poly, OFFSET)
        poly = [(p[0] + X0, p[1] + Y0) for p in poly]
        faces_px.append(dict(poly_px=poly, area_px=s["n"], mask_box=(s["x0"] + X0, s["y0"] + Y0, s["x1"] + X0, s["y1"] + Y0),
                             region_mask=m[s["y0"]:s["y1"]+1, s["x0"]:s["x1"]+1]))
    return faces_px


def snap_net(faces_px, unit=None):
    """Snap face polygons to net coordinates (unit = 1, y up, vertices a + b*sqrt(2)/2). Returns (faces, info)."""
    allv = [np.array(p) for f in faces_px for p in f["poly_px"]]
    xs = np.array([p[0] for p in allv]); ys = np.array([p[1] for p in allv])
    xmin, ymin = xs.min(), ys.min()

    def resid(u):
        ex = [snap_coord((x - xmin) / u)[1] * u for x in xs]
        ey = [snap_coord((y - ymin) / u)[1] * u for y in ys]
        return float(np.mean(ex + ey))
    cands = [(resid(u), u) for u in np.arange(62.0, 78.01, 0.25)]
    u = min(cands)[1] if unit is None else unit
    ox, oy = xmin, ymin
    for it in range(3 if unit is None else 0):
        X = [snap_coord((x - ox) / u)[0] for x in xs]
        Y = [snap_coord((y - oy) / u)[0] for y in ys]
        A = np.array([[1, x] for x in X]); ox, u1 = np.linalg.lstsq(A, xs, rcond=None)[0]
        A2 = np.array([[1, y] for y in Y]); oy, u2 = np.linalg.lstsq(A2, ys, rcond=None)[0]
        u = (u1 + abs(u2)) / 2
        # y is measured downward from ymin: keep orientation explicit below
    X, Y, err = [], [], []
    for x, y in zip(xs, ys):
        sx, ex = snap_coord((x - ox) / u)
        sy, ey = snap_coord((y - ymin) / u)
        X.append(sx); Y.append(-sy); err.append(max(ex, ey))
    out = []
    k = 0
    for f in faces_px:
        n = len(f["poly_px"])
        poly = [(round(X[k + i], 6), round(Y[k + i], 6)) for i in range(n)]
        k += n
        area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
        if area < 0:
            poly = poly[::-1]
        out.append(dict(f, poly=poly))
    return out, dict(unit=float(u), origin=(float(ox), float(ymin)), max_err=float(max(err)), mean_resid=float(resid(u)))


def face_kind(poly):
    """'sq', 'rect' (1 x sqrt2), 'tri' (right isosceles legs 1) or None, from snapped coordinates."""
    P = [np.array(p) for p in poly]
    n = len(P)
    L = sorted(np.linalg.norm(P[i] - P[(i + 1) % n]) for i in range(n))
    if n == 4:
        if abs(L[0] - 1) < 0.02 and abs(L[3] - 1) < 0.02:
            return "sq"
        if abs(L[0] - 1) < 0.02 and abs(L[1] - 1) < 0.02 and abs(L[2] - 2 * S2 * 1.0000001 * 1) < 1 and abs(L[3] - math.sqrt(2)) < 0.02 and abs(L[2] - math.sqrt(2)) < 0.02:
            return "rect"
    if n == 3 and abs(L[0] - 1) < 0.02 and abs(L[1] - 1) < 0.02 and abs(L[2] - math.sqrt(2)) < 0.02:
        return "tri"
    return None


def find_links(faces, gray, u, origin):
    """Shared full edges between faces; classify the ink on each as dotted fold / grey flat seam / solid cut."""
    ox, oy = origin

    def px(p):
        return (ox + u * p[0], oy - u * p[1])
    edges = {}
    for i, f in enumerate(faces):
        P = f["poly"]
        for m in range(len(P)):
            a, b = P[m], P[(m + 1) % len(P)]
            key = frozenset([tuple(np.round(a, 3)), tuple(np.round(b, 3))])
            edges.setdefault(key, []).append((i, a, b))
    links, cuts = [], []
    for key, lst in edges.items():
        if len(lst) != 2:
            continue
        (i, a, b), (j, _, _) = lst
        mn, cov_dark, cov_any = edge_ink(gray, px(a), px(b))
        if cov_dark > 0.85:
            kind = "cut"
        elif mn < 110 and 0.15 <= cov_dark <= 0.75:
            kind = "fold"
        elif mn >= 110 and cov_any > 0.85:
            kind = "flat"
        else:
            kind = "unknown"
        rec = dict(i=i, j=j, a=a, b=b, kind=kind, stat=(round(mn, 1), round(cov_dark, 2), round(cov_any, 2)))
        (cuts if kind == "cut" else links).append(rec)
    return links, cuts


# ------------------------------------------------------------------ template fit (more accurate than raw vertices)
_BASE = {
    "sq": [(0, 0), (1, 0), (1, 1), (0, 1)],
    "rect": [(0, 0), (math.sqrt(2), 0), (math.sqrt(2), 1), (0, 1)],
    "tri": [(0, 0), (1, 0), (0, 1)],
}
_AREA = {"sq": 1.0, "rect": math.sqrt(2), "tri": 0.5}


def _poly_area(P):
    n = len(P)
    return sum(P[i][0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * P[i][1] for i in range(n)) / 2


def _iou(A, B, res=16):
    allp = np.array(A + B)
    mn = allp.min(axis=0) - 0.2
    mx = allp.max(axis=0) + 0.2
    W, H = int((mx[0] - mn[0]) * res) + 2, int((mx[1] - mn[1]) * res) + 2
    ims = []
    for Pp in (A, B):
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([((x - mn[0]) * res, (y - mn[1]) * res) for x, y in Pp], fill=1)
        ims.append(np.asarray(im))
    return float((ims[0] & ims[1]).sum() / max(1, (ims[0] | ims[1]).sum()))


def fit_face(poly_u):
    """poly_u: measured vertices in unit coordinates (y up, CCW). Returns (kind, exact polygon at measured position, iou)."""
    area = abs(_poly_area(poly_u))
    kind = min(_AREA, key=lambda k: abs(math.log(max(area, 1e-6) / _AREA[k])))
    if abs(math.log(max(area, 1e-6) / _AREA[kind])) > 0.3:
        return None, None, 0.0
    cen = np.array(poly_u).mean(axis=0)
    # polygon centroid
    A = _poly_area(poly_u)
    n = len(poly_u)
    cx = sum((poly_u[i][0] + poly_u[(i + 1) % n][0]) * (poly_u[i][0] * poly_u[(i + 1) % n][1] - poly_u[(i + 1) % n][0] * poly_u[i][1]) for i in range(n)) / (6 * A)
    cy = sum((poly_u[i][1] + poly_u[(i + 1) % n][1]) * (poly_u[i][0] * poly_u[(i + 1) % n][1] - poly_u[(i + 1) % n][0] * poly_u[i][1]) for i in range(n)) / (6 * A)
    best = (-1, None)
    for k in range(8):
        a = k * math.pi / 4
        c, s = math.cos(a), math.sin(a)
        T = [(c * x - s * y, s * x + c * y) for x, y in _BASE[kind]]
        tc = np.array(T).mean(axis=0) if kind == "tri" else None
        # centroid of template
        At = _poly_area(T)
        m = len(T)
        tx = sum((T[i][0] + T[(i + 1) % m][0]) * (T[i][0] * T[(i + 1) % m][1] - T[(i + 1) % m][0] * T[i][1]) for i in range(m)) / (6 * At)
        ty = sum((T[i][1] + T[(i + 1) % m][1]) * (T[i][0] * T[(i + 1) % m][1] - T[(i + 1) % m][0] * T[i][1]) for i in range(m)) / (6 * At)
        Tp = [(x - tx + cx, y - ty + cy) for x, y in T]
        io = _iou(Tp, [tuple(p) for p in poly_u])
        if io > best[0] + 1e-9:
            best = (io, Tp)
    io, Tp = best
    # refine translation: match each template vertex to the nearest measured vertex
    Q = np.array(poly_u)
    d = np.array([Q[np.argmin(np.linalg.norm(Q - np.array(t), axis=1))] - np.array(t) for t in Tp])
    # keep only well-matched vertices (the 45-degree corners are noisy)
    ok = np.linalg.norm(d, axis=1) < 0.12
    if ok.sum() >= 2:
        shift = d[ok].mean(axis=0)
        Tp = [(x + shift[0], y + shift[1]) for x, y in Tp]
    return kind, Tp, io


def exact_faces(faces_px, unit, tol=0.075):
    """Fit exact face shapes and snap them to a common lattice. Returns (faces, info)."""
    xs = [p[0] for f in faces_px for p in f["poly_px"]]
    ys = [p[1] for f in faces_px for p in f["poly_px"]]
    ox, oy = min(xs), min(ys)
    fits = []
    for f in faces_px:
        pu = [((p[0] - ox) / unit, -(p[1] - oy) / unit) for p in f["poly_px"]]
        if _poly_area(pu) < 0:
            pu = pu[::-1]
        kind, T, io = fit_face(pu)
        fits.append((kind, T, io))
    # snap: translate each fitted face so that its first vertex is on the lattice, using one global shift
    g = np.zeros(2)
    for it in range(4):
        res = []
        for kind, T, io in fits:
            if T is None:
                continue
            ax, ay = T[0]
            sx, ex = snap_coord(ax - g[0])
            sy, ey = snap_coord(ay - g[1])
            res.append((ax - sx, ay - sy, max(ex, ey)))
        g = np.array([np.mean([r[0] for r in res]), np.mean([r[1] for r in res])])
    out, errs = [], []
    for f, (kind, T, io) in zip(faces_px, fits):
        if T is None:
            out.append(dict(f, kind=None, poly=None, iou=io))
            continue
        ax, ay = T[0]
        sx, ex = snap_coord(ax - g[0])
        sy, ey = snap_coord(ay - g[1])
        errs.append(max(ex, ey))
        poly = [(round(x - ax + sx, 6), round(y - ay + sy, 6)) for x, y in T]
        out.append(dict(f, kind=kind, poly=poly, iou=io))
    return out, dict(max_err=float(max(errs)), min_iou=float(min(f["iou"] for f in out)), origin=(float(ox - g[0] * unit), float(oy)),
                     shift=g.tolist(), unit=unit, ox=float(ox), oy=float(oy))


def global_unit(gray, boxes):
    """Net unit in px: scan u so that hull vertices of all nets sit on the a + b*sqrt(2)/2 lattice."""
    sets = []
    for b in boxes:
        f = parse_net(gray, b)
        sets.append(([p[0] for ff in f for p in ff["poly_px"]], [p[1] for ff in f for p in ff["poly_px"]]))
    best = None
    for u in np.arange(60.0, 80.01, 0.1):
        tot, cnt = 0.0, 0
        for xs, ys in sets:
            xmin, ymin = min(xs), min(ys)
            for v, m in [(x, xmin) for x in xs] + [(y, ymin) for y in ys]:
                tot += snap_coord((v - m) / u)[1] * u
                cnt += 1
        if best is None or tot / cnt < best[0]:
            best = (tot / cnt, u)
    return float(best[1]), float(best[0])


def px_of(info):
    ox, oy, u = info["ox"], info["oy"], info["unit"]
    gx, gy = info["shift"]
    return lambda p: (ox + u * (p[0] + gx), oy - u * (p[1] + gy))


def find_links2(faces, gray, info):
    px = px_of(info)
    edges = {}
    for i, f in enumerate(faces):
        P = f["poly"]
        for m in range(len(P)):
            a, b = P[m], P[(m + 1) % len(P)]
            key = frozenset([(round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3))])
            edges.setdefault(key, []).append((i, a, b))
    links, cuts = [], []
    for key, lst in edges.items():
        if len(lst) != 2:
            continue
        (i, a, b), (j, _, _) = lst
        mn, cd, ca = edge_ink(gray, px(a), px(b))
        if cd > 0.85:
            kind = "cut"
        elif mn < 110 and 0.15 <= cd <= 0.75:
            kind = "fold"
        elif mn >= 110 and ca > 0.85:
            kind = "flat"
        else:
            kind = "unknown"
        rec = dict(i=i, j=j, a=a, b=b, kind=kind, stat=(round(mn, 1), round(cd, 2), round(ca, 2)))
        (cuts if kind == "cut" else links).append(rec)
    return links, cuts


def face_letter(gray, face, info):
    """Find the printed capital and its underline inside a face; returns dict(letter, up (net coords), score) or None."""
    px = px_of(info)
    P = np.array([px(p) for p in face["poly"]])
    cen = P.mean(axis=0)
    x0, y0, x1, y1 = [int(v) for v in (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())]
    # shrink: keep pixels farther than 9 px from every edge (polygon inset)
    inset = Image.new("L", (gray.shape[1], gray.shape[0]), 0)
    Pin = _inset(P, 9.0)
    ImageDraw.Draw(inset).polygon([tuple(p) for p in Pin], fill=255)
    m = (np.asarray(inset) > 0) & (gray < 150)
    sub = m[y0:y1 + 1, x0:x1 + 1]
    if sub.sum() < 20:
        return None
    lab, n = label(sub, 8)
    st = comp_stats(lab, n)
    # merge small bits that belong to the glyph; underline = very elongated thin component
    bars, glyph = [], []
    for k, s in st.items():
        w, h = s["x1"] - s["x0"] + 1, s["y1"] - s["y0"] + 1
        if min(w, h) <= 5 and max(w, h) >= 16 and s["n"] >= 0.7 * w * h:
            bars.append((k, s))
        elif s["n"] >= 4:
            glyph.append((k, s))
    if len(bars) != 1 or not glyph:
        return dict(letter=None, reason=f"bars={len(bars)} glyph_parts={len(glyph)}")
    gx0 = min(s["x0"] for _, s in glyph); gy0 = min(s["y0"] for _, s in glyph)
    gx1 = max(s["x1"] for _, s in glyph); gy1 = max(s["y1"] for _, s in glyph)
    bs = bars[0][1]
    gc = np.array([(gx0 + gx1) / 2, (gy0 + gy1) / 2])
    bc = np.array([bs["cx"], bs["cy"]])
    v = gc - bc                                   # from underline toward the glyph = "up" of the letter (pixel coords)
    if abs(v[0]) > abs(v[1]):
        up_px = (1 if v[0] > 0 else -1, 0)
    else:
        up_px = (0, 1 if v[1] > 0 else -1)         # pixel y down: +1 means pointing down the page
    up_net = (up_px[0], -up_px[1])
    crop = np.zeros((gy1 - gy0 + 1, gx1 - gx0 + 1))
    for k, s in glyph:
        mk = (lab == k)
        crop += mk[gy0:gy1 + 1, gx0:gx1 + 1]
    # use grey darkness for antialiasing
    gs = gray[y0:y1 + 1, x0:x1 + 1][gy0:gy1 + 1, gx0:gx1 + 1]
    dark = np.clip((255 - gs) / (255 - 17.0), 0, 1) * (crop > 0)
    # rotate so that "up" points up in the array
    if up_px == (0, -1):
        k = 0
    elif up_px == (1, 0):
        k = 1       # up points right -> rotate counter-clockwise by 90
    elif up_px == (0, 1):
        k = 2
    else:
        k = 3
    rot = np.rot90(dark, k)
    ch, score, second = match_letter(rot)
    return dict(letter=ch, up=up_net, score=round(score, 3), second=round(second, 3),
                box=(x0 + gx0, y0 + gy0, x0 + gx1, y0 + gy1), glyph_h=int(max(gx1 - gx0, gy1 - gy0) + 1) if False else int(
                    (gy1 - gy0 + 1) if up_px[1] != 0 else (gx1 - gx0 + 1)))


def _inset(P, s):
    P = [np.array(p, float) for p in P]
    n = len(P)
    A = sum(P[i][0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * P[i][1] for i in range(n))
    sgn = 1 if A > 0 else -1
    lines = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([d[1], -d[0]]) * sgn
        lines.append((a - nrm * s, d))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        M = np.array([d1, -d2]).T
        t = np.linalg.solve(M, p2 - p1)
        out.append(p1 + d1 * t[0])
    return out


# ------------------------------------------------------------------ the 3-D house
TOWARD = (0.62, -1.0, 0.78)      # page convention: axonometric view from front-right-above (same for the worked example)


def candidate_houses():
    """Small family: main block nx x ny x nz of cubes, optional gable roof wedges (ridge along x), optional one-cell
    annex at the +x end (a cube on the ground, optionally capped by a lean-to wedge falling toward +x)."""
    for nx in range(2, 7):
        for ny in range(1, 5):
            for nz in range(1, 4):
                for roof in (0, 1):
                    if roof and ny % 2:
                        continue
                    base = {}
                    for x in range(nx):
                        for y in range(ny):
                            for z in range(nz):
                                base[(x, y, z)] = None
                            if roof:
                                base[(x, y, nz)] = ((0, 0, 1), (0, 1, 0)) if y < ny // 2 else ((0, 0, 1), (0, -1, 0))
                    yield dict(base), (nx, ny, nz, roof, None, 0)
                    for ay in range(ny):
                        for lean in (0, 1):
                            c = dict(base)
                            c[(nx, ay, 0)] = None
                            if lean:
                                c[(nx, ay, 1)] = ((0, 0, 1), (-1, 0, 0))
                            yield c, (nx, ny, nz, roof, ay, lean)


def _fill_value(n):
    if n[2] > 1e-6:
        return 238
    if n[0] > 1e-6:
        return 217
    return 255


def render_candidate(cells, view, scale, off, shape):
    import housegeom as hg
    polys = hg.surface(cells)
    items = []
    for vs, n, t in polys:
        if not view.visible_face(n):
            continue
        pts = [view.xy(np.array(p, float) / 2.0) for p in vs]
        depth = float(np.dot(np.mean([np.array(p, float) / 2.0 for p in vs], axis=0), view.v))
        items.append((depth, pts, _fill_value(n)))
    items.sort(key=lambda t: t[0])
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    for depth, pts, val in items:
        d.polygon([(off[0] + scale * x, off[1] - scale * y) for x, y in pts], fill=val)
    return np.asarray(im)


def candidate_bbox(cells, view):
    import housegeom as hg
    pts = []
    for vs, n, t in hg.surface(cells):
        for p in vs:
            pts.append(view.xy(np.array(p, float) / 2.0))
    a = np.array(pts)
    return a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()


def fit_house(gray, bbox):
    import housegeom as hg
    view = hg.View(TOWARD)
    x0, y0, x1, y1 = bbox[:4]
    X0, Y0, X1, Y1 = x0 - 6, y0 - 6, x1 + 7, y1 + 7
    g = gray[Y0:Y1, X0:X1]
    # silhouette = not reachable from the border over near-white pixels
    white = g >= 250
    lab, n = label(white, 4)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
    outside = np.isin(lab, list(border))
    sil = ~outside
    ys, xs = np.nonzero(sil)
    ow, oh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    obs_cls = np.zeros(g.shape, np.int32)       # 0 unknown (lines), else fill value
    for v in (238, 217, 255):
        obs_cls[(np.abs(g - v) <= 4) & sil] = v
    results = []
    for cells, tag in candidate_houses():
        bx0, bx1, by0, by1 = candidate_bbox(cells, view)
        sx, sy = ow / (bx1 - bx0), oh / (by1 - by0)
        if abs(sx / sy - 1) > 0.04:
            continue
        s = (sx + sy) / 2
        off = (xs.min() - bx0 * s, ys.min() + by1 * s)
        pred = render_candidate(cells, view, s, off, g.shape)
        psil = pred > 0
        inter = (psil & sil).sum()
        iou = inter / max(1, (psil | sil).sum())
        if iou < 0.9:
            results.append((iou * 0.0, iou, 0.0, tag, cells, s))
            continue
        known = obs_cls > 0
        agree = ((pred == obs_cls) & known).sum() / max(1, known.sum())
        results.append((agree + iou, iou, agree, tag, cells, s))
    results.sort(key=lambda r: -r[0])
    return results[:3], dict(unit_px=float(results[0][5]))
