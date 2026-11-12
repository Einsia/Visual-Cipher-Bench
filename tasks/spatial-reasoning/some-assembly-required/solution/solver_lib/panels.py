"""Recover computational unit tiles inside unmarked paper regions.

Input is only a segmented PNG region and the unit measured from intact faces.
No face tables, seam coordinates, letters, answer or render data are used. Each
region is fitted to a 0/45-degree lattice. Full grid cells are squares; half cells
are blank right triangles. Sloping rectangles use the measured sqrt(2) dimension.
Every inferred unit interface is allowed to fold OR remain flat; closure decides.
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


def recover_panel(face, unit):
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
        if max(abs(hi-lo-dims*step)) > unit*(0.25 if kind=="sq" else 0.12):
            continue
        origin = (lo+hi-dims*step)/2
        # Fit grid translation before classifying cells. An oblique tip can
        # move the offset convex hull by several pixels; it must not create a
        # spurious half-cell or determine the grid origin.
        frac = np.linspace(.20, .80, 9)
        sample_uv = np.array([(a,b) for a in frac for b in frac])
        tris = [[(0,0),(1,0),(0,1)], [(0,0),(1,0),(1,1)],
                [(1,0),(1,1),(0,1)], [(0,0),(1,1),(0,1)]]
        patterns = [np.zeros(len(sample_uv),bool), np.ones(len(sample_uv),bool)]
        if kind == 'sq':
            patterns += [sample_uv.sum(1)<1.01, sample_uv[:,1]<=sample_uv[:,0]+.01,
                         sample_uv.sum(1)>.99, sample_uv[:,1]>=sample_uv[:,0]-.01]
        patterns = np.asarray(patterns)
        cell_indices=np.array([(ix,iy) for ix in range(dims[0]) for iy in range(dims[1])])
        base_samples=(origin+step*(cell_indices[:,None,:]+sample_uv[None,:,:])) @ basis.T
        trial=[]
        for dy in range(-12,13,2):
            for dx in range(-12,13,2):
                samples=base_samples+[dx,dy]
                xs=np.round(samples[:,:,0]-x0).astype(int)
                ys=np.round(samples[:,:,1]-y0).astype(int)
                valid=(xs>=0)&(ys>=0)&(xs<mask.shape[1])&(ys<mask.shape[0])
                obs=np.zeros(xs.shape,bool);obs[valid]=mask[ys[valid],xs[valid]]
                scores=np.mean(patterns[None,:,:]!=obs[:,None,:],axis=2)
                picks=scores.argmin(1);errors=scores.min(1)
                trial.append((float(errors.sum()), float(errors.max()), dx*dx+dy*dy, dx,dy,picks))
        _,err,_,gx,gy,picks=min(trial,key=lambda x:x[:3])
        if err>.35:
            continue
        polygons=[]
        for (ix,iy),pick in zip(cell_indices,picks):
            if pick==0: continue
            base=origin+step*[ix,iy]
            local=[(0,0),(1,0),(1,1),(0,1)] if pick==1 else tris[pick-2]
            polygons.append((base+np.asarray(local)*step) @ basis.T+[gx,gy])
        if not polygons: continue
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
        # without using glyph positions or any table of seams.
        translations = []
        for dy in range(-12,13):
            for dx in range(-12,13):
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
    # Square grids differing by 90 degrees are not generated. In these panels,
    # the length fit must leave only one grid family, not merely a preferred one.
    if len(candidates)>1 and candidates[1][0] > candidates[0][0]-.03:
        raise ValueError('ambiguous lattice subdivision: %s' % (face['mask_box'],))
    score, polygons, kind, angle = candidates[0]
    return [dict(poly_px=[tuple(p) for p in poly], panel_id=face['mask_box']) for poly in polygons], dict(
        box=face['mask_box'], tiles=len(polygons), grid=kind, angle=angle,
        outline_iou=round(score,4), viable_grids=len(candidates))


def recover(faces_px, unit):
    faces, evidence = [], []
    for f in faces_px:
        pu = [(x/unit, -y/unit) for x,y in f['poly_px']]
        if P._poly_area(pu)<0:
            pu=pu[::-1]
        kind, template, iou = P.fit_face(pu)
        try:
            ff, info = recover_panel(f, unit)
        except ValueError:
            if kind is None or iou <= .8:
                raise
            ff = [dict(f, panel_id=f['mask_box'])]
            info = dict(box=f['mask_box'], tiles=1, grid=kind, outline_iou=round(iou,4), viable_grids=1)
        faces.extend(ff)
        evidence.append(info)
    return faces, evidence
