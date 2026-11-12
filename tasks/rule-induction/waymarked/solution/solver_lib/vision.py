"""Read the Waymarked page from pixels.

Nothing here knows the puzzle data: grids are found from their thick black frames, cell counts from the
grey ruling, signs from black ink inside each cell, marks from mid-grey rings / light-grey diagonals and
letters by matching generic DejaVu capital outlines (font_caps.json).
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

INK = 60          # black ink (#111) after anti-aliasing core
SOFT_INK = 72     # component threshold: below the #555 ring core (~85)
RING_LO, RING_HI = 68, 110      # #555 ring
STRIKE_LO, STRIKE_HI = 128, 178  # #999 strike
DIRS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}


class ReadError(Exception):
    pass


def load(path):
    im = Image.open(path)
    if im.mode not in ("RGB", "RGBA", "L"):
        im = im.convert("RGB")
    rgb = np.asarray(im.convert("RGB")).astype(np.int16)
    gray = rgb.mean(axis=2)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    return gray, chroma


def _runs(v):
    out, start = [], None
    for i, x in enumerate(v):
        if x and start is None:
            start = i
        elif not x and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(v) - 1))
    return out


def _group(idx, gap=1):
    groups = []
    for i in idx:
        if groups and i - groups[-1][-1] <= gap:
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def find_frames(gray, min_len=300):
    """Square thick-black frames: pairs of long horizontal bars joined by long vertical bars."""
    dark = gray < INK
    bars = {}
    for y in range(dark.shape[0]):
        for x0, x1 in _runs(dark[y]):
            if x1 - x0 + 1 >= min_len:
                bars.setdefault((x0 // 4, x1 // 4), []).append((y, x0, x1))
    horiz = []
    for rows in bars.values():
        for grp in _group([r[0] for r in rows]):
            sel = [r for r in rows if grp[0] <= r[0] <= grp[-1]]
            x0 = min(r[1] for r in sel); x1 = max(r[2] for r in sel)
            horiz.append((grp[0], grp[-1], x0, x1))
    horiz.sort()
    frames = []
    used = set()
    for i, (t0, t1, x0, x1) in enumerate(horiz):
        if i in used:
            continue
        for j in range(i + 1, len(horiz)):
            b0, b1, u0, u1 = horiz[j]
            if j in used or abs(u0 - x0) > 3 or abs(u1 - x1) > 3:
                continue
            # vertical sides must be solid dark columns
            left = dark[t1:b0, x0:x0 + 8].all(axis=0).any()
            right = dark[t1:b0, x1 - 7:x1 + 1].all(axis=0).any()
            if left and right:
                lw = int(dark[t1:b0, x0:x0 + 12].all(axis=0).sum())
                rw = int(dark[t1:b0, x1 - 11:x1 + 1].all(axis=0).sum())
                frames.append({"outer": (x0, t0, x1, b1),
                               "inner": (x0 + lw, t1 + 1, x1 - rw, b0 - 1)})
                used.update((i, j))
                break
    return frames


def grid_lines(gray, frame):
    """Interior ruling: columns/rows that are non-white along almost the whole interior."""
    x0, y0, x1, y1 = frame["inner"]
    sub = gray[y0:y1 + 1, x0:x1 + 1]
    nonwhite = sub < 235
    vcols = np.where(nonwhite.mean(axis=0) > 0.8)[0]
    hrows = np.where(nonwhite.mean(axis=1) > 0.8)[0]
    W_, H_ = sub.shape[1], sub.shape[0]
    vl = [x0 + int(np.mean(g)) for g in _group(list(vcols)) if g[0] > 2 and g[-1] < W_ - 3]
    hl = [y0 + int(np.mean(g)) for g in _group(list(hrows)) if g[0] > 2 and g[-1] < H_ - 3]
    xs = [x0 - 0.5] + vl + [x1 + 0.5]
    ys = [y0 - 0.5] + hl + [y1 + 0.5]
    widths = np.diff(xs); heights = np.diff(ys)
    if len(vl) != len(hl) or widths.max() - widths.min() > 4 or heights.max() - heights.min() > 4:
        raise ReadError(f"irregular ruling in frame {frame['outer']}: {len(vl)} v-lines, {len(hl)} h-lines")
    return xs, ys


def cell_boxes(xs, ys):
    n = len(xs) - 1
    return {(r, c): (int(math.ceil(xs[c])) + 3, int(math.ceil(ys[r])) + 3, int(xs[c + 1]) - 3, int(ys[r + 1]) - 3)
            for r in range(n) for c in range(n)}


def _components(mask):
    """8-connected components; returns list of arrays of (y, x)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys, xs):
        if seen[sy, sx]:
            continue
        stack = [(sy, sx)]; seen[sy, sx] = True; pts = []
        while stack:
            y, x = stack.pop(); pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; stack.append((yy, xx))
        comps.append(np.array(pts))
    return comps


def parse_arrow(mask):
    """mask: bool array of one arrow component (cropped). Returns (direction, chevrons, detail)."""
    ys, xs = np.nonzero(mask)
    h = ys.max() - ys.min() + 1; w = xs.max() - xs.min() + 1
    vertical = h > w
    m = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if vertical:
        m = m.T  # axis now runs along columns (left = top of page)
    L = m.shape[1]
    prof = [_runs(m[:, i]) for i in range(L)]
    shaft = int(np.median([r[0][1] - r[0][0] + 1 for r in prof if len(r) == 1]))
    multi = [i for i, r in enumerate(prof) if len(r) >= 2]
    chev_groups = _group(multi)
    # head: a run of columns at one extreme end whose single run is wide (filled triangle)
    def head_len(cols):
        k = 0
        for i in cols:
            r = prof[i]
            if len(r) == 1 and r[0][1] - r[0][0] + 1 >= shaft + 3:
                k += 1
            elif len(r) == 1 and k == 0 and r[0][1] - r[0][0] + 1 < shaft + 3:
                continue  # the very tip is narrow
            else:
                break
        return k
    end_lo = head_len(range(0, min(L, 20)))
    end_hi = head_len(range(L - 1, max(-1, L - 21), -1))
    if not chev_groups:
        raise ReadError("arrow without chevrons")
    chev_c = np.mean([np.mean(g) for g in chev_groups])
    tail_at_lo = chev_c < L / 2
    head_cols = end_hi if tail_at_lo else end_lo
    other = end_lo if tail_at_lo else end_hi
    if head_cols < 4 or other >= 4:
        raise ReadError(f"arrowhead not found cleanly (head {head_cols}, other end {other})")
    # the outermost chevron sits at the tail end; chevrons are evenly spaced and clear of the head
    if (chev_groups[0][0] > 2) if tail_at_lo else (chev_groups[-1][-1] < L - 3):
        raise ReadError("tail end carries no chevron")
    starts = [g[0] for g in chev_groups]
    if len(starts) > 2 and max(np.diff(starts)) - min(np.diff(starts)) > 3:
        raise ReadError("unevenly spaced chevrons")
    head_zone = range(L - head_cols - 2, L) if tail_at_lo else range(0, head_cols + 2)
    if any(i in head_zone for g in chev_groups for i in g):
        raise ReadError("chevron inside the arrowhead")
    # shaft continuity: every column from first chevron to head has ink on the centre line
    centre = int(np.median([(r[0][0] + r[0][1]) / 2 for r in prof if len(r) == 1]))
    span = range(chev_groups[0][0], L) if tail_at_lo else range(0, chev_groups[-1][-1] + 1)
    gaps = [i for i in span if not m[max(0, centre - 1):centre + 2, i].any()]
    first_apex = chev_groups[0][-1] + 1 if tail_at_lo else chev_groups[-1][0] - 1
    gaps = [i for i in gaps if (i > first_apex if tail_at_lo else i < first_apex)]
    if gaps:
        raise ReadError(f"broken shaft ({len(gaps)} empty columns)")
    if vertical:
        d = "D" if tail_at_lo else "U"
    else:
        d = "R" if tail_at_lo else "L"
    return d, len(chev_groups), {"length": int(L), "shaft": shaft, "head_cols": int(head_cols)}


def ring_present(gray, box):
    x0, y0, x1, y1 = box
    sub = gray[y0 - 3:y1 + 4, x0 - 3:x1 + 4]
    cy = (sub.shape[0] - 1) / 2; cx = (sub.shape[1] - 1) / 2
    size = sub.shape[0]
    yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
    rr = np.hypot(yy - cy, xx - cx)
    ringpx = (sub >= RING_LO) & (sub <= RING_HI) & (rr > 0.36 * size) & (rr < 0.5 * size)
    ang = np.arctan2(yy[ringpx] - cy, xx[ringpx] - cx)
    bins = np.unique(((ang + math.pi) / (2 * math.pi) * 36).astype(int) % 36)
    return len(bins) / 36.0


def strike_present(gray, box, black):
    x0, y0, x1, y1 = box
    sub = gray[y0:y1 + 1, x0:x1 + 1]
    near_black = np.zeros_like(black[y0:y1 + 1, x0:x1 + 1])
    b = black[y0:y1 + 1, x0:x1 + 1]
    # ignore anti-aliased halo of black ink
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            near_black |= np.roll(np.roll(b, dy, 0), dx, 1)
    pts = np.argwhere((sub >= STRIKE_LO) & (sub <= STRIKE_HI) & ~near_black)
    if len(pts) < 10:
        return 0, 0
    s = pts[:, 0] + pts[:, 1]          # lower-left to upper-right: y + x constant
    best, best_n, span = None, 0, 0
    for v in range(int(s.min()), int(s.max()) + 1):
        sel = np.abs(s - v) <= 1
        if sel.sum() > best_n:
            best_n = int(sel.sum()); best = v
            span = int(pts[sel, 1].max() - pts[sel, 1].min())
    return best_n, span


def read_cell(gray, box, letters_allowed):
    x0, y0, x1, y1 = box
    blk = gray[y0:y1 + 1, x0:x1 + 1] < SOFT_INK
    comps = [c for c in _components(blk) if len(c) >= 4]
    if not comps:
        return None
    size = x1 - x0 + 1
    ext = lambda c: max(c[:, 0].max() - c[:, 0].min(), c[:, 1].max() - c[:, 1].min()) + 1
    comps.sort(key=lambda c: -ext(c))
    arrow = comps[0]
    if ext(arrow) < 0.3 * size:
        raise ReadError(f"ink in cell {box} but no arrow-sized shape")
    am = np.zeros_like(blk); am[arrow[:, 0], arrow[:, 1]] = True
    core = am & (gray[y0:y1 + 1, x0:x1 + 1] < INK)
    d, n, det = parse_arrow(core)
    rest = comps[1:]
    letter = None
    if rest:
        if not letters_allowed:
            raise ReadError(f"extra ink beside the arrow in example cell {box}")
        lm = np.zeros_like(blk)
        for c in rest:
            lm[c[:, 0], c[:, 1]] = True
        letter = lm
    abox = (x0 + int(arrow[:, 1].min()), y0 + int(arrow[:, 0].min()), x0 + int(arrow[:, 1].max()), y0 + int(arrow[:, 0].max()))
    return {"dir": d, "n": n, "letter_mask": letter, "letter_origin": (x0, y0), "arrow_box": abox, "detail": det}


# ---------------------------------------------------------------- letters
_FONT = json.loads((Path(__file__).with_name("font_caps.json")).read_text())
_TEMPLATES = {}


def _flatten(d):
    import re
    toks = re.findall(r"[MLQZ]|-?\d+(?:\.\d+)?", d)
    polys, cur, i, cmd, pen = [], [], 0, None, (0, 0)
    while i < len(toks):
        t = toks[i]
        if t in "MLQZ":
            cmd = t; i += 1
            if t == "Z":
                if cur: polys.append(cur)
                cur = []
            continue
        if cmd == "M":
            if cur: polys.append(cur)
            pen = (float(toks[i]), float(toks[i + 1])); cur = [pen]; i += 2; cmd = "L"
        elif cmd == "L":
            pen = (float(toks[i]), float(toks[i + 1])); cur.append(pen); i += 2
        elif cmd == "Q":
            cx, cy, ex, ey = map(float, toks[i:i + 4]); i += 4
            sx, sy = pen
            for k in range(1, 9):
                t_ = k / 8
                cur.append(((1 - t_) ** 2 * sx + 2 * (1 - t_) * t_ * cx + t_ ** 2 * ex,
                            (1 - t_) ** 2 * sy + 2 * (1 - t_) * t_ * cy + t_ ** 2 * ey))
            pen = (ex, ey)
        else:
            raise ValueError(cmd)
    if cur: polys.append(cur)
    return polys


def _raster(ch, cap=25, phase=(0.0, 0.0)):
    """Generic font raster at text size, including subpixel placement.

    Compare observed small letters with small-letter templates rather than a
    single idealized 160 px outline. Oversampling preserves thin middle strokes.
    All 26 letters receive the same size and phase bank; no puzzle data is used.
    """
    from PIL import ImageDraw
    polys = _flatten(_FONT["glyphs"][ch])
    ss = 8
    s = cap / 1493.0
    width = int(2200 * s) + 6
    height = int(2000 * s) + 6
    acc = np.zeros((height * ss, width * ss), dtype=bool)
    for poly in polys:
        im = Image.new("1", (width * ss, height * ss), 0)
        ImageDraw.Draw(im).polygon([
            ((2 + x * s + phase[0]) * ss,
             (height - 2 - (y + 500) * s + phase[1]) * ss)
            for x, y in poly], fill=1)
        acc ^= np.asarray(im, dtype=bool)
    coverage = np.asarray(Image.fromarray((acc * 255).astype(np.uint8)).resize(
        (width, height), Image.Resampling.BOX))
    return coverage > 255 - SOFT_INK


def _norm(mask, size=40):
    ys, xs = np.nonzero(mask)
    m = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = m.shape
    sc = (size - 2) / max(h, w)
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.BILINEAR)
    out = np.zeros((size, size)); a = np.asarray(im) / 255.0
    oy = (size - a.shape[0]) // 2; ox = (size - a.shape[1]) // 2
    out[oy:oy + a.shape[0], ox:ox + a.shape[1]] = a
    return out, w / h


def letter_templates():
    if not _TEMPLATES:
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            _TEMPLATES[ch] = [_norm(_raster(ch, cap, (dx, dy)))
                              for cap in (23, 24, 25, 26, 160)
                              for dx in (0.0, 0.25, 0.5, 0.75) for dy in (0.0, 0.25, 0.5, 0.75)]
    return _TEMPLATES


def classify_letter(mask):
    obs, asp = _norm(mask)
    scores = []
    # Absolute aspect error avoids amplifying a single raster pixel on narrow I/J glyphs.
    for ch, variants in letter_templates().items():
        diff = min(np.abs(obs - tpl).mean() + 0.5 * abs(asp - tasp)
                   for tpl, tasp in variants)
        scores.append((diff, ch))
    scores.sort()
    return scores[0][1], scores[0][0], scores[1][0] - scores[0][0], scores[1][1]


# ---------------------------------------------------------------- page
def read_page(path):
    gray, chroma = load(path)
    H, W = gray.shape
    black = gray < INK
    frames = find_frames(gray)
    if len(frames) < 2:
        raise ReadError(f"found {len(frames)} framed grids")
    frames.sort(key=lambda f: (f["outer"][1] // 50, f["outer"][0]))
    sizes = [f["outer"][2] - f["outer"][0] for f in frames]
    big = max(range(len(frames)), key=lambda i: sizes[i])
    target = frames[big]
    examples = [f for i, f in enumerate(frames) if i != big]
    if any(f["outer"][3] > target["outer"][1] for f in examples):
        raise ReadError("an example board is not above the lettered board")
    boards = []
    for kind, f in [("example", e) for e in examples] + [("target", target)]:
        xs, ys = grid_lines(gray, f)
        n = len(xs) - 1
        cells = cell_boxes(xs, ys)
        signs = {}
        for rc, box in cells.items():
            info = read_cell(gray, box, letters_allowed=(kind == "target"))
            ring = ring_present(gray, box)
            sn, sspan = strike_present(gray, box, black)
            if info is None:
                if ring > 0.3 or sn >= 20:
                    raise ReadError(f"mark without a sign in {kind} cell {rc}")
                continue
            info["ring_cover"] = round(ring, 3); info["strike_px"] = sn; info["strike_span"] = sspan
            ringed = ring >= 0.8
            struck = sn >= 30 and sspan >= 0.3 * (box[2] - box[0])
            if kind == "example":
                if ringed == struck:
                    raise ReadError(f"example sign at {rc} is {'both' if ringed else 'neither'} ringed and struck")
                info["mark"] = "ringed" if ringed else "struck"
            else:
                if ring > 0.3 or sn >= 20:
                    raise ReadError(f"target sign at {rc} carries a mark")
                if info["letter_mask"] is None:
                    raise ReadError(f"target sign at {rc} has no letter")
                ch, dist, margin, second = classify_letter(info["letter_mask"])
                if dist > 0.12 or margin < 0.03:
                    raise ReadError(f"letter at {rc} unreadable ({ch} {dist:.3f}, runner-up {second} +{margin:.3f})")
                lm = info["letter_mask"]; yy, xx = np.nonzero(lm)
                ox, oy = info["letter_origin"]
                info["letter"] = ch; info["letter_dist"] = round(float(dist), 4); info["letter_margin"] = round(float(margin), 4)
                info["letter_box"] = (ox + int(xx.min()), oy + int(yy.min()), ox + int(xx.max()), oy + int(yy.max()))
                info["letter_height"] = int(yy.max() - yy.min() + 1)
            info.pop("letter_mask", None); info.pop("letter_origin", None)
            signs[rc] = info
        boards.append({"kind": kind, "size": n, "outer": tuple(int(v) for v in f["outer"]),
                       "cell": float(np.mean(np.diff(xs))), "signs": signs})
    blanks = read_blanks(gray, target["outer"])
    return {"boards": boards, "blanks": blanks, "shape": (W, H), "gray": gray, "chroma": chroma}


def read_blanks(gray, tbox):
    """Short black underscores below the lettered board, grouped by the wider gaps."""
    y_start = tbox[3] + 5
    dark = gray[y_start:, :] < INK
    segs = []
    for y in range(dark.shape[0]):
        for x0, x1 in _runs(dark[y]):
            if 25 <= x1 - x0 + 1 <= 120:
                segs.append((y + y_start, x0, x1))
    if not segs:
        return []
    rows = _group(sorted({s[0] for s in segs}))
    line = max(rows, key=len) if rows else []
    ys = set(line)
    xs = sorted({(s[1], s[2]) for s in segs if s[0] in ys})
    merged = []
    for x0, x1 in xs:
        if merged and x0 <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], x1))
        else:
            merged.append((x0, x1))
    gaps = [merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1)]
    if not gaps:
        return [len(merged)]
    small = min(gaps)
    groups, k = [], 1
    for g in gaps:
        if g > 1.8 * small:
            groups.append(k); k = 1
        else:
            k += 1
    groups.append(k)
    return groups
