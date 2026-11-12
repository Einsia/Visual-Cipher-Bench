"""Pixel reading: locate grids, classify cells, recognise letters and pictograms by template matching.

Templates come from the bundled DejaVu outlines (glyphs.json) and pictogram outlines (icons.json) plus a drawn daisy;
nothing about this page's content is stored here.
"""
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
TOKEN = re.compile(r"[MLQCZ]|-?\d+(?:\.\d+)?")
NORM = 40


# ---------- outline rasteriser -------------------------------------------------
def contours(d):
    toks = TOKEN.findall(d)
    out, cur, i, pos = [], [], 0, (0.0, 0.0)

    def num(k):
        return float(toks[k])

    while i < len(toks):
        t = toks[i]
        if t == "M":
            if cur:
                out.append(cur)
            pos = (num(i + 1), num(i + 2))
            cur = [pos]
            i += 3
        elif t == "L":
            pos = (num(i + 1), num(i + 2))
            cur.append(pos)
            i += 3
        elif t == "Q":
            c = (num(i + 1), num(i + 2))
            e = (num(i + 3), num(i + 4))
            for s in range(1, 9):
                u = s / 8
                cur.append(((1 - u) ** 2 * pos[0] + 2 * (1 - u) * u * c[0] + u * u * e[0],
                            (1 - u) ** 2 * pos[1] + 2 * (1 - u) * u * c[1] + u * u * e[1]))
            pos = e
            i += 5
        elif t == "C":
            c1 = (num(i + 1), num(i + 2))
            c2 = (num(i + 3), num(i + 4))
            e = (num(i + 5), num(i + 6))
            for s in range(1, 9):
                u = s / 8
                cur.append(((1 - u) ** 3 * pos[0] + 3 * (1 - u) ** 2 * u * c1[0] + 3 * (1 - u) * u * u * c2[0] + u ** 3 * e[0],
                            (1 - u) ** 3 * pos[1] + 3 * (1 - u) ** 2 * u * c1[1] + 3 * (1 - u) * u * u * c2[1] + u ** 3 * e[1]))
            pos = e
            i += 7
        elif t == "Z":
            i += 1
        else:
            i += 1
    if cur:
        out.append(cur)
    return out


def raster(d, height=160):
    """Even-odd fill of a font-unit outline; returns a bool array cropped to its bbox."""
    cs = contours(d)
    pts = [p for c in cs for p in c]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = height / max(y1 - y0, 1e-6)
    W, H = int((x1 - x0) * s) + 3, int((y1 - y0) * s) + 3
    acc = None
    for c in cs:
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * s + 1, (y1 - y) * s + 1) for x, y in c], fill=1)
        acc = im if acc is None else ImageChops.logical_xor(acc, im)
    return np.array(acc, dtype=bool)


def daisy_mask(size=160):
    """Seven petals around a hollow centre, a stem and a leaf (the drawn flower pictogram)."""
    S = 4
    N = size * S
    im = Image.new("L", (N, N), 0)
    dr = ImageDraw.Draw(im)
    b = N * 0.8
    cx, cy = N / 2, N / 2
    hx, hy = cx, cy - 0.17 * b
    for k in range(7):
        a = math.radians(k * 360 / 7)
        pts = []
        for t in range(24):
            th = 2 * math.pi * t / 24
            ex, ey = 0.085 * b * math.cos(th), 0.15 * b * math.sin(th) - 0.19 * b
            pts.append((hx + ex * math.cos(a) - ey * math.sin(a), hy + ex * math.sin(a) + ey * math.cos(a)))
        dr.polygon(pts, fill=255)
    r = 0.1 * b
    dr.ellipse([hx - r, hy - r, hx + r, hy + r], fill=0, outline=255, width=max(1, int(0.035 * b)))
    dr.line([(hx, hy + 0.3 * b), (hx, cy + 0.5 * b)], fill=255, width=max(1, int(0.05 * b)))
    a = math.radians(-30)
    lx, ly = hx + 0.12 * b, cy + 0.3 * b
    pts = []
    for t in range(24):
        th = 2 * math.pi * t / 24
        ex, ey = 0.13 * b * math.cos(th), 0.055 * b * math.sin(th)
        pts.append((lx + ex * math.cos(a) - ey * math.sin(a), ly + ex * math.sin(a) + ey * math.cos(a)))
    dr.polygon(pts, fill=255)
    return np.array(im.resize((size, size), Image.LANCZOS)) > 128


# ---------- normalisation & matching --------------------------------------------
def normalise(mask):
    """Crop to the ink bbox, fit into NORM x NORM keeping aspect, centre, blur a little; unit-norm vector."""
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return None
    m = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = m.shape
    s = (NORM - 4) / max(h, w)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("L", (NORM, NORM), 0)
    canvas.paste(im, ((NORM - nw) // 2, (NORM - nh) // 2))
    a = np.array(canvas.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(1.2)), dtype=float)
    a -= a.mean()
    n = np.linalg.norm(a)
    return a / n if n > 0 else None


_TPL = None


def templates():
    global _TPL
    if _TPL is not None:
        return _TPL
    G = json.loads((HERE / "glyphs.json").read_text())["faces"]
    I = json.loads((HERE / "icons.json").read_text())["icons"]
    tpl = {"bold": {}, "reg": {}, "icon": {}}
    for face, key in (("sans-bold", "bold"), ("sans", "reg")):
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            tpl[key][ch] = normalise(raster(G[face]["glyphs"][ch]["d"]))
    for name, ic in I.items():
        if name == "flower":
            continue  # the DejaVu U+2698 glyph is not what the page draws; the drawn daisy stands in
        tpl["icon"][name] = normalise(raster(ic["d"]))
    tpl["icon"]["daisy"] = normalise(daisy_mask())
    _TPL = tpl
    return tpl


def classify_mask(mask, kinds=("bold", "reg", "icon")):
    v = normalise(mask)
    if v is None:
        return None, 0.0, 0.0
    best = []
    tpl = templates()
    for kind in kinds:
        for name, t in tpl[kind].items():
            best.append((float((v * t).sum()), kind, name))
    best.sort(reverse=True)
    top = best[0]
    second = next((b for b in best[1:] if (b[1], b[2]) != (top[1], top[2]) and b[2] != top[2]), (0, None, None))
    return (top[1], top[2]), top[0], top[0] - second[0]


# ---------- page analysis ---------------------------------------------------------
def load_gray(path):
    return np.array(Image.open(path).convert("L"), dtype=np.int16)


def components(mask, min_size=0):
    """8-connected components of a bool mask; returns list of (bbox x0,y0,x1,y1, count)."""
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    coords = np.argwhere(mask)
    for y, x in coords:
        if seen[y, x]:
            continue
        st = [(y, x)]
        seen[y, x] = True
        x0 = x1 = x
        y0 = y1 = y
        n = 0
        while st:
            cy, cx = st.pop()
            n += 1
            if cx < x0: x0 = cx
            if cx > x1: x1 = cx
            if cy < y0: y0 = cy
            if cy > y1: y1 = cy
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        st.append((ny, nx))
        if n >= min_size:
            out.append((int(x0), int(y0), int(x1), int(y1), n))
    return out


def find_grids(g):
    """Grid boxes = bbox of the big black outline components (white-region outline, 4 px)."""
    dark = g < 80
    comps = components(dark, min_size=800)
    grids = []
    for x0, y0, x1, y1, n in comps:
        if x1 - x0 >= 300 and y1 - y0 >= 300:
            grids.append((x0 + 2, y0 + 2, x1 - 2, y1 - 2))
    grids.sort(key=lambda b: (b[1], b[0]))
    return grids


def pitch_for(g, box):
    """Pick the cell count N (so pitch = size/N) whose multiples carry cell-boundary lines."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    sub = g[y0 - 2:y1 + 3, x0 - 2:x1 + 3]
    line = (sub < 200)
    vprof = line.sum(0)
    hprof = line.sum(1)
    best = None
    for N in range(3, 16):
        P = w / N
        if not (60 <= P <= 140):
            continue
        M = h / P
        if abs(M - round(M)) * P > 3:
            continue
        M = int(round(M))
        s = 0.0
        cnt = 0
        for k in range(1, N):
            xx = int(round(2 + k * P))
            s += vprof[max(0, xx - 1):xx + 2].max()
            cnt += 1
        for k in range(1, M):
            yy = int(round(2 + k * P))
            s += hprof[max(0, yy - 1):yy + 2].max()
            cnt += 1
        sc = s / max(cnt, 1)
        if best is None or sc > best[0]:
            best = (sc, N, M, P)
    if best is None:
        raise ValueError("cannot infer cell pitch")
    return best[1], best[2], best[3]


def cell_box(box, P, r, c, inset=0):
    x0, y0 = box[0], box[1]
    return (int(round(x0 + c * P)) + inset, int(round(y0 + r * P)) + inset,
            int(round(x0 + (c + 1) * P)) - inset, int(round(y0 + (r + 1) * P)) - inset)


def read_cell(g, box, P, r, c):
    """Return dict(kind=block|empty|circle|letter|icon|ringed_letter|other, ...)."""
    x0, y0, x1, y1 = cell_box(box, P, r, c, inset=int(round(0.08 * P)))
    sub = g[y0:y1, x0:x1]
    grey = float((np.abs(sub - 217) <= 4).mean())
    if grey > 0.97:
        return {"kind": "block"}
    if grey > 0.02:
        return {"kind": "anomaly", "why": "grey block with ink or partial block", "grey": grey}
    ink = sub < 175
    n = int(ink.sum())
    h, w = sub.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    d = np.hypot(yy - cy, xx - cx)
    ang = (np.arctan2(yy - cy, xx - cx) + math.pi) / (2 * math.pi)
    # a ring needs ink all round an annulus whose radius is about 0.4 pitch
    band = (d >= 0.32 * P) & (d <= 0.43 * P) & ink
    bins = np.zeros(36, dtype=bool)
    bins[np.minimum((ang[band] * 36).astype(int), 35)] = True
    ring = int(bins.sum()) >= 35
    inner = ink & (d < 0.30 * P)
    if ring:
        if inner.sum() < 12:
            return {"kind": "circle"}
        cl, sc, mg = classify_mask(inner, kinds=("reg", "bold"))
        return {"kind": "ringed_letter", "cls": cl, "score": sc, "margin": mg}
    if n < 12:
        return {"kind": "empty"}
    dark = sub < 140
    cl, sc, mg = classify_mask(dark)
    if cl is None:
        return {"kind": "empty"}
    if sc < 0.80:
        return {"kind": "other", "cls": cl, "score": sc, "margin": mg, "ink": n}
    kind = "icon" if cl[0] == "icon" else "letter"
    return {"kind": kind, "cls": cl, "score": sc, "margin": mg, "ink": n}


def read_grid(g, box):
    N, M, P = pitch_for(g, box)
    cells = {}
    for r in range(M):
        for c in range(N):
            cells[(r, c)] = read_cell(g, box, P, r, c)
    return {"box": box, "cols": N, "rows": M, "pitch": P, "cells": cells}


def read_blanks(g, box_below):
    """Underlined answer blanks inside box_below=(x0,y0,x1,y1): returns list of dict(x, y, letter|None)."""
    x0, y0, x1, y1 = box_below
    sub = g[y0:y1, x0:x1] < 80
    rows = np.where(sub.sum(1) >= 40)[0]
    out = []
    if len(rows) == 0:
        return out
    ly = int(rows[np.argmax(sub.sum(1)[rows])])
    line = sub[max(0, ly - 1):ly + 2].any(0)
    xs = np.where(line)[0]
    runs = []
    s = p = None
    for x in xs:
        if s is None:
            s = p = x
        elif x == p + 1:
            p = x
        else:
            runs.append((s, p))
            s = p = x
    if s is not None:
        runs.append((s, p))
    for a, b in runs:
        if b - a < 30:
            continue
        cx = x0 + (a + b) // 2
        out.append({"cx": cx, "line_y": y0 + ly, "width": b - a + 1})
    for bl in out:
        ww = int(bl["width"])
        top = max(0, bl["line_y"] - ww - 6)
        win = g[top:bl["line_y"] - 2, bl["cx"] - ww // 2:bl["cx"] + ww // 2 + 1]
        ink = win < 175
        ys, xs = np.where(ink)
        bl["ring"] = False
        bl["letter"] = None
        bl["ink"] = 0
        if len(ys) < 40:
            continue
        dia = max(ys.max() - ys.min(), xs.max() - xs.min()) + 1
        cyy, cxx = (ys.max() + ys.min()) / 2, (xs.max() + xs.min()) / 2
        hh, wd = win.shape
        yy, xx = np.mgrid[0:hh, 0:wd]
        d = np.hypot(yy - cyy, xx - cxx)
        band = ink & (d >= 0.40 * dia) & (d <= 0.58 * dia)
        bins = np.zeros(36, dtype=bool)
        ang = (np.arctan2(yy - cyy, xx - cxx) + math.pi) / (2 * math.pi)
        bins[np.minimum((ang[band] * 36).astype(int), 35)] = True
        bl["ring"] = int(bins.sum()) >= 35 and 30 <= dia <= 80
        inner = (win < 140) & (d < 0.32 * dia)
        bl["ink"] = int(inner.sum())
        bl["diameter"] = int(dia)
        if inner.sum() >= 12:
            cl, sc, mg = classify_mask(inner, kinds=("reg", "bold"))
            bl["letter"] = cl[1] if (cl and sc >= 0.8) else "?"
            bl["score"] = sc
    for bl in out:
        bl["cx"] = int(bl["cx"]); bl["line_y"] = int(bl["line_y"]); bl["width"] = int(bl["width"])
    return out


def read_stencils(g):
    """Find faint rectangular lattices; recover pitch, letters and relative positions.

    No expected stencil contents or bounding boxes. Main crossword outlines are black,
    and their short gray interior edges cannot pass the full rectangular-lattice check.
    """
    plates=[]
    for x0,y0,x1,y1,n in components((g>=145)&(g<=230),min_size=200):
        w,h=x1-x0+1,y1-y0+1
        if min(w,h)<35 or max(w,h)>450:
            continue
        sub=g[y0:y1+1,x0:x1+1]
        mask=(sub>=145)&(sub<=230)
        def centres(prof):
            idx=np.where(prof>.80)[0]
            runs=[]
            for i in idx:
                if not runs or i>runs[-1][-1]+1:runs.append([i])
                else:runs[-1].append(i)
            return [float(np.mean(v)) for v in runs]
        xs=centres(mask.mean(0));ys=centres(mask.mean(1))
        if len(xs)<2 or len(ys)<2:
            continue
        if xs[0]>2 or ys[0]>2 or w-1-xs[-1]>2 or h-1-ys[-1]>2:
            continue
        gaps=np.array([*np.diff(xs),*np.diff(ys)])
        pitch=float(np.median(gaps))
        if not (35<=pitch<=58) or np.max(np.abs(gaps-pitch))>2:
            continue
        points=[];scores=[];bad=False
        for r in range(len(ys)-1):
            for c in range(len(xs)-1):
                a=int(round(x0+xs[c]+.14*pitch));b=int(round(x0+xs[c+1]-.14*pitch))
                t=int(round(y0+ys[r]+.12*pitch));u=int(round(y0+ys[r+1]-.12*pitch))
                ink=g[t:u,a:b]<140
                if ink.sum()<12:continue
                cl,score,margin=classify_mask(ink,kinds=('bold',))
                if score<.85 or margin<.03:
                    bad=True
                points.append([r,c,cl[1]])
                scores.append({'cell':[r,c],'letter':cl[1],'score':float(score),'margin':float(margin),
                               'ink_height':int(np.where(ink)[0].max()-np.where(ink)[0].min()+1)})
        if len(points)>=2:
            plates.append({'box':[x0,y0,x1,y1],'rows':len(ys)-1,'cols':len(xs)-1,
                           'pitch':pitch,'letters':points,'scores':scores,'readable':not bad})
    return sorted(plates,key=lambda p:(p['box'][1],p['box'][0]))
