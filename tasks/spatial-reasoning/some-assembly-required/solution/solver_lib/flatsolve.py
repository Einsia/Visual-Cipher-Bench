"""Pixel-driven solver: parse the house, the worked example, the four nets and the blanks from the PNG, fold every net
(fold direction unknown), pack the blocks into the house, carry the letters through, read the upright blank-shaped wall."""
import collections
import itertools
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pixparse as P  # noqa: E402
import netparse as N  # noqa: E402
from flatpack import solid_from_faces, solid_of, exact_cover, transform_solid, surface, ROTS, MIRROR  # noqa: E402
from foldlatent import fold as fold_fast  # noqa: E402

ANGLES_TYPED = {"mountain": [45, 90, 135], "valley": [225, 270], "flat": [180], "latent": [45,90,135,180,225,270,315], "fold": [45, 90, 135, 225, 270, 315]}
ANGLES_FREE = {"mountain": [45, 90, 135, 225, 270], "valley": [45, 90, 135, 225, 270], "flat": [180], "latent": [45,90,135,180,225,270,315], "fold": [45, 90, 135, 225, 270, 315]}


def load_words():
    return set(w.strip() for w in (HERE / "english_words.txt").read_text().splitlines() if w.strip())


# ------------------------------------------------------------------ page parsing
def parse_page(img_path):
    rgb, gray = P.load_gray(img_path)
    comps = P.find_net_components(gray)
    parsed, others = [], []
    # Measure the common printed unit from repeated foot-bar spacing in the
    # answer diagram, then check the paper perimeter against that same scale.
    lab, count = P.label(gray[1880:] < 150, 8)
    bars = [v for v in P.comp_stats(lab, count).values()
            if 18 <= v['x1']-v['x0']+1 <= 40 and v['y1']-v['y0']+1 <= 6]
    xs = sorted(set(round(v['cx'], 2) for v in bars))
    if len(xs)<2:raise ValueError('no repeated unit in answer drawing')
    unit=float(np.median(np.diff(xs)))
    for b in comps:
        x0,y0,x1,y1=b[:4]
        region=gray[y0:y1+1,x0:x1+1]
        # The solid drawings have large grey filled planes. Paper has only ink.
        fills=((region==217)|(region==238)).sum()
        if fills>500 or y0>1880:
            others.append(b)
        else:
            parsed.append((b,[dict(outline_box=b,unit_hint=unit)]))
    return rgb, gray, parsed, others


def build_net(gray, faces_px, unit):
    import outlineparse
    box=faces_px[0]['outline_box']
    subdivisions,evidence=outlineparse.recover(gray,box,unit)
    valid=[];rejected=[]
    for index,fs in enumerate(subdivisions):
        net,err=N.build_net(gray,fs,unit)
        if net is None:
            rejected.append(dict(subdivision=index,reason=err))
            continue
        valid.append(net)
    if len(valid)!=1:
        return None,'expected one edge-to-edge net subdivision, found %d'%len(valid)
    net=valid[0]
    evidence.update(edge_to_edge_subdivisions=len(valid),rejected=rejected,
                    tiles=len(net['faces']),viable_grids=1,box=box[:4])
    net['panel_recovery']=[evidence]
    for f in net['faces']:
        poly_px=[N.px_of(p,unit) for p in f['fit_poly']]
        L=N.face_letter(gray,poly_px,inset=5.)
        f['letter_info']=L
        f['letter']=None if L is None else L['letter']
        f['up']=None if L is None else L['up']
        f['center_px']=tuple(float(v) for v in np.mean(poly_px,axis=0))
    return net,None


def net_is_tree(net):
    n = len(net["faces"])
    return len(net["links"]) == n - 1 and all(l["kind"] in ANGLES_TYPED for l in net["links"])


def fold_net(net, box=None, typed=True):
    """Exhaustive fold; typed=True uses the drawn mountain / valley kinds, else only flat vs fold with unknown direction."""
    ANG = ANGLES_TYPED if typed else ANGLES_FREE
    faces = net["faces"]
    n = len(faces)
    root = net["root"]
    polys = [list(f["poly"]) for f in faces]
    adj = collections.defaultdict(list)
    for (a, b, e, kind) in net["glued"]:
        adj[a].append((b, e, kind))
        adj[b].append((a, e, kind))
    # A tree-centre square gives early bounds on all branches. This is computed
    # from PNG adjacency, independent of any stored face order or root.
    choices = []
    for candidate, face in enumerate(faces):
        if face["kind"] != "sq":
            continue
        queue = [candidate]
        distances = {candidate: 0}
        for parent in queue:
            for child, _, _ in adj[parent]:
                if child not in distances:
                    distances[child] = distances[parent] + 1
                    queue.append(child)
        choices.append((max(distances.values()), sum(distances.values()), candidate))
    root = min(choices)[2]
    order = {root: 0}
    seq = [root]
    links = []
    for a in seq:
        for b, e, kind in adj[a]:
            if b not in order:
                order[b] = len(order)
                seq.append(b)
                links.append((a, b, e, kind))
    new_idx = {old: k for k, old in enumerate(seq)}
    fpolys = [polys[old] for old in seq]
    flinks = [(new_idx[a], new_idx[b], e) for a, b, e, k in links]
    opts = [ANG[k] for a, b, e, k in links]
    sols, nodes = fold_fast(fpolys, flinks, opts, box=box)
    out = []
    for s in sols:
        pts = [[np.array(p, float) * 2 for p in s[j]] for j in range(n)]
        cells = solid_from_faces([[tuple(p) for p in f] for f in pts])
        if cells is None:
            continue
        mn = np.round(np.array([p for f in pts for p in f])).min(axis=0)
        npts = [[np.round(p) - mn for p in f] for f in pts]
        ups, letters = [], []
        for jn, old in enumerate(seq):
            f = faces[old]
            letters.append(f["letter"])
            if not f["letter"]:
                ups.append(None)
                continue
            q = [np.array(x, float) for x in fpolys[jn][:3]]
            p = [np.array(x, float) for x in s[jn][:3]]
            Q = np.array([q[1] - q[0], q[2] - q[0]]).T
            Pm = np.array([p[1] - p[0], p[2] - p[0]]).T
            Lm = Pm @ np.linalg.inv(Q)
            u3 = Lm @ np.array(f["up"], float)
            ups.append(np.round(u3 / np.linalg.norm(u3), 4) + 0.0)
        centers = [tuple(int(round(v)) for v in faces[old]["center_px"]) for old in seq]
        out.append({"cells": cells, "faces": npts, "ups": ups, "letters": letters, "centers": centers,
                    "concave": _count_concave(npts, flinks, links)})
    return out, nodes


def _count_concave(npts, flinks, links):
    c = 0
    for (i, j, e), (a, b, ee, kind) in zip(flinks, links):
        if kind == "flat":
            continue
        Pi, Pj = [np.array(p) for p in npts[i]], [np.array(p) for p in npts[j]]
        ni = np.cross(Pi[1] - Pi[0], Pi[2] - Pi[0])
        c += int(np.dot(np.mean(Pj, 0) - np.mean(Pi, 0), ni) > 1e-9)
    return c


FREE_ROUTE = False      # validate.py switches this on (direction-unknown route as extra evidence)


def _tilted(face):
    """True when the face has no edge along a page axis (it lies at 45 degrees)."""
    Q = face["poly"]
    n = len(Q)
    for i in range(n):
        dx, dy = Q[(i + 1) % n][0] - Q[i][0], Q[(i + 1) % n][1] - Q[i][1]
        if abs(dx) < 1e-6 or abs(dy) < 1e-6:
            return False
    return True


def parse_blanks(gray, y_min=1880, boxes=()):
    """Answer blanks = an empty grid of touching grey-hairline cells, each with one short foot bar (underline).
    Rows x columns come from the foot bars; the hairline grid must have the same cell count (cells of equal size)."""
    ink = gray[y_min:] < 200
    lab, n = P.label(ink, 8)
    st = P.comp_stats(lab, n)
    bars, grids = [], []
    for s in st.values():
        w, h = s["x1"] - s["x0"] + 1, s["y1"] - s["y0"] + 1
        if 18 <= w <= 40 and h <= 6:
            bars.append(s)
        elif w >= 100 and h >= 60:
            grids.append(s)
    rows = collections.defaultdict(list)
    for s in bars:
        rows[round((s["y0"] + y_min) / 20)].append(s["x0"])
    cnt = [len(v) for k, v in sorted(rows.items())]
    widths = sorted({s["x1"] - s["x0"] + 1 for s in bars})
    grid_ok = False
    if len(grids) == 1 and rows and len(set(cnt)) == 1:
        g = grids[0]
        cw = (g["x1"] - g["x0"]) / cnt[0]
        ch = (g["y1"] - g["y0"]) / len(rows)
        # one foot bar per cell, inside its own cell
        xs = sorted(s["cx"] for s in bars)
        grid_ok = bool(abs(cw - ch) < 4 and all(g["x0"] <= x <= g["x1"] for x in xs))
    return dict(rows=len(rows), per_row=cnt, bars=len(bars), bar_widths=widths, grid_ok=grid_ok, grids=len(grids))


def place_points(cells, M, off):
    cc = np.array([M @ (np.array(c) * 2 + 1) for c in cells])
    m = cc.min(axis=0)
    return lambda p: M @ p - m + 1 + 2 * np.array(off)


def measure_unit(parsed):
    units=[fs[0]['unit_hint'] for _,fs in parsed]
    if not units or max(units)-min(units)>.1:raise ValueError('inconsistent drawing units')
    return float(np.median(units))


def solve(img_path, log=None):
    log = log or (lambda *a, **k: None)
    T0 = time.perf_counter()
    rgb, gray, parsed, others = parse_page(img_path)
    boxes = [b for b, _ in parsed]
    # unit: per-component shortest-edge estimate; the 3-D house is the outlier (its faces are not unit nets)
    unit = measure_unit(parsed)
    non_nets = list(others)
    net_parsed = list(parsed)
    nets_all = []
    build_errors = []
    for b, faces in net_parsed:
        net, err = build_net(gray, faces, unit)
        if net is None or not net_is_tree(net):
            non_nets.append(b)
            build_errors.append((b[:4], err))
            continue
        net["box"] = b
        nets_all.append(net)
    if len(nets_all) != 5:
        return dict(answer=None, error=f"expected 5 intact nets (4 + worked example), found {len(nets_all)}",
                    nets_found=len(nets_all), parsed_components=len(parsed), build_errors=build_errors)
    # house = the largest dark component that is not a net
    non_nets.sort(key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    hb = non_nets[0]
    res, hinfo = P.fit_house(gray, hb)
    best, second = res[0], res[1]
    cells = best[4]
    BOX = tuple(sorted(int(v) for v in (np.array(list(cells)).max(0) - np.array(list(cells)).min(0) + 1)))
    # worked example = the net above all others; the four puzzle nets follow in page order
    nets_all.sort(key=lambda n: (round(((n["box"][1] + n["box"][3]) / 2) / 350), n["box"][0]))
    example, nets = nets_all[0], nets_all[1:]
    blanks = parse_blanks(gray, boxes=[n["box"][:4] for n in nets_all] + [hb[:4]])
    issues, tri_letters, scores, heights, go = [], 0, [], [], []
    for ni, nt in enumerate([example] + nets):
        for fi, f in enumerate(nt["faces"]):
            L = f["letter_info"]
            if L is None:
                if f["kind"] != "tri":
                    issues.append((ni, fi, "square or rectangle face without a printed letter"))
                continue
            if not L.get("letter"):
                issues.append((ni, fi, L.get("reason")))
                continue
            if f["kind"] == "tri":
                issues.append((ni, fi, "mark inside a blank triangle"))
                continue
            if L["score"] < 0.7 or L["glyph_only_letter"] != L["letter"] or L["glyph_only_score"] < 0.7:
                issues.append((ni, fi, "unreadable letter (score %.2f / glyph-only %s %.2f)" % (L["score"], L["glyph_only_letter"], L["glyph_only_score"])))
                continue
            if f["kind"] == "tri":
                tri_letters += 1
            scores.append((L["score"], L["score"] - L["second_other_letter"]))
            heights.append(L["glyph_h"])
            go.append((L["glyph_only_letter"] != L["letter"], L["glyph_only_margin"], L["angle"]))
    if issues:
        return dict(answer=None, error="unreadable marks inside faces", issues=issues)
    log("parsed", dict(unit=unit, nets=len(nets), house=best[3], box=BOX, blanks=blanks))
    report = dict(letters=len(scores), min_letter_score=round(float(min(a for a, b in scores)), 3),
                  min_letter_margin=round(float(min(b for a, b in scores)), 3), tri_letters=tri_letters,
                  min_glyph_h=int(min(heights)), max_glyph_h=int(max(heights)),
                  glyph_only_disagreements=int(sum(1 for a, b, c in go if a)),
                  min_glyph_only_margin=round(float(min(b for a, b, c in go)), 3),
                  letter_turns=dict(sorted(collections.Counter(c for a, b, c in go).items())),
                  nets_found=len(nets_all), unit=unit, house_tag=best[3], house_fit=[round(float(best[1]), 4), round(float(best[2]), 4)],
                  house_runner_up=[round(float(second[0]), 4), second[3]], box=BOX, blanks=blanks,
                  net_faces=[len(n["faces"]) for n in nets], example_faces=len(example["faces"]))
    report["panel_recovery"] = [dict(net=i+1, panels=n.get("panel_recovery", []),
        implicit_joins=[dict(faces=[l["i"], l["j"]], a_px=N.px_of(l["a"],unit),
                             b_px=N.px_of(l["b"],unit), pixels=l["stat"])
                        for l in n["links"] if l.get("implicit")]) for i,n in enumerate(nets)]
    # ---- example: folds uniquely into one wedge, F on the front face upright, G on top with its foot toward the front
    exs, exn = fold_net(example, box=None)
    ex_ok = False
    ex_info = {}
    if len(exs) == 1 and len(exs[0]["cells"]) == 1 and len(solid_of(exs[0]["cells"])) == 12:
        e = exs[0]
        letters = {l: u for l, u in zip(e["letters"], e["ups"]) if l}
        fp = {l: pts for l, pts in zip(e["letters"], e["faces"]) if l}
        ex_info = {"letters": sorted(letters)}
        ex_ok = _example_convention(e)
    report["example"] = dict(closed_foldings=len(exs), search_nodes=exn, convention_ok=bool(ex_ok), **ex_info)
    # ---- fold the four nets
    pieces_data = []
    rows = []
    for k, net in enumerate(nets):
        t = time.perf_counter()
        sols, nodes = fold_net(net, box=BOX, typed=True)
        t1 = time.perf_counter() - t
        t = time.perf_counter()
        kinds = collections.Counter(l["kind"] for l in net["links"])
        rows.append(dict(net=k + 1, faces=len(net["faces"]), creases=len(net["links"]), closed_foldings=len(sols),
                         nodes=nodes, seconds=round(t1, 2), crease_kinds=dict(kinds),
                         concave=[s["concave"] for s in sols], lettered=sum(1 for f in net["faces"] if f["letter"]),
                         tilted_faces=sum(1 for f in net["faces"] if _tilted(f))))
        if len(sols) == 1:
            pieces_data.append(sols[0])
        else:
            pieces_data.append(None)
        log("fold", rows[-1])
    report["folds"] = rows
    if not all(pieces_data):
        report.update(answer=None, error="a net did not fold into exactly one closed block")
        return report
    pieces = [solid_of(d["cells"]) for d in pieces_data]
    target = solid_of(cells)
    report["volumes"] = dict(pieces=[len(p) / 24 for p in pieces], house=len(target) / 24)
    sols, st = exact_cover(pieces, target, limit=50)
    if len(sols) >= 50:
        raise RuntimeError("packing cap reached; uniqueness unproved")
    report["packings"] = len(sols)
    report["placements"] = st["placements"]
    mirror_packings = 0
    mirror_by_mask = {}
    for mask in itertools.product([0, 1], repeat=len(pieces)):
        if not any(mask):
            continue
        ps = [transform_solid(p, MIRROR) if m else p for p, m in zip(pieces, mask)]
        s2, _ = exact_cover(ps, target, limit=2)
        mirror_packings += len(s2)
        mirror_by_mask["".join(map(str, mask))] = len(s2)
    report["mirror_packings"] = mirror_packings
    report["mirror_by_mask"] = mirror_by_mask
    # chirality of each block: does the mirrored block differ from every rotation of itself?
    report["chiral"] = [bool(all(transform_solid(transform_solid(p, MIRROR), M) != p for M in ROTS)) for p in pieces]
    if len(sols) < 1:
        report.update(answer=None, error="no packing")
        return report
    house_ext = {}
    for vs, n, typ, cell in surface(cells):
        house_ext[frozenset(vs)] = (n, typ)
    tcells = {x[0] for x in target}
    R_BL, C_BL = blanks["rows"], blanks["per_row"][0]
    # ---- per (piece, orientation variant): which house faces it covers and which letters it shows there
    variant_cache = {}

    def variants(i, placed):
        """Every rotation that puts piece i's solid exactly onto the placed sub-tetrahedra (self-symmetries)."""
        ck = (i, placed)
        if ck in variant_cache:
            return variant_cache[ck]
        out = []
        for M in ROTS:
            r = transform_solid(pieces[i], M)
            c0 = min(x[0] for x in r)
            for t in tcells:
                off = tuple(t[k] - c0[k] for k in range(3))
                p = frozenset((tuple(x[0][k] + off[k] for k in range(3)), x[1], x[2]) for x in r)
                if p == placed:
                    out.append((M, off))
        res = []
        for (M, off) in out:
            f = pieces_data[i]
            tf = place_points(f["cells"], M, off)
            ext, inter = {}, []
            for j, fp in enumerate(f["faces"]):
                key = frozenset(tuple(int(round(x)) for x in tf(p)) for p in fp)
                if key in house_ext:
                    ext[key] = None if f["ups"][j] is None else (f["letters"][j], np.round(M @ f["ups"][j], 6), i + 1, f["centers"][j])
                else:
                    inter.append(key)
            res.append((M, off, ext, inter))
        variant_cache[ck] = res
        return res

    def read_walls(letters_on):
        planes = collections.defaultdict(list)
        for key, (n, typ) in house_ext.items():
            pts = np.array([list(p) for p in key], float)
            planes[(tuple(n), float(np.round(np.dot(pts[0], n), 6)))].append((key, typ))
        walls = []
        for (n, d), items in sorted(planes.items()):
            if abs(n[2]) > 1e-9:
                continue
            nv = np.array(n)
            right = np.cross((0, 0, 1), nv)
            grid = {}
            for key, typ in items:
                if typ != "sq":
                    continue
                c = np.array([list(p) for p in key], float).mean(axis=0) / 2.0
                grid[(int(np.floor(c[2])), int(np.floor(np.dot(c, right))))] = key
            for (z0, u0) in grid:
                rc = [(z0 - r, u0 + c) for r in range(R_BL) for c in range(C_BL)]
                if not all(x in grid for x in rc):
                    continue
                L = [letters_on.get(grid[x]) for x in rc]
                if not all(L):
                    continue
                ups = [bool(np.allclose(x[1], (0, 0, 1))) for x in L]
                walls.append(dict(normal=[round(float(v), 3) for v in n], top_left=[z0, u0], text="".join(x[0] for x in L),
                                  upright=sum(ups), all_upright=all(ups), nets=sorted({x[2] for x in L}),
                                  cells=[(x[0], x[2], x[3], bool(np.allclose(x[1], (0, 0, 1)))) for x in L]))
        return walls

    n_asm, surface_ok_all = 0, True
    text_stats = collections.defaultdict(lambda: dict(count=0, upright_count=0, max_upright=0))
    upright_hits = []     # (packing index, variant choice, wall dict)
    best_not_upright = 0
    wall_best = {}
    for pk, sol in enumerate(sols):
        vlists = [variants(i, placed) for (i, placed, _) in sol]
        for combo in itertools.product(*[range(len(v)) for v in vlists]):
            n_asm += 1
            covered, interior, letters_on = collections.Counter(), collections.Counter(), {}
            for (v, ci) in zip(vlists, combo):
                M, off, ext, inter = v[ci]
                for key, lt in ext.items():
                    covered[key] += 1
                    if lt is not None:
                        letters_on[key] = lt
                for key in inter:
                    interior[key] += 1
            ok = bool(all(covered[k] == 1 for k in house_ext) and len(covered) == len(house_ext) and all(v == 2 for v in interior.values()))
            surface_ok_all = surface_ok_all and ok
            for w in read_walls(letters_on):
                key_n = (tuple(w["normal"]), tuple(w["top_left"]))
                wall_best[key_n] = max(wall_best.get(key_n, 0), w["upright"])
                st = text_stats[w["text"]]
                st["count"] += 1
                st["max_upright"] = max(st["max_upright"], w["upright"])
                if w["all_upright"]:
                    st["upright_count"] += 1
                    upright_hits.append((pk, combo, w))
    report["wall_best_upright"] = [dict(normal=list(k[0]), top_left=list(k[1]), max_upright=v) for k, v in sorted(wall_best.items())]
    report["assemblies"] = n_asm
    report["surface_ok"] = bool(surface_ok_all)
    report["distinct_wall_texts"] = len(text_stats)
    report["all_wall_texts"] = sorted(text_stats)
    upright_texts = sorted({w["text"] for _, _, w in upright_hits})
    report["upright_walls"] = upright_texts
    report["upright_wall_hits"] = len(upright_hits)
    report["upright_hit_packings"] = sorted({p for p, _, _ in upright_hits})
    if upright_hits:
        w = upright_hits[0][2]
        report["walls"] = [dict(normal=w["normal"], top_left=w["top_left"], text=w["text"], upright=w["upright"], nets=w["nets"], cells=w["cells"])]
        # drawn (front) wall: best uprightness per normal over all assemblies is reported through the texts
    report["max_upright_by_text_top"] = sorted(((t, d["max_upright"]) for t, d in text_stats.items() if d["max_upright"] >= 6), key=lambda x: -x[1])[:12]
    report["texts_in_word_list"] = sorted(t for t in text_stats if t in load_words())
    words = load_words()
    report["answer"] = upright_texts[0] if len(upright_texts) == 1 else None
    report["answer_in_word_list"] = bool(report["answer"] and report["answer"] in words)
    report["packings"] = len(sols)
    report["seconds"] = round(time.perf_counter() - T0, 1)
    return report


def _example_convention(e):
    """Rotate the folded example so that F stands on a vertical face with its normal toward the viewer (-y) and upright;
    then G must lie on the top face with its foot toward the front (up = +y), as drawn."""
    idx = {l: j for j, l in enumerate(e["letters"]) if l}
    if "F" not in idx or "G" not in idx:
        return False
    def normal(j):
        Pj = [np.array(p) for p in e["faces"][j]]
        n = np.cross(Pj[1] - Pj[0], Pj[2] - Pj[0])
        return n / np.linalg.norm(n)
    # outward normals: faces are CCW seen from outside after fold only if printed side is out; check via signed volume
    vol = 0.0
    for Pj in e["faces"]:
        for m in range(1, len(Pj) - 1):
            a, b, c = np.array(Pj[0]), np.array(Pj[m]), np.array(Pj[m + 1])
            vol += np.dot(a, np.cross(b, c)) / 6
    if vol <= 0:
        return False
    nF, nG = normal(idx["F"]), normal(idx["G"])
    uF, uG = e["ups"][idx["F"]], e["ups"][idx["G"]]
    for M in ROTS:
        if np.allclose(M @ nF, (0, -1, 0)) and np.allclose(M @ uF, (0, 0, 1)):
            return bool(np.allclose(M @ nG, (0, 0, 1)) and np.allclose(M @ uG, (0, 1, 0)))
    return False
