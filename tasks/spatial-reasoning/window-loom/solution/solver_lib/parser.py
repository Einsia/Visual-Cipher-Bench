"""Pixel-derived structural reading of the sheet."""
from pathlib import Path
from PIL import Image
import json
import math
from collections import deque
import numpy as np
from .pixel_utils import components, rgb_mask


FACE_BOXES = {
    'A+':[192,1208,704,1720], 'B+':[704,1208,1216,1720],
    'C+':[704,696,1216,1208], 'D+':[1216,696,1728,1208],
    'A-':[192,1720,704,2232], 'B-':[704,1720,1216,2232],
    'C-':[704,184,1216,696], 'D-':[1216,184,1728,696],
}


class PixelError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise PixelError(message)


class OCR:
    def __init__(self):
        p=Path(__file__).parent/'ocr_character_templates.json'
        self.templates=json.loads(p.read_text())['characters']
        for variants in self.templates.values():
            for t in variants:
                t['mask']=np.unpackbits(np.frombuffer(bytes.fromhex(t['bits']),dtype=np.uint8)).reshape(48,32)

    def char(self, mask, choices=None):
        yy,xx=np.nonzero(mask)
        require(len(xx)>0,'Missing glyph')
        mask=mask[yy.min():yy.max()+1,xx.min():xx.max()+1]
        h,w=mask.shape
        target=np.asarray(Image.fromarray(mask).resize((32,48),Image.Resampling.NEAREST),dtype=np.uint8)
        scores={}
        for char,variants in self.templates.items():
            if choices and char not in choices:continue
            scores[char]=min(float(np.mean(t['mask']!=target))+.15*abs(math.log((w/h)/t['aspect'])) for t in variants)
        char=min(scores,key=scores.get)
        require(scores[char]<.24, 'Unrecognizable glyph: '+str(sorted(scores.items(),key=lambda x:x[1])[:3]))
        return char,round(scores[char],4)

    def compact_line(self, crop, choices=None):
        mask=crop[:,:,0]<140
        edges=np.flatnonzero(np.diff(np.pad(mask.any(axis=0).astype(np.int8),(1,1))))
        try:
            return ''.join(self.char(mask[:,a:b],choices)[0] for a,b in zip(edges[::2],edges[1::2]))
        except PixelError as exc:
            raise PixelError(str(exc)+' in text crop '+str(crop.shape)) from exc


def center(box):
    a,b,c,d=box
    return ((a+c)/2,(b+d)/2)


def face_for(point):
    x,y=point
    return next((f for f,(a,b,c,d) in FACE_BOXES.items() if a<x<c and b<y<d),None)


def within(point,box,pad=0):
    x,y=point;a,b,c,d=box
    return a-pad<=x<c+pad and b-pad<=y<d+pad


def component_bitmap(c, shape):
    m=np.zeros(shape,dtype=bool)
    for a,y,b in c['runs']:m[y,a:b]=True
    return m


def enclosed_areas(component):
    a,b,c,d=component['box']
    boundary=np.zeros((d-b+2,c-a+2),dtype=bool)
    for left,y,right in component['runs']:boundary[y-b+1,left-a+1:right-a+1]=True
    return [q['area'] for q in components(~boundary)
            if q['box'][0]>0 and q['box'][1]>0 and q['box'][2]<boundary.shape[1] and q['box'][3]<boundary.shape[0]]


def parse(image_path):
    arr=np.asarray(Image.open(image_path).convert('RGB'))
    require(arr.shape==(2376,3360,3),'Unexpected canvas size')
    brown=rgb_mask(arr,(17,17,17))
    brown[:,1890:]=False
    comps=components(brown)
    ocr=OCR()
    nodes=[];windows=[];small=[]
    for c in comps:
        a,b,d,e=c['box'];w,h=d-a,e-b;point=center(c['box']);face=face_for(point)
        kind=None
        if face and 100<=w<=220 and 100<=h<=220:
            if brown[b:e,a:d].sum(axis=1).max()>.7*w:
                kind='window'
            elif abs(w-h)<=2:kind='pool'
        elif 160<=w<=180 and 70<=h<=80:
            kind='badge'
        elif 45<=w<=50 and 45<=h<=50 and abs(w-h)<=2 and face:
            kind='switch'
        if kind:
            require(face is not None, 'Extra semantic shape outside a material face: '+str(c['box']))
            require(any(area>.25*w*h for area in enclosed_areas(c)), 'Incomplete enclosing contour: '+str(c['box']))
            obj={'kind':kind,'box':c['box'],'center':list(point),'face':face}
            if kind=='window':windows.append(obj)
            else:nodes.append(obj)
    text_mask=brown.copy()
    for c in components(text_mask):
        a,b,d,e=c['box'];w,h=d-a,e-b
        if face_for(center(c['box'])) and 6<=w<=45 and 22<=h<=40:small.append(c)
    for face in FACE_BOXES:
        require(sum(w['face']==face for w in windows)==1,'Missing/extra complete window on '+face)
        require(sum(n['face']==face and n['kind']=='pool' for n in nodes)==2,'Missing/extra pool on '+face)

    for i,n in enumerate(nodes):
        n['id']=i
        a,b,c,d=n['box'];x,y=n['center'];w,h=c-a,d-b
        if n['kind']=='pool':
            region=arr[b+6:d-6,a+6:c-6]
            inner_frames=[q for q in comps if 52<=q['box'][2]-q['box'][0]<=70
                          and 60<=q['box'][3]-q['box'][1]<=78 and within(center(q['box']),n['box'])]
            if inner_frames:
                require(len(inner_frames)==1,'Ambiguous boxed numeral frame')
                # Read inside the frame, excluding its border and printed baseline.
                cx,cy=map(lambda v:int(round(v)),n['center'])
                mask=rgb_mask(arr[cy-27:cy+23,cx-23:cx+23],(17,17,17))
                require(mask.any(),'A boxed numeral is missing inside its intact frame')
                n['digit'],n['ocr_error']=ocr.char(mask,'0123456789')
            else:
                m=rgb_mask(region,(17,17,17))
                ry,rx=np.mgrid[b+6:d-6,a+6:c-6]
                m &= (rx+.5-x)**2+(ry+.5-y)**2 < (.85*min(w,h)/2)**2
                yy,xx=np.nonzero(m)
                require(len(xx)>300,'Missing start/finish icon')
                require(np.ptp(xx)>30 and np.ptp(yy)>55,'Incomplete start/finish icon')
                parts=components(m)
                holes=sum(len(enclosed_areas(q)) for q in parts)
                n['icon']='lock' if holes>=2 else 'drop'
                if n['icon']=='drop':require(len(parts)==1,'Unrecognizable drop icon')
        elif n['kind']=='badge':
            n['view_code']=ocr.char(arr[int(y)-27:int(y)+27,int(x)-28:int(x)+28,0]<140,'JKLMNPQRS')[0]
        else:
            region=arr[b+7:d-10,a+14:c-14]
            n['hinge']=int(ocr.char(region[:,:,0]<140,'123')[0])
            require(n['hinge'] in (2,3),'A route marks a hinge with no alternate stance')

    for win in windows:
        a,b,c,d=win['box'];x,y=win['center']
        # Internal identifier is derived from attachment geometry. No aperture
        # letter is printed and no identity or pair table is loaded.
        win['letter']='window_'+win['face'][0]
        # Find actual square edge centres independently of the midpoint ticks.
        local=brown[b:d,a:c]
        yy=np.flatnonzero(local.sum(axis=1)>.7*(c-a))
        xx=np.flatnonzero(local.sum(axis=0)>.7*(d-b))
        require(len(xx)>=4 and len(yy)>=4,'Incomplete aperture boundary')
        def endpoints(v):
            return [float(v[v<np.mean(v)].mean()),float(v[v>np.mean(v)].mean())]
        xe,ye=endpoints(xx),endpoints(yy)
        win['cut_box']=[a+xe[0]+.5,b+ye[0]+.5,a+xe[1]+.5,b+ye[1]+.5]
    letters={w['letter'] for w in windows}
    require(len(letters)==4,'Window identity count is not four')
    for letter in letters:
        match=[w for w in windows if w['letter']==letter]
        require(len(match)==2 and match[0]['face'][0]==match[1]['face'][0], 'Mismatched front/back window labels')

    graphs={};component_records=[];arrow_records=[]
    for face,box in FACE_BOXES.items():
        a,b,c,d=box
        colored=rgb_mask(arr[b:d,a:c],(153,153,153))
        yy,xx=np.mgrid[b:d,a:c]
        on_face=[n for n in nodes if n['face']==face]
        touch_masks={}
        for n in on_face:
            l,t,r,bt=n['box'];cx,cy=n['center']
            if n['kind']=='pool':
                radius=(r-l+bt-t)/4
                dist=(xx+.5-cx)**2+(yy+.5-cy)**2
                occupied=dist<=radius**2
                adjacent=dist<=(radius+2)**2
            elif n['kind']=='switch':
                # The complete printed switch includes its two curved arrows.
                occupied=(xx>=l-5)&(xx<r+5)&(yy>=t-18)&(yy<bt+18)
                adjacent=(xx>=l-7)&(xx<r+7)&(yy>=t-20)&(yy<bt+20)
            else:
                occupied=(xx>=l)&(xx<r)&(yy>=t)&(yy<bt)
                adjacent=(xx>=l-2)&(xx<r+2)&(yy>=t-2)&(yy<bt+2)
            colored[occupied]=False
            touch_masks[n['id']]=adjacent&~occupied
        graph={n['id']:[] for n in on_face}
        stored_components={}
        for k,comp in enumerate(components(colored)):
            if comp['area']<5:continue
            touched=[]
            for node_id,touch in touch_masks.items():
                hits=sum(int(touch[y,l:r].sum()) for l,y,r in comp['runs'])
                if hits>=2:touched.append(node_id)
            if not touched:continue
            key='component_'+face+'_'+str(k)
            graph[key]=touched
            for node_id in touched:graph[node_id].append(key)
            stored_components[key]=comp
            component_records.append({'component':key,'nodes':touched,'area':comp['area'],
                                      'box':[comp['box'][0]+a,comp['box'][1]+b,comp['box'][2]+a,comp['box'][3]+b]})
        graphs[face]=graph
        # Directed flow is recovered from the opposite-color arrows themselves.
        distance={n['id']:0 for n in on_face if n['kind']=='badge'}
        queue=deque(distance)
        while queue:
            u=queue.popleft()
            if isinstance(u,int) and nodes[u]['kind']=='pool':continue
            for v in graph[u]:
                if v not in distance:distance[v]=distance[u]+1;queue.append(v)
        label_map=np.full(colored.shape,-1,dtype=np.int32)
        comp_keys=list(stored_components)
        for k,key in enumerate(comp_keys):
            for l,y,r in stored_components[key]['runs']:label_map[y,l:r]=k
        opposite=rgb_mask(arr[b:d,a:c],(17,17,17))
        field_cache={}
        for arrow in components(opposite):
            l,t,r,bt=arrow['box'];ww,hh=r-l,bt-t
            if not (7<=ww<60 and 7<=hh<60 and arrow['area']>45):continue
            cx,cy=(l+r)/2+a,(t+bt)/2+b
            if any(within((cx,cy),n['box'],20 if n['kind']=='switch' else 5) for n in on_face):continue
            region=label_map[max(0,t-2):min(bt+2,d-b),max(0,l-2):min(r+2,c-a)]
            labels,counts=np.unique(region[region>=0],return_counts=True)
            if not len(labels):continue
            k=int(labels[np.argmax(counts)]);key=comp_keys[k]
            points=np.array([(x+.5,y+.5) for ll,y,rr in arrow['runs'] for x in range(ll,rr)])
            centered=points-points.mean(axis=0)
            cov=centered.T@centered
            _,vectors=np.linalg.eigh(cov);axis=vectors[:,-1]
            across=np.array([-axis[1],axis[0]])
            along=centered@axis;cross=centered@across
            low,high=along.min(),along.max();widths=[]
            for lo,hi in zip(np.linspace(low,high,9)[:-1],np.linspace(low,high,9)[1:]):
                values=cross[(along>=lo)&(along<=hi)]
                widths.append(float(np.ptp(values)) if len(values) else 0)
            # A head has an abrupt broad base and tapers toward its tip.
            # The shaft extends to the rounded tip in this printed arrow style.
            jumps=np.diff(widths)
            if jumps[np.argmax(np.abs(jumps))]<0:axis=-axis;along=-along;low,high=-high,-low
            require(max(widths)>5,'Unclear flow arrow shape: '+str((face,arrow['box'],widths)))
            if key not in field_cache:
                targets=[n for n in graph[key] if n in distance]
                require(targets,'Arrow component has no downstream instruction')
                goal=min(targets,key=distance.get)
                component_mask=label_map==k
                yy0,xx0=np.nonzero(component_mask&touch_masks[goal])
                require(len(xx0)>0,'No terminal contact for arrow path')
                field=np.full(colored.shape,-1,dtype=np.int32);q=deque()
                for y,x in zip(yy0,xx0):field[y,x]=0;q.append((int(y),int(x)))
                while q:
                    y,x=q.popleft()
                    for dy,dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                        ny,nx=y+dy,x+dx
                        if 0<=ny<field.shape[0] and 0<=nx<field.shape[1] and component_mask[ny,nx] and field[ny,nx]<0:
                            field[ny,nx]=field[y,x]+1;q.append((ny,nx))
                field_cache[key]=field
            field=field_cache[key]
            samples=[]
            for fraction in (.15,.85):
                point=points.mean(axis=0)+axis*(low+(high-low)*fraction)
                xp,yp=point
                ys,xs=np.nonzero((field>=0)&((xx-a+.5-xp)**2+(yy-b+.5-yp)**2<110))
                require(len(xs)>0,'Flow arrow is not supported by a continuous stream: '+str((face,arrow['box'],key,point.tolist())))
                nearest=np.argmin((xs+.5-xp)**2+(ys+.5-yp)**2)
                samples.append(int(field[ys[nearest],xs[nearest]]))
            require(samples[1]<samples[0]-3,'Flow arrow points away from its instruction: '+str((face,arrow['box'],samples)))
            arrow_records.append({'face':face,'box':[l+a,t+b,r+a,bt+b],'component':key,
                                  'direction':axis.tolist(),'distance_to_instruction':samples})
    for n in nodes:
        if n['kind']!='pool':continue
        graph=graphs[n['face']];found=[]
        def visit(k,seen,marks):
            if k in seen:return
            seen=seen|{k}
            if isinstance(k,int) and k!=n['id']:
                obj=nodes[k]
                if obj['kind']=='pool':return
                if obj['kind']=='badge':
                    found.append((k,tuple(marks)));return
                if obj['kind']=='switch':marks=marks+[obj['hinge']]
            for dest in graph[k]:visit(dest,seen,marks)
        visit(n['id'],set(),[])
        found=sorted(set(found))
        if n.get('icon')=='lock':require(not found,'Terminal lock has an outgoing route')
        else:
            require(len(found)==1,'Missing or ambiguous continuous route: '+str((n,found)))
            dest,marks=found[0]
            require(len(marks)<=1,'More than one switch on one route')
            n['view_code']=nodes[dest]['view_code'];n['switches']=list(marks);n['badge_id']=dest
            require(any(ar['face']==n['face'] for ar in arrow_records),'No readable flow direction on material face')
    return {'windows':windows,'nodes':nodes,'components':component_records,'flow_arrows':arrow_records}


