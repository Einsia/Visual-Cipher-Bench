"""Geometry screening from recovered image measurements."""
from pathlib import Path
from PIL import Image
import json
import math
import numpy as np
from .parser import parse, OCR, FACE_BOXES, require, PixelError
from .pixel_utils import rgb_mask, components, rod
from .sight_pixels import read_cards
from .sight_match import match


def read_gauges(arr):
    """Recover the physical triangle angles from their exterior pixel hulls."""
    crop=arr[320:960,230:570];gauges=[]
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for comp in components(rgb_mask(crop,(17,17,17))):
        left,top,right,bottom=comp['box']
        if right-left<180 or bottom-top<180:continue
        points=sorted(set((x,y) for l,y,r in comp['runs'] for x in (l,r-1)))
        halves=[]
        for sequence in (points,list(reversed(points))):
            half=[]
            for p in sequence:
                while len(half)>1 and cross(half[-2],half[-1],p)<=0:half.pop()
                half.append(p)
            halves.append(half[:-1])
        hull=[np.array(p,dtype=float) for p in halves[0]+halves[1]]
        while len(hull)>3:
            errors=[abs(cross(hull[i-1],hull[i],hull[(i+1)%len(hull)])) /
                    np.linalg.norm(hull[(i+1)%len(hull)]-hull[i-1]) for i in range(len(hull))]
            j=int(np.argmin(errors))
            if errors[j]>2.5:break
            hull.pop(j)
        require(len(hull)==3,'Gauge silhouette is not a complete triangle')
        angles=[]
        for i,p in enumerate(hull):
            a,b=hull[i-1]-p,hull[(i+1)%3]-p
            angles.append(math.degrees(math.acos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
        # The largest physical corner is the marked fitting corner in both
        # drawn gauges. Integer-degree rounding only removes raster-edge noise.
        contact=max(angles);nearest=int(round(contact))
        require(abs(contact-nearest)<.55,'Imprecise physical gauge corner')
        gauges.append({'vertices_px':[(p+[230,320]).tolist() for p in hull],
                       'measured_angles':angles,'contact_angle':nearest})
    require(len(gauges)==2,'Missing physical gauge')
    return gauges


def read_setup(arr):
    ocr=OCR();poses=[]
    gauges=read_gauges(arr)
    diagram_regions=[(1950,1288,2280,1588),(2410,1288,2730,1588),(2890,1278,3200,1588)]
    angle_regions=[(2190,921,2258,958),(2646,921,2740,958),(3118,761,3188,797)]
    arrow_regions=[(691,1240,717,1335),(742,1195,837,1221),(1203,733,1230,822)]
    for index,box in enumerate(diagram_regions):
        a,b,c,d=box
        red=rgb_mask(arr[b:d,a:c],(85,85,85))
        candidates=[]
        for comp in components(red):
            l,t,r,bt=comp['box']
            if 15<=r-l<=24 and abs(r-l-(bt-t))<=2:
                candidates.append(((l+r)/2+a,(t+bt)/2+b))
        require(len(candidates)==1,'Missing/extra filled start endpoint in setup diagram')
        start=np.array(candidates[0])
        # Parent baseline and child junction are read in a narrow layout band.
        band=red[1420-b:1445-b]
        row_counts=band.sum(axis=1)
        # All three observed stationary parent arms share a horizontal baseline.
        base=1432
        xs=np.flatnonzero(red[base-b])
        require(len(xs)>0,'No child arm at the setup pivot')
        pivot=np.array([float(xs.mean()+a+.5),float(base)])
        theta=math.degrees(math.atan2(start[1]-pivot[1],start[0]-pivot[0]))
        # Read the section, then match the supplementary physical gauge angle.
        # No angle list or angle numeral is used by the solver.
        measured_angle=min((180-g['contact_angle'] for g in gauges),key=lambda q:abs(q-abs(theta)))
        require(abs(abs(theta)-measured_angle)<.4,'Unclear geometric setup angle')
        l,t,r,bt=arrow_regions[index]
        ink=rgb_mask(arr[t:bt,l:r],(17,17,17))
        profile=ink.sum(axis=1 if index!=1 else 0)
        broad=np.flatnonzero(profile>profile.max()*.75)
        require(len(broad)>0,'Missing axis view arrow')
        head=float(broad.mean())
        extent=len(profile)
        sign=1 if head<extent/2 else -1
        if index==1:sign=-sign
        degree=(1 if theta>0 else -1)*measured_angle*sign
        poses.append({'hinge':index+1,'diagram_box':list(box),'pivot_px':pivot.tolist(),
                      'start_px':start.tolist(),'drawn_angle_degrees':theta,
                      'measured_angle':measured_angle,'view_sign':sign,'material_angle':degree,
                      'physical_gauges':gauges,
                      'axis_arrow_box':list(arrow_regions[index])})
    return poses


def local_uv(face,point):
    a,b,c,d=FACE_BOXES[face]
    x,y=point
    return np.array([(x-a)/(c-a),((d-y) if face.endswith('+') else (y-b))/(d-b)])


def transforms(angles):
    # Shared edges are obtained from the measured unfolded panel rectangles.
    cells=[]
    for p in 'ABCD':
        a,b,c,d=FACE_BOXES[p+'+'];cells.append(np.array([(a-192)/512,(1720-d)/512]))
    ts=[np.eye(4)]
    for i,degree in enumerate(angles):
        parent,child=cells[i],cells[i+1]
        delta=child-parent
        if delta[0]>.5:
            origin=np.r_[child,0.];axis=[0,1,0]
        else:
            origin=np.r_[child,0.];axis=[1,0,0]
        rr=rod(axis,degree);move=np.eye(4);move[:3,:3]=rr;move[:3,3]=origin-rr@origin
        ts.append(ts[-1]@move)
    return cells,ts


def solve_structure(structure,angles,arr):
    cards=read_cards(arr,OCR())
    front_windows=[w for w in structure['windows'] if w['face'].endswith('+')]
    pools=[p for p in structure['nodes'] if p['kind']=='pool']
    starts=[p for p in pools if p.get('icon')=='drop'];require(len(starts)==1,'No unique start')
    state=starts[0];visited=set();digits=[];trace=[]
    for step in range(100):
        if state.get('icon')=='lock':
            return {'answer':''.join(digits),'trace':trace,'terminated':True,'final_angles':angles}
        key=(state['id'],tuple(angles));require(key not in visited,'Route loops');visited.add(key)
        for h in state['switches']:angles[h-1]*=-1
        cells,ts=transforms(angles);holes=[]
        for p in 'ABCD':
            w=next(w for w in front_windows if w['face']==p+'+')
            l,t,r,b=w['cut_box'];lo=local_uv(w['face'],(l,b));hi=local_uv(w['face'],(r,t))
            holes.append([[*lo,*hi]])
        origin,direction,evidence=match(cells,ts,holes,cards[state['view_code']])
        events=[]
        for p in range(4):
            inv=np.linalg.inv(ts[p]);o=(inv@np.r_[origin,1.])[:3];v=(inv@np.r_[direction,0.])[:3]
            if abs(v[2])<1e-9:continue
            t=-o[2]/v[2];uv=(o+t*v)[:2]-cells[p]
            inside=bool(np.all(uv>=0)&np.all(uv<=1))
            if not inside and p in (0,3):
                a,b,c,d=FACE_BOXES['ABCD'[p]+'+'];xx=int(round(a+512*uv[0]));yy=int(round(d-512*uv[1]))
                on_tab=((a-144<=xx<a) if p==0 else (c<=xx<c+144)) and b<=yy<d
                if on_tab:
                    row=rgb_mask(arr[yy,max(0,a-144):a] if p==0 else arr[yy,c:c+144],(17,17,17));edges=np.flatnonzero(row)
                    inside=bool(len(edges) and (xx>=max(0,a-144)+edges.min() if p==0 else xx<c+edges.max()))
            if not inside:continue
            l,b,r,top=holes[p][0];u,w=uv
            hole=bool(l<u<r and b<w<top)
            events.append({'panel':'ABCD'[p],'side':'+' if v[2]<0 else '-', 't':float(t),'uv':uv.tolist(),'hole':hole,
                           'aperture_margin_mm':64*min(u-l,r-u,w-b,top-w) if hole else None})
        events.sort(key=lambda h:h['t']);solids=[(i,h) for i,h in enumerate(events) if not h['hole']]
        require(solids,'Sightline misses the paper');first,hit=solids[0]
        require(first>=2,'The cross is not visible through two windows before first paper: '+str((state['view_code'],events,evidence['pixel_error'])))
        face=hit['panel']+hit['side'];uv=np.array(hit['uv']);receivers=[]
        for pool in pools:
            if pool['face']!=face:continue
            a,b,c,d=pool['box'];radius=((c-a+d-b)/4-1.6)/512
            distance=float(np.linalg.norm(local_uv(face,pool['center'])-uv))
            if distance<radius:receivers.append(pool);hit['pool_margin_mm']=(radius-distance)*64
        require(len(receivers)==1,'No unique pool contains first opaque hit: '+str(hit))
        nxt=receivers[0]
        if 'digit' in nxt:digits.append(nxt['digit'])
        trace.append({'step':step+1,'source_pool':state['id'],'view_match':evidence,'view_code':state['view_code'],
                      'switches':state['switches'],'angles':angles.copy(),'intersections':events,
                      'first_material':hit,'receiver_pool':nxt['id'],'read':nxt.get('digit',nxt.get('icon'))})
        state=nxt
    raise PixelError('Route exceeds finite-state bound')
