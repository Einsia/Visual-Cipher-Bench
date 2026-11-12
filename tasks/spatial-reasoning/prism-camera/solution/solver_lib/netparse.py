"""Pixel parsing of the flat-pack nets for pages whose nets may have branches turned by 45 degrees.
Standard library + NumPy + Pillow only. Builds on pixparse (components, hulls, template fit)."""
import collections
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pixparse as P

HERE = Path(__file__).resolve().parent
S2 = math.sqrt(2) / 2


# ------------------------------------------------------------------ unit and face fitting
def estimate_unit(faces_px):
    """Net unit in px = median over faces of the shortest edge of the measured face polygon."""
    ls = []
    for f in faces_px:
        Q = [np.array(p, float) for p in f["poly_px"]]
        n = len(Q)
        e = sorted(np.linalg.norm(Q[i] - Q[(i + 1) % n]) for i in range(n))
        ls.append(e[0])
    return float(np.median(ls)) if ls else 0.0


def page_unit(parsed):
    """Robust scale from intact square outlines; ignores concave-panel hull edges.
    It needs no sheet dimensions or fixed unit constant.
    """
    estimates=[]
    for _,faces in parsed:
        for f in faces:
            q=np.asarray(f["poly_px"],float)
            if len(q)!=4:continue
            d=np.roll(q,-1,axis=0)-q
            lengths=np.linalg.norm(d,axis=1)
            if min(lengths)<15 or max(lengths)/min(lengths)>1.12:continue
            if max(abs(np.dot(d[i],d[(i+1)%4])/(lengths[i]*lengths[(i+1)%4])) for i in range(4))>.12:continue
            # Unit-square edges in this notation use the page's 0/45-degree frames.
            if any(min(abs(v[0]),abs(v[1]),abs(abs(v[0])-abs(v[1]))) / np.linalg.norm(v)>.08 for v in d):continue
            estimates.append(float(np.mean(lengths)))
    if not estimates:raise ValueError("no intact square from which to recover scale")
    groups=[[v for v in estimates if abs(v/u-1)<.06] for u in estimates]
    group=max(groups,key=len)
    unit=float(np.median(group))
    return unit


def refine_unit(faces_px, u0):
    """Second pass: unit from face areas (measured polygon area / template area), robust median."""
    A = {"sq": 1.0, "rect": math.sqrt(2), "tri": 0.5}
    fits = fit_all(faces_px, u0)
    est = []
    for f, fi in zip(faces_px, fits):
        if fi["kind"] is None or fi["iou"] < .90:
            continue
        est.append(math.sqrt(abs(P._poly_area(f["poly_px"])) / A[fi["kind"]]))
    return float(np.median(est)) if est else u0


def fit_all(faces_px, u):
    """Template fit of every measured face. Returns faces with kind, exact polygon (unit coordinates, y up, CCW)."""
    out = []
    for f in faces_px:
        pu = [(x / u, -y / u) for x, y in f["poly_px"]]
        if P._poly_area(pu) < 0:
            pu = pu[::-1]
        kind, T, io = P.fit_face(pu)
        out.append(dict(kind=kind, poly=None if T is None else [tuple(map(float, t)) for t in T], iou=float(io)))
    return out


def px_of(p, u):
    return (p[0] * u, -p[1] * u)


# ------------------------------------------------------------------ creases
def classify_edge(gray, a_px, b_px, margin=9):
    """Look along the segment; returns (kind, stats). kind in cut | flat | mountain | valley | unknown."""
    p, q = np.array(a_px, float), np.array(b_px, float)
    L = float(np.linalg.norm(q - p))
    d = (q - p) / L
    nrm = np.array([-d[1], d[0]])
    vals = []
    t = float(margin)
    while t < L - margin:
        best = 255.0
        for o in (-2, -1, 0, 1, 2):
            x, y = p + d * t + nrm * o
            best = min(best, gray[int(round(y)), int(round(x))])
        vals.append(best)
        t += 1.0
    v = np.array(vals)
    dark = v < 110
    mn, cd, ca = float(v.min()), float(dark.mean()), float((v < 215).mean())
    runs = []
    s = None
    for k, x in enumerate(dark):
        if x and s is None:
            s = k
        if (not x) and s is not None:
            runs.append((s, k - 1))
            s = None
    if s is not None:
        runs.append((s, len(dark) - 1))
    interior = [(a, b) for a, b in runs if a > 0 and b < len(dark) - 1]
    short = [b - a + 1 for a, b in interior if b - a + 1 <= 5]
    # longest stretch without the mark's own ink (gap in the line)
    def longest_false(mask):
        best = cur = 0
        for x in mask:
            cur = 0 if x else cur + 1
            best = max(best, cur)
        return best
    gap_dark = longest_false(dark)
    gap_any = longest_false(v < 215)
    stats = dict(min=round(mn, 1), dark=round(cd, 2), any=round(ca, 2), runs=len(runs), short_runs=len(short),
                 max_gap=int(gap_dark), max_gap_any=int(gap_any))
    if cd > 0.85 and gap_any <= 3:
        return "cut", stats
    if mn >= 110 and ca > 0.85 and gap_any <= 3:
        return "flat", stats
    if mn < 110 and 0.15 <= cd <= 0.8 and gap_dark <= 10:
        return ("mountain" if short else "valley"), stats
    return "unknown", stats


def shared_edges(faces, tol=0.09):
    E = []
    for i, f in enumerate(faces):
        Q = f["poly"]
        n = len(Q)
        for m in range(n):
            E.append((i, np.array(Q[m]), np.array(Q[(m + 1) % n])))
    out = []
    for x in range(len(E)):
        for y in range(x + 1, len(E)):
            i, a, b = E[x]
            j, c, d = E[y]
            if i == j:
                continue
            if abs(np.linalg.norm(b - a) - np.linalg.norm(d - c)) > 0.08:
                continue
            d1 = max(np.linalg.norm(a - c), np.linalg.norm(b - d))
            d2 = max(np.linalg.norm(a - d), np.linalg.norm(b - c))
            if min(d1, d2) < tol:
                out.append((i, j, a, b, c, d))
    return out


def build_net(gray, faces_px, u):
    """Fit faces, find shared edges, classify them, glue the linked faces exactly (unit coordinates, y up)."""
    fits = fit_all(faces_px, u)
    n = len(fits)
    if any(f["poly"] is None for f in fits):
        return None, "face not matching any template"
    if min(f["iou"] for f in fits) < 0.8:
        return None, "face template fit too loose"
    edges = shared_edges(fits)
    links, cuts = [], []
    for (i, j, a, b, c, d) in edges:
        kind, stats = classify_edge(gray, px_of(a, u), px_of(b, u))
        implicit = (faces_px[i].get("panel_id") is not None
                    and faces_px[i].get("panel_id") == faces_px[j].get("panel_id"))
        if implicit:
            # This boundary exists only in our computational subdivision of a
            # single connected paper panel. Its PNG pixels must be blank.
            if stats["any"] > .05:
                return None, "inferred flat join crosses printed ink"
            kind = "flat"
        rec = dict(i=i, j=j, a=(float(a[0]), float(a[1])), b=(float(b[0]), float(b[1])), c=tuple(map(float, c)),
                   d=tuple(map(float, d)), kind=kind, stat=stats, implicit=implicit)
        (cuts if kind == "cut" else links).append(rec)
    if any(l["kind"] == "unknown" for l in links):
        return None, "unclassified edge: %s" % [l["stat"] for l in links if l["kind"] == "unknown"]
    if len(links) != n - 1:
        return None, "links=%d for %d faces (not a tree)" % (len(links), n)
    adj = collections.defaultdict(list)
    for k, l in enumerate(links):
        adj[l["i"]].append((l["j"], k))
        adj[l["j"]].append((l["i"], k))
    root = next(i for i, f in enumerate(fits) if f["kind"] == "sq")
    pos = {root: [np.array(p) for p in fits[root]["poly"]]}
    order = [root]
    glued = []
    for a_ in order:
        for b_, k in adj[a_]:
            if b_ in pos:
                continue
            l = links[k]
            # the shared edge in a_'s glued frame: take the edge of a_ nearest to the measured link edge
            Pa = pos[a_]
            Pb0 = [np.array(p) for p in fits[b_]["poly"]]
            # measured edge endpoints belonging to a_ and b_
            if l["i"] == a_:
                ea, eb = np.array(l["a"]), np.array(l["b"])
                ec, ed = np.array(l["c"]), np.array(l["d"])
            else:
                ea, eb = np.array(l["c"]), np.array(l["d"])
                ec, ed = np.array(l["a"]), np.array(l["b"])
            # glued endpoints of a_ edge: match measured ea, eb to vertices of a_ (original fitted) -> glued vertices
            Qa0 = [np.array(p) for p in fits[a_]["poly"]]
            def glued_of(pt):
                m = int(np.argmin([np.linalg.norm(q - pt) for q in Qa0]))
                return Pa[m]
            A, B = glued_of(ea), glued_of(eb)
            C = Pb0[int(np.argmin([np.linalg.norm(q - ec) for q in Pb0]))]
            D = Pb0[int(np.argmin([np.linalg.norm(q - ed) for q in Pb0]))]
            if np.linalg.norm(A - B) < 1e-6 or np.linalg.norm(C - D) < 1e-6:
                return None, "degenerate shared edge"
            if abs(np.linalg.norm(A - B) - np.linalg.norm(C - D)) > 1e-6:
                return None, "edge length mismatch while gluing"
            tdir = (A + B) / 2 - (C + D) / 2
            pos[b_] = [q + tdir for q in Pb0]
            order.append(b_)
            glued.append((a_, b_, (tuple(A), tuple(B)), l["kind"]))
    if len(pos) != n:
        return None, "net not connected through links"
    faces = []
    for i in range(n):
        faces.append(dict(kind=fits[i]["kind"], poly=[tuple(map(float, p)) for p in pos[i]], iou=fits[i]["iou"],
                          fit_poly=fits[i]["poly"]))
    return dict(faces=faces, links=links, cuts=cuts, glued=glued, root=root, unit=u), None


# ------------------------------------------------------------------ letters
_CAPS = None


def caps():
    global _CAPS
    if _CAPS is None:
        _CAPS = json.loads((HERE / "caps.json").read_text())
    return _CAPS


_GT = {}
SZ = 80          # side of the template canvas
FONT_PX = 28.0
UL_GAP, UL_W, UL_LEN = 6.0, 3.0, 24.0


def group_template(ch, ss=4):
    """Upright capital with its underline, centred as the page draws it (group centred on the canvas centre)."""
    if ch in _GT:
        return _GT[ch]
    c = caps()
    sc = FONT_PX / c["units_per_em"] * ss
    cap = c["cap_height"] * FONT_PX / c["units_per_em"]
    top = -(cap + UL_GAP + UL_W) / 2
    base = top + cap
    g = c["glyphs"][ch]
    W = SZ * ss
    acc = np.zeros((W, W), np.uint8)
    x0 = W / 2 - g["adv"] * sc / 2
    yb = W / 2 + base * ss
    for cont in P._contours(g["d"]):
        im = Image.new("1", (W, W), 0)
        ImageDraw.Draw(im).polygon([(x0 + x * sc, yb - y * sc) for x, y in cont], fill=1)
        acc ^= np.asarray(im, np.uint8)
    im = Image.fromarray(acc * 255).convert("L")
    d = ImageDraw.Draw(im)
    uy0 = W / 2 + (base + UL_GAP) * ss
    d.rectangle([W / 2 - UL_LEN / 2 * ss, uy0, W / 2 + UL_LEN / 2 * ss - 1, uy0 + UL_W * ss - 1], fill=255)
    f = np.asarray(im, float) / 255.0
    f = f.reshape(SZ, ss, SZ, ss).mean(axis=(1, 3))
    _GT[ch] = f
    return f


def _inset(Q, s):
    return P._inset(Q, s)


def face_letter(gray, poly_px, inset=9.0):
    """Read the capital and its underline inside one face. The face may carry the letter at any of 8 rotations.
    Returns None if there is no ink, else dict(letter, angle_deg (visual clockwise turn from upright), up (page y-up
    vector), score, margin, glyph_h)."""
    Q = np.array(poly_px, float)
    c = Q.mean(axis=0)
    H, W = gray.shape
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in _inset(Q, inset)], fill=255)
    cx, cy = int(round(c[0])), int(round(c[1]))
    half = 70
    box = (cx - half, cy - half, cx + half, cy + half)
    mk = np.asarray(m.crop(box)) > 0
    dark = np.clip((255 - gray[cy - half:cy + half, cx - half:cx + half]) / (255 - 17.0), 0, 1) * mk
    if dark.sum() < 25:
        return None
    ctr = (c[0] - (cx - half), c[1] - (cy - half))
    img = Image.fromarray(dark.astype(np.float32), mode="F")
    best = []
    for k in range(8):
        ang = 45 * k             # visual clockwise rotation of the letter in the page
        r = np.asarray(img.rotate(ang, resample=Image.BICUBIC, center=ctr), float)   # PIL rotates counter-clockwise: undo
        # centre crop SZ x SZ around the rotation centre
        x0, y0 = int(round(ctr[0])) - SZ // 2, int(round(ctr[1])) - SZ // 2
        win = r[y0:y0 + SZ, x0:x0 + SZ]
        win = np.clip(win, 0, 1)
        if win.sum() < 25:
            continue
        gy, gx = np.mgrid[0:SZ, 0:SZ]
        wc = np.array([(win * gy).sum(), (win * gx).sum()]) / win.sum()
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            t = group_template(ch)
            tc = np.array([(t * gy).sum(), (t * gx).sum()]) / t.sum()
            sh = np.round(tc - wc).astype(int)
            bs = -1.0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    w2 = np.roll(np.roll(win, sh[0] + dy, axis=0), sh[1] + dx, axis=1)
                    s = 2 * np.minimum(w2, t).sum() / (w2.sum() + t.sum())
                    if s > bs:
                        bs = s
            best.append((bs, ch, k))
    best.sort(reverse=True)
    top = best[0]
    others = [b for b in best[1:] if (b[1], b[2]) != (top[1], top[2])]
    second = others[0][0]
    other_letter = [b for b in best[1:] if b[1] != top[1]][0][0]
    k = top[2]
    ang = 45 * k
    g_best, g_second = _glyph_only(img, ctr, ang, top[1])
    # up vector: letter turned clockwise by ang on the page -> page up (y down coords) = (sin, -cos); y-up: (sin, cos)
    up = (round(math.sin(math.radians(ang)), 6), round(math.cos(math.radians(ang)), 6))
    return dict(letter=top[1], angle=ang, up=up, score=round(float(top[0]), 3), second=round(float(second), 3),
                second_other_letter=round(float(other_letter), 3),
                glyph_only_letter=g_best[1], glyph_only_score=round(float(g_best[0]), 3),
                glyph_only_margin=round(float(g_best[0] - g_second), 3),
                glyph_h=_glyph_height(img, ctr, ang))


def _glyph_only(img, ctr, ang, letter):
    """Second stage at the chosen turn: compare the capital alone (underline rows removed) with all 26 templates."""
    r = np.asarray(img.rotate(ang, resample=Image.BICUBIC, center=ctr), float)
    x0, y0 = int(round(ctr[0])) - SZ // 2, int(round(ctr[1])) - SZ // 2
    win = np.clip(r[y0:y0 + SZ, x0:x0 + SZ], 0, 1)
    cap = caps()["cap_height"] * FONT_PX / caps()["units_per_em"]
    top = -(cap + UL_GAP + UL_W) / 2
    cut = int(round(SZ / 2 + top + cap + UL_GAP / 2))      # rows from here on belong to the underline
    gy, gx = np.mgrid[0:SZ, 0:SZ]
    # locate the real shift with the group template of the chosen letter
    t0 = group_template(letter)
    tc = np.array([(t0 * gy).sum(), (t0 * gx).sum()]) / t0.sum()
    wc = np.array([(win * gy).sum(), (win * gx).sum()]) / max(win.sum(), 1e-9)
    sh = np.round(tc - wc).astype(int)
    res = []
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        t = group_template(ch).copy()
        t[cut:] = 0
        bs = -1.0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                w2 = np.roll(np.roll(win, sh[0] + dy, axis=0), sh[1] + dx, axis=1).copy()
                w2[cut:] = 0
                sc = 2 * np.minimum(w2, t).sum() / (w2.sum() + t.sum())
                bs = max(bs, sc)
        res.append((bs, ch))
    res.sort(reverse=True)
    return res[0], res[1][0]


def _glyph_height(img, ctr, ang):
    r = np.asarray(img.rotate(ang, resample=Image.BICUBIC, center=ctr), float)
    x0, y0 = int(round(ctr[0])) - SZ // 2, int(round(ctr[1])) - SZ // 2
    win = r[y0:y0 + SZ, x0:x0 + SZ]
    rows = np.where((win > 0.5).any(axis=1))[0]
    if not len(rows):
        return 0
    runs, s = [], rows[0]
    for a, b in zip(rows[:-1], rows[1:]):
        if b != a + 1:
            runs.append((s, a))
            s = b
    runs.append((s, rows[-1]))
    if len(runs) < 2:
        return 0
    g0, g1 = runs[0][0], runs[-2][1]
    return int(g1 - g0 + 1)
