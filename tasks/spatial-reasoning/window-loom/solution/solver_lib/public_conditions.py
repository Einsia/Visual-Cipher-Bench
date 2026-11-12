"""Pixel checks for the public rule, preparation, and output grammar."""
from PIL import Image
import numpy as np
from .parser import OCR, require, FACE_BOXES
from .pixel_utils import rgb_mask, components

RULE_ROWS=[
 (1704,1744,'Cut edges, slots, gauges and crossed windows.'),
 (1748,1787,'Backs under; tuck tabs.'),
 (1856,1895,'View along arrows; fit gauges as shown.'),
 (1961,1998,'Switch marked hinges through flat.'),
 (2005,2042,'Continue at the hit pool, on that side.'),
 (2049,2087,'Read boxed digits to the lock.'),
 (2093,2130,'Match the view after switching.'),
 (1659,1693,'MAKE FIRST'),
 (1810,1844,'SETUP - 1 MIN - BACKED, FLAT SHEET'),
 (1914,1948,'PLAY')]


def same_component(mask, first, last):
    for c in components(mask):
        first_hit=last_hit=False
        for a,y,b in c['runs']:
            if first[1]<=y<first[3] and a<first[2] and b>first[0]:first_hit=True
            if last[1]<=y<last[3] and a<last[2] and b>last[0]:last_hit=True
        if first_hit and last_hit:return True
    return False


def verify_public(arr,structure,setup):
    ocr=OCR();results=[]
    for top,bottom,expected in RULE_ROWS:
        try:observed=ocr.compact_line(arr[top:bottom,1930:3220])
        except ValueError as exc:raise ValueError(str(exc)+' for rule '+expected) from exc
        require(observed==expected.replace(' ',''),'Incomplete or changed public instruction: '+str((expected,observed)))
        results.append({'text':expected,'box':[1930,top,3220,bottom],'recovered_compact':observed})
    for text,box in [('start',[1998,1167,2110,1208]),('other',[2254,1167,2370,1208]),('flat',[2608,1167,2710,1208])]:
        a,b,c,d=box
        observed=ocr.compact_line(arr[b:d,a:c],choices=set(text))
        require(observed==text,'Missing setup legend: '+str((text,observed)))
    for text,y in [('Parallel views; turn, never mirror.',124),
                   ('Outlines only; tabs and ink omitted.',130),
                   ('White fronts; grey backs.',136),
                   ('Sight at the cross through the windows.',142),
                   ('Stop at the first paper on that sightline.',204)]:
        box=[1930,int((y-4.3)*8),3270,int((y+.8)*8)]
        a,b,c,d=box
        observed=ocr.compact_line(arr[b:d,a:c],choices=set(text))
        require(observed==text.replace(' ',''),'Missing spatial-view rule: '+str((text,observed)))
        results.append({'text':text,'box':box,'recovered_compact':observed})
    for s in setup:
        px,py=s['pivot_px'];sx,sy=s['start_px']
        flat=rgb_mask(arr[int(py)-2:int(py)+3,int(px)+25:int(px)+128],(17,17,17)).any(axis=0)
        require(flat.mean()>.35,'Missing flat reference in setup diagram')
        if s['hinge']==1:continue
        ox,oy=sx,2*py-sy
        ring=rgb_mask(arr[int(oy)-16:int(oy)+17,int(ox)-16:int(ox)+17],(17,17,17))
        for theta in np.linspace(0,2*np.pi,24,endpoint=False):
            tx=int(round(16+12*np.cos(theta)));ty=int(round(16+12*np.sin(theta)))
            require(ring[ty-2:ty+3,tx-2:tx+3].any(),'Missing alternate stance endpoint')
        require(not rgb_mask(arr[int(oy)-3:int(oy)+4,int(ox)-3:int(ox)+4],(85,85,85)).any(),
                'Alternate stance is not an open endpoint')
    for w in structure['windows']:
        a,b,c,d=map(int,w['cut_box']);inside=arr[b+8:d-8,a+8:c-8]
        dark=(inside[:,:,0]<200)&(inside[:,:,1]<175)&(inside[:,:,2]<150)
        cross=[q for q in components(dark) if q['area']>80]
        require(len(cross)==1,'Missing or extra waste cross in '+w['letter']+w['face'])
        l,t,r,bt=cross[0]['box']
        require(r-l>.50*(c-a) and bt-t>.50*(d-b),'Incomplete crossed waste symbol')
    for front in [w for w in structure['windows'] if w['face'].endswith('+')]:
        back=next(w for w in structure['windows'] if w['face']==front['face'][0]+'-')
        fold=1720 if front['face'][0] in 'AB' else 696
        mapped=[back['center'][0],2*fold-back['center'][1]]
        require(np.max(np.abs(np.array(mapped)-front['center']))<1,'Front/back aperture registration differs')
        require(np.max(np.abs(np.diff(np.array(front['cut_box']).reshape(2,2),axis=0)-np.diff(np.array(back['cut_box']).reshape(2,2),axis=0)))<1,'Front/back aperture sizes differ')
    # Complete slits: single thin connected strokes, not just one center sample.
    slit_boxes=[[218,1548,231,1688],[1178,1210,1191,1306],[729,716,743,861],[1689,1033,1703,1178]]
    slit_records=[]
    for box in slit_boxes:
        a,b,c,d=box;m=rgb_mask(arr[b:d,a:c],(17,17,17));cc=components(m)
        candidates=[q for q in cc if q['box'][3]-q['box'][1]>60 and q['box'][2]-q['box'][0]<=7]
        require(len(candidates)==1,'Missing/broken backing slit')
        l,t,r,bt=candidates[0]['box']
        slit_records.append({'box':[a+l,b+t,a+r,b+bt],'length_px':bt-t})
    # A numbered dashed score must span each of the three shared edges.
    hinge_lines=[(True,704,1208,1720,1456),(False,1208,704,1216,950),(True,1216,696,1208,944)]
    for vertical,constant,start,end,badge in hinge_lines:
        if vertical:m=rgb_mask(arr[start:end,constant-2:constant+3],(17,17,17)).any(axis=1)
        else:m=rgb_mask(arr[constant-2:constant+3,start:end],(17,17,17)).any(axis=0)
        keep=np.abs(np.arange(start,end)-badge)>31
        require(float(m[keep].mean())>.50,'Missing numbered hinge span')
        longest=run=0
        for ink,used in zip(m,keep):
            run=run+1 if used and not ink else 0;longest=max(longest,run)
        require(longest<28,'Unexplained long break in a main hinge')
    # Output plaque, lock and arrow remain distinct, visible objects.
    output=rgb_mask(arr[2155:2300,2745:3230],(17,17,17))
    cc=components(output)
    require(any(q['box'][2]-q['box'][0]>440 and q['box'][3]-q['box'][1]>115 for q in cc),'Missing output plaque')
    require(rgb_mask(arr[2170:2285,2620:2706],(17,17,17)).sum()>1700,'Missing output lock')
    require(rgb_mask(arr[2300:2324,2760:3210],(17,17,17)).sum()>1400,'Missing read-order arrow')
    return {'rules':results,'slits':slit_records,'checked':['window_waste_crosses','front_back_aperture_registration',
             'continuous_slits','main_score_spans','nine_spatial_view_cards','no_mirror_rule',
             'marked_general_sightline','first_opaque_stop','output_lock_plaque_arrow']}
