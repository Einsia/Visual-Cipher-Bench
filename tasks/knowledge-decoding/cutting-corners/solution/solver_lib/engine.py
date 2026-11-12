"""PNG-only reference: recover grids, letters, icons, extraction circles and unregistered stencils; learn the example, then jointly solve stencil registration and the picture crossword."""
import hashlib
import json
from pathlib import Path

from . import model as M
from . import pixels as P
from . import stencils as S

HERE = Path(__file__).resolve().parent


def images_path(arg):
    p = Path(arg)
    if p.is_file():
        return p
    pngs = sorted(p.glob("*.png"))
    if not pngs:
        raise FileNotFoundError(f"no PNG under {p}")
    return pngs[0]


def picture_names():
    return json.loads((HERE / "picture_names.json").read_text())["names"]


def tokens_of(grid, with_pictures=True):
    out = {}
    for rc, x in grid["cells"].items():
        k = x["kind"]
        if k == "block":
            out[rc] = "."
        elif k == "empty":
            out[rc] = "_"
        elif k == "circle":
            out[rc] = "o"
        elif k == "letter":
            out[rc] = ("G:" if x["cls"][0] == "bold" else "F:") + x["cls"][1]
        elif k == "icon":
            out[rc] = "P:" + x["cls"][1]
        elif k == "ringed_letter":
            out[rc] = "R:" + (x["cls"][1] if x["cls"] else "?")
        else:
            out[rc] = "X:" + k
    return out


def rows_text(grid, toks):
    return [" ".join(toks[(r, c)] for c in range(grid["cols"])) for r in range(grid["rows"])]


def analyse(path):
    """Return a context dict with everything read from pixels (no solving)."""
    ctx = {"errors": [], "checks": []}
    from PIL import Image
    im = Image.open(path)
    ctx["size"] = im.size
    g = P.load_gray(path)
    grids = P.find_grids(g)
    ctx["grid_boxes"] = grids
    if len(grids) != 3:
        ctx["errors"].append(f"expected 3 grids (BEFORE, AFTER, main), found {len(grids)}")
        return ctx
    area = [(b[2] - b[0]) * (b[3] - b[1]) for b in grids]
    main_i = max(range(3), key=lambda i: area[i])
    ex = sorted([grids[i] for i in range(3) if i != main_i], key=lambda b: b[0])
    ctx["main_box"] = grids[main_i]
    plates = P.read_stencils(g)
    ctx["stencils_example"] = [p for p in plates if p["box"][3] < grids[main_i][1]]
    ctx["stencils_main"] = [p for p in plates if p["box"][1] > grids[main_i][1]]
    before = P.read_grid(g, ex[0])
    after = P.read_grid(g, ex[1])
    main = P.read_grid(g, grids[main_i])
    ctx.update({"g": g, "before": before, "after": after, "main": main})
    ctx["before_tokens"] = tokens_of(before)
    ctx["after_tokens"] = tokens_of(after)
    ctx["main_tokens"] = tokens_of(main)
    bx = ex[0]
    ctx["blanks_before"] = P.read_blanks(g, (bx[0] - 10, bx[3] + 10, bx[2] + 30, bx[3] + 130))
    ax = ex[1]
    ctx["blanks_after"] = P.read_blanks(g, (ax[0] - 10, ax[3] + 10, ax[2] + 30, ax[3] + 130))
    mb = grids[main_i]
    ctx["blanks_main"] = P.read_blanks(g, (mb[0] - 10, mb[3] + 15, mb[2] + 10, mb[3] + 150))
    return ctx


def learn_example(ctx):
    """Check BEFORE -> AFTER and learn how circled cells are copied onto blanks. Returns (ok, evidence, order)."""
    b, a = ctx["before"], ctx["after"]
    ev = {}
    if (b["rows"], b["cols"]) != (a["rows"], a["cols"]):
        return False, {"why": "example grids differ in size"}, None
    bt, at = ctx["before_tokens"], ctx["after_tokens"]
    circled_b = sorted(rc for rc, t in bt.items() if t == "o")
    circled_a = sorted(rc for rc, t in at.items() if t.startswith("R:"))
    ev["circled_cells_before"] = circled_b
    ev["circled_cells_after"] = circled_a
    if circled_b != circled_a or not circled_b:
        return False, dict(ev, why="circled cells differ between BEFORE and AFTER"), None
    kept = all(at[rc] == t for rc, t in bt.items() if t.startswith("G:"))
    ev["engraved_letters_kept"] = kept
    plates=ctx["stencils_example"]
    if len(plates)!=1 or not all(p['readable'] for p in plates):
        return False, dict(ev, why="example stencil missing or unreadable"), None
    targets={rc:t[2:] for rc,t in at.items() if t.startswith('G:')}
    cells={rc for rc,t in bt.items() if t in ('_', 'o')}
    ps=S.placements(plates[0]['letters'],cells)
    matching=[p for p in ps if p==targets]
    ev['stencil_registrations_matching_bold_letters']=len(matching)
    ev['stencil_letters_from_pixels']=plates[0]['letters']
    kept=kept and len(matching)==1 and not any(t.startswith('G:') for t in bt.values())
    filled = sorted(rc for rc, t in bt.items() if t in ("_", "o", "P:note") or t.startswith("P:"))
    ev["filled_cells"] = filled
    letters = {rc: at[rc][2:] for rc in circled_a}
    blanks = ctx["blanks_after"]
    word = "".join(x["letter"] or "?" for x in blanks)
    ev["blank_word"] = word
    ev["blanks_before_count"] = len(ctx["blanks_before"])
    ev["blanks_after_count"] = len(blanks)
    orders = {
        "row-major": sorted(circled_a, key=lambda rc: (rc[0], rc[1])),
        "column-major": sorted(circled_a, key=lambda rc: (rc[1], rc[0])),
    }
    fits = [n for n, cells in orders.items() if "".join(letters[c] for c in cells) == word]
    ev["orders_matching_blanks"] = fits
    ev["circled_letters_by_order"] = {n: "".join(letters[c] for c in cells) for n, cells in orders.items()}
    if not kept or len(fits) != 1 or len(ctx["blanks_before"]) != len(circled_b) or len(blanks) != len(circled_b):
        return False, dict(ev, why="example does not fix one reading order"), None
    return True, ev, fits[0]


def build_design(ctx):
    main = ctx["main"]
    toks = ctx["main_tokens"]
    names = picture_names()
    rows, pictures, circles, engraved = [], {}, [], set()
    for r in range(main["rows"]):
        row = []
        for c in range(main["cols"]):
            t = toks[(r, c)]
            if t == ".":
                row.append(".")
            elif t in ("_", "o"):
                row.append("?")
                if t == "o":
                    circles.append([r, c])
            elif t.startswith("G:") or t.startswith("F:"):
                row.append(t[2:])
                engraved.add((r, c))
            elif t.startswith("P:"):
                icon = t[2:]
                if icon not in names:
                    raise ValueError(f"pictogram {icon!r} at {(r, c)} has no name list")
                key = f"p{r}_{c}"
                pictures[key] = {"names": names[icon], "icon": icon, "cell": [r, c]}
                row.append("#" + key)
            else:
                raise ValueError(f"unreadable main-grid cell {(r, c)}: {t}")
        rows.append(" ".join(row))
    return {"grid": rows, "pictures": pictures, "circles": circles}, engraved


def evaluate(path):
    ctx = analyse(path)
    checks = []
    res = {"valid": False, "unique": False, "solution_count": 0, "answer": None,
           "image_hashes": {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest()}, "checks": checks}

    def chk(name, ok, ev):
        checks.append({"name": name, "passed": bool(ok), "evidence": ev})
        return ok

    if ctx["errors"]:
        chk("page_structure", False, ctx["errors"])
        return res
    chk("page_structure", min(ctx["size"]) >= 768, {"size": ctx["size"], "grid_boxes": ctx["grid_boxes"],
                                                    "main_cells": [ctx["main"]["rows"], ctx["main"]["cols"], round(ctx["main"]["pitch"], 1)]})
    ok, ev, order = learn_example(ctx)
    chk("example_convention", ok, dict(ev, before=rows_text(ctx["before"], ctx["before_tokens"]),
                                       after=rows_text(ctx["after"], ctx["after_tokens"]), reading_order=order))
    if not ok:
        return res
    anomalies = {rc: x for rc, x in ctx["main"]["cells"].items() if x["kind"] in ("anomaly", "other", "ringed_letter")}
    if not chk("main_cells_readable", not anomalies, {"anomalies": {str(k): v.get("why", v["kind"]) for k, v in anomalies.items()}}):
        return res
    try:
        design, engraved = build_design(ctx)
    except ValueError as e:
        chk("main_grid_model", False, str(e))
        return res
    circles = sorted(map(tuple, design["circles"]), key=(lambda rc: (rc[0], rc[1])) if order == "row-major" else (lambda rc: (rc[1], rc[0])))
    design["circles"] = [list(c) for c in circles]
    nblanks = len(ctx["blanks_main"])
    chk("answer_blanks_match_circles", nblanks == len(circles) and all(b["ring"] and b["letter"] is None for b in ctx["blanks_main"]),
        {"blanks": nblanks, "circles": len(circles)})
    if nblanks != len(circles):
        return res
    plates=ctx['stencils_main']
    if not chk('stencils_readable', bool(plates) and all(p['readable'] for p in plates) and not engraved,
               {'stencils': plates, 'fixed_main_letters':len(engraved)}):
        return res
    design['stencils']=[p['letters'] for p in plates]
    strict, broad = M.lexicons()
    try:
        mb = M.Model(design, broad)
        ms = M.Model(design, strict)
    except ValueError as e:
        chk("main_grid_model", False, str(e))
        return res
    fb, capb, stb = S.solve(mb, design["stencils"])
    fs, caps, sts = S.solve(ms, design["stencils"])
    outs = sorted({mb.extract(s["letters"]) for s in fb})
    res["solution_count"] = len(fb)
    chk("unique_fill_broad_lexicon", len(fb) == 1 and not capb,
        {"distinct_fills": len(fb), "outputs": outs[:10], "capped": capb, "nodes": stb["nodes"],
         "slots": len(mb.slots), "pictures": len(design["pictures"]), "engraved": len(engraved), "circles": len(circles), "registration_search":stb})
    chk("unique_fill_strict_lexicon", len(fs) == 1 and not caps, {"distinct_fills": len(fs), "capped": caps})
    if len(fb) != 1 or capb:
        res["candidate_answers"] = outs
        return res
    sol = fb[0]
    ans = mb.extract(sol["letters"])
    res.update({"valid": all(c["passed"] for c in checks), "unique": True, "answer": ans,
                "words": sorted(zip([s["dir"] for s in mb.slots], sol["words"]))})
    res["picture_names"] = {k: sorted(v) for k, v in sol["names"].items()}
    res["_ctx"] = {"design": design, "engraved": engraved, "model_broad": mb, "model_strict": ms, "fills": (fb, fs), "order": order, "registration_stats":stb}
    return res
