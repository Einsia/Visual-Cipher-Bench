"""Recover unit tiles inside continuous paper regions from PNG geometry.

Inputs are segmented regions, the measured unit and (when needed) printed glyph
positions. No design coordinates or crease tables are consulted. These
are computational tiles; their unmarked boundaries may be flat or folded.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
import pixparse as P


def fill_holes(mask):
    z = np.pad(mask, 1)
    lab, n = P.label(~z, 4)
    exterior = lab[0, 0]
    return (lab != exterior)[1:-1, 1:-1]


def recover_panel(face, unit, gray=None):
    Q = np.asarray(face['poly_px'], float)
    mask = fill_holes(face['region_mask'])
    x0, y0, x1, y1 = face['mask_box']
    candidates = []
    # Two square grids and four possible long-axis directions for slope rectangles.
    for kind, angle in [('sq', 0), ('sq', 45), ('rect', 0), ('rect', 45), ('rect', 90), ('rect', 135)]:
        t = math.radians(angle)
        basis = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
        uv = Q @ basis
        lo, hi = uv.min(0), uv.max(0)
        step = np.array([unit, unit * (math.sqrt(2) if kind == 'rect' else 1)])
        dims = np.round((hi-lo)/step).astype(int)
        if min(dims) < 1 or max(dims) > 8:
            continue
        if max(abs(hi-lo-dims*step)) > unit*0.23:
            continue
        origin = (lo+hi-dims*step)/2
        polygons = []
        errors = []
        # Compare interior samples, clear of the printed boundary and letter holes.
        frac = np.linspace(.18, .82, 9)
        sample_uv = np.array([(a,b) for a in frac for b in frac])
        patterns = [np.ones(len(sample_uv), bool)]
        tris = [[(0,0),(1,0),(0,1)], [(0,0),(1,0),(1,1)],
                [(1,0),(1,1),(0,1)], [(0,0),(1,1),(0,1)]]
        patterns += [sample_uv.sum(1)<1.01, sample_uv[:,1]<=sample_uv[:,0]+.01,
                     sample_uv.sum(1)>.99, sample_uv[:,1]>=sample_uv[:,0]-.01]
        for ix in range(dims[0]):
            for iy in range(dims[1]):
                base = origin+step*[ix,iy]
                samples = (base+sample_uv*step) @ basis.T
                xs = np.round(samples[:,0]-x0).astype(int)
                ys = np.round(samples[:,1]-y0).astype(int)
                valid = (xs>=0)&(ys>=0)&(xs<mask.shape[1])&(ys<mask.shape[0])
                observed = np.zeros(len(xs), bool)
                observed[valid] = mask[ys[valid],xs[valid]]
                if observed.mean()<.04:
                    continue
                scores = [np.mean(p!=observed) for p in patterns[:(5 if kind=='sq' else 1)]]
                pick = int(np.argmin(scores))
                errors.append(scores[pick])
                local = [(0,0),(1,0),(1,1),(0,1)] if pick==0 else tris[pick-1]
                polygons.append((base+np.asarray(local)*step) @ basis.T)
        if not polygons or max(errors)>.35:
            continue
        # Whole-region support check, including concave corners and empty cells.
        pad = int(unit*.2)
        target = np.pad(mask, pad)
        target = P.dilate(target, 6)
        pred_img = Image.new('1', (target.shape[1],target.shape[0]))
        draw = ImageDraw.Draw(pred_img)
        for poly in polygons:
            draw.polygon([tuple(p-[x0-pad,y0-pad]) for p in poly], fill=1)
        pred = np.asarray(pred_img, bool)
        # Convex-hull offsets can shift the fitted origin at a concave corner.
        # Register the complete (possibly concave) union against the region,
        # without using glyph positions or a table of undrawn seams.
        translations = []
        for dy in range(-6,7):
            for dx in range(-6,7):
                shifted = np.roll(np.roll(pred,dy,axis=0),dx,axis=1)
                iou = (shifted&target).sum()/max(1,(shifted|target).sum())
                translations.append((float(iou), -dx*dx-dy*dy, dx, dy))
        iou, _, dx, dy = max(translations)
        polygons = [p+np.array([dx,dy]) for p in polygons]
        if iou < .88:
            continue
        candidates.append((float(iou), polygons, kind, angle))
    candidates.sort(key=lambda c:-c[0])
    if not candidates:
        raise ValueError('continuous panel cannot be recovered from its outline: %s' % (face['mask_box'],))
    outline_candidates = len(candidates)
    glyph_resolved = False
    if len(candidates)>1:
        if gray is None:
            raise ValueError('panel grid ambiguous without the printed letter positions')
        import netparse as N
        viable=[]
        for cand in candidates:
            ok=True
            for poly in cand[1]:
                letter=N.face_letter(gray,poly)
                if len(poly)==3:
                    ok = letter is None
                else:
                    ok = bool(letter and letter['score']>=.7 and letter['glyph_only_letter']==letter['letter']
                              and letter['glyph_only_score']>=.7)
                if not ok:break
            if ok:viable.append(cand)
        if len(viable)!=1:
            raise ValueError('panel grid remains ambiguous after checking its printed letters')
        candidates=viable
        glyph_resolved=True
    score, polygons, kind, angle = candidates[0]
    return [dict(poly_px=[tuple(p) for p in poly], panel_id=face['mask_box']) for poly in polygons], dict(
        box=face['mask_box'], tiles=len(polygons), grid=kind, angle=angle,
        outline_iou=round(score,4), viable_grids=len(candidates), outline_candidates=outline_candidates, glyph_resolved=glyph_resolved)


def recover(faces_px, unit, gray=None):
    faces, evidence = [], []
    for f in faces_px:
        pu = [(x/unit, -y/unit) for x,y in f['poly_px']]
        if P._poly_area(pu)<0:
            pu=pu[::-1]
        kind, template, iou = P.fit_face(pu)
        try:
            ff, info = recover_panel(f, unit, gray)
        except ValueError:
            if kind is None or iou <= .8:
                raise
            ff = [dict(f, panel_id=f['mask_box'])]
            info = dict(box=f['mask_box'], tiles=1, grid=kind, outline_iou=round(iou,4), viable_grids=1)
        faces.extend(ff)
        evidence.append(info)
    return faces, evidence
