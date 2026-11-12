"""Read glyphs, object silhouettes, and the directed diagram from PNG pixels."""
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DATA = Path(__file__).parent

@dataclass
class Component:
    box: tuple
    area: int
    runs: list

@dataclass
class Token:
    box: tuple
    value: str
    score: float
    kind: str = 'text'


def components(ink):
    """8-connected components using row runs; no scipy dependency."""
    parent, runs, previous = [], [], []
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for y, row in enumerate(ink):
        padded = np.r_[False, row, False]
        changes = np.flatnonzero(padded[1:] != padded[:-1])
        current = []
        for x0, x1 in zip(changes[::2], changes[1::2]):
            i = len(parent)
            parent.append(i)
            runs.append((int(x0), y, int(x1), y + 1))
            current.append(i)
            for j in previous:
                a, _, b, _ = runs[j]
                if b < x0:
                    continue
                if a > x1:
                    break
                parent[root(i)] = root(j)
        previous = current
    groups = defaultdict(list)
    for i, run in enumerate(runs):
        groups[root(i)].append(run)
    result = []
    for group in groups.values():
        a = np.array(group)
        area = int(sum(r[2] - r[0] for r in group))
        if area >= 3:
            result.append(Component((int(a[:, 0].min()), int(a[:, 1].min()),
                                     int(a[:, 2].max()), int(a[:, 3].max())), area, group))
    return result


def crop(ink, box):
    x0, y0, x1, y1 = box
    return ink[y0:y1, x0:x1]


def union_box(items):
    boxes = [i.box for i in items]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def trimmed(a):
    y, x = np.nonzero(a)
    if not len(y):
        raise ValueError('Empty glyph')
    return a[y.min():y.max()+1, x.min():x.max()+1]


def normalized(a, size=(40, 56)):
    im = Image.fromarray(np.uint8(trimmed(a))*255).resize(size, Image.Resampling.LANCZOS)
    return np.array(im, dtype=float)/255


class OCR:
    def __init__(self):
        self.glyphs = {}
        font = ImageFont.truetype(str(DATA / 'DejaVuSansMono.ttf'), 100)
        for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=?':
            im = Image.new('L', (180, 180))
            ImageDraw.Draw(im).text((20, 10), ch, font=font, fill=255)
            a = trimmed(np.array(im)>100)
            self.glyphs[ch] = (normalized(a), a.shape[1]/a.shape[0])

    def glyph(self, a):
        a = trimmed(a)
        n = normalized(a)
        aspect = a.shape[1]/a.shape[0]
        scores = []
        for ch, (template, ratio) in self.glyphs.items():
            score = float(np.mean(np.abs(n-template))) + .13*abs(math.log(aspect/ratio))
            scores.append((score, ch))
        return min(scores)

    def word(self, a):
        occupied = np.any(a, axis=0)
        changes = np.flatnonzero(np.r_[False, occupied, False][1:] !=
                                 np.r_[False, occupied, False][:-1])
        letters = [self.glyph(a[:, x0:x1]) for x0, x1 in zip(changes[::2], changes[1::2])]
        return ''.join(ch for _, ch in letters), max(s for s, _ in letters)


def icon_kind(a, text_height):
    """Generic line-art morphology. Labels are object categories, not row labels.

    Speaker: closed cone and detached sound arcs. String ball: dense round
    winding and a short loose end. Cereal ear: narrow, branched seed head.
    Ray: broad wings, sparse outline, and a narrow trailing tail.
    Reject unknown artwork instead of assigning it by its location.
    """
    a = trimmed(a)
    h, w = a.shape
    if h < text_height*1.65:
        return None
    aspect, density = w/h, float(a.mean())
    pieces = components(a)
    widths = a.sum(axis=1)
    # A speaker has a separate cone, an inner arc, and an outer arc.
    if .8 < aspect < 1.4 and .10 < density < .32 and len(pieces) == 3:
        ordered = sorted(pieces, key=lambda c:c.box[0])
        cone, inner, outer = ordered
        if (cone.area > inner.area*2 and cone.box[2] < inner.box[0]
                and outer.box[3]-outer.box[1] > (inner.box[3]-inner.box[1])*1.3):
            return 'speaker'
    # Dense crossing strands occupy the upper round part of a ball of string.
    if .65 < aspect < 1.10 and .32 < density < .65:
        upper, lower = a[:int(h*.7)], a[int(h*.8):]
        if upper.mean() > lower.mean()*1.7:
            return 'string_ball'
    # The narrow cereal head has many paired branches and a central stalk.
    if .36 < aspect < .70 and .24 < density < .62:
        center = a[:, int(w*.30):int(w*.70)]
        if np.mean(np.any(center, axis=1)) > .75:
            return 'cereal_ear'
    # Ray wings span the upper half, tapering to a curved, narrow tail.
    if 1.05 < aspect < 1.65 and .10 < density < .30:
        spans=[]
        for row in a:
            xs=np.flatnonzero(row)
            spans.append(xs[-1]-xs[0]+1 if len(xs) else 0)
        if np.mean(spans[int(h*.65):]) < np.mean(spans[int(h*.15):int(h*.55)])*.65:
            return 'ray'
    return None


from collections import deque


def component_mask(c):
    x0,y0,x1,y1=c.box
    out=np.zeros((y1-y0,x1-x0),dtype=bool)
    for a,y,b,_ in c.runs:out[y-y0,a-x0:b-x0]=True
    return out


def thin(a):
    a=np.pad(a,1).astype(np.uint8)
    while True:
        count=0
        for phase in (0,1):
            p=[a[:-2,1:-1],a[:-2,2:],a[1:-1,2:],a[2:,2:],a[2:,1:-1],a[2:,:-2],a[1:-1,:-2],a[:-2,:-2]]
            n=sum(p); transitions=sum((p[i]==0)&(p[(i+1)%8]==1) for i in range(8))
            if phase==0: cond=(p[0]*p[2]*p[4]==0)&(p[2]*p[4]*p[6]==0)
            else:cond=(p[0]*p[2]*p[6]==0)&(p[0]*p[4]*p[6]==0)
            remove=(a[1:-1,1:-1]>0)&(n>=2)&(n<=6)&(transitions==1)&cond
            count+=int(remove.sum()); a[1:-1,1:-1][remove]=0
        if not count:break
    return a[1:-1,1:-1].astype(bool)


def arrow_of(c):
    a=component_mask(c);h,w=a.shape
    if max(h,w)<34:return None
    # Orthogonal arrow shafts contain a long straight run; silhouettes do not.
    if max(a.sum(axis=0).max(),a.sum(axis=1).max()) < max(32, max(h,w)*.75):return None
    s=thin(a); padded=np.pad(s,1).astype(int)
    neighbors=sum(padded[dy:dy+h,dx:dx+w] for dy in range(3) for dx in range(3) if (dy,dx)!=(1,1))
    ends=[(int(x),int(y)) for y,x in zip(*np.where(s&(neighbors==1)))]
    groups=[]
    for point in ends:
        for g in groups:
            if min(math.dist(point,q) for q in g)<18:g.append(point);break
        else:groups.append([point])
    if len(groups)!=2:return None
    centers=[tuple(np.mean(g,axis=0)) for g in groups]
    mass=[]
    for x,y in centers:
        x,y=int(round(x)),int(round(y))
        mass.append(int(a[max(0,y-18):min(h,y+19),max(0,x-18):min(w,x+19)].sum()))
    if max(mass)<min(mass)*1.25:return None
    head=int(mass[1]>mass[0]); tail=1-head
    offset=np.array(c.box[:2])
    return {'box':c.box,'start':list(np.array(centers[tail])+offset), 'end':list(np.array(centers[head])+offset),'end_mass':mass}


def rectangles(rgb):
    gray=(rgb[:,:,0]>=140)&(rgb[:,:,0]<=190)
    columns=np.flatnonzero(gray.sum(axis=0)>55)
    edges=[]
    for x in columns:
        ys=np.flatnonzero(gray[:,x]);groups=[]
        for y in ys:
            if groups and y-groups[-1][-1]<=9:groups[-1].append(int(y))
            else:groups.append([int(y)])
        for g in groups:
            if g[-1]-g[0]>55 and len(g)>(g[-1]-g[0])*.85:
                edges.append((int(x),g[0],g[-1]))
    merged=[]
    for x,y,z in edges:
        if merged and x-merged[-1][0]<4 and abs(y-merged[-1][1])<4 and abs(z-merged[-1][2])<4:continue
        merged.append((x,y,z))
    result=[]
    for x,y,z in merged:
        matches=[e for e in merged if e[0]>x+40 and abs(e[1]-y)<4 and abs(e[2]-z)<4]
        if not matches:continue
        xx,_,_=matches[0]
        # Both horizontal boundaries must exist, allowing black crossings.
        dark=rgb[:,:,0]<210
        if all(dark[max(0,yy-2):yy+3,x:xx+1].any(axis=0).mean()>.97 for yy in (y,z)):
            box=(x,y,xx+1,z+1)
            if not any(max(abs(a-b) for a,b in zip(box,prior))<4 for prior in result):
                result.append(box)
    return result


def inside(inner,outer):
    return inner[0]>outer[0] and inner[1]>outer[1] and inner[2]<outer[2] and inner[3]<outer[3]


def point_distance(point,box):
    x,y=point;x0,y0,x1,y1=box
    return math.hypot(max(x0-x,0,x-x1),max(y0-y,0,y-y1))


def read_page(path):
    rgb=np.array(Image.open(path).convert('RGB'));ink=rgb[:,:,0]<100
    comps=components(ink)
    if not comps:raise ValueError('No readable ink components')
    boxes=rectangles(rgb)
    regions=[b for b in boxes if b[3]-b[1]>400]
    frames=[b for b in boxes if b not in regions and min(b[2]-b[0],b[3]-b[1])>70]
    cells=[b for b in boxes if b not in regions and b not in frames]
    if len(regions)!=2 or not cells:raise ValueError('Missing mode regions or letter cells')
    # Empty, individually bordered cells group by proximity and common baseline.
    groups=[]
    for b in sorted(cells,key=lambda b:(b[1],b[0])):
        for g in groups:
            if abs(b[1]-g[-1][1])<4 and 0<b[0]-g[-1][2]<25:
                g.append(b);break
        else:groups.append([b])
    entities=[]
    for g in groups:
        box=(g[0][0],min(b[1] for b in g),g[-1][2],max(b[3] for b in g))
        entities.append({'kind':'operand','box':box,'token':Token(box,'?'*len(g),0,'slots'),'cells':g})
    nodes=[];remaining=[];arrows=[];ports=[]
    for c in comps:
        a=component_mask(c);h,w=a.shape
        if 25<h<40 and .9<w/h<1.1 and .13<a.mean()<.35 and not a[h//2-3:h//2+3,w//2-3:w//2+3].any():
            nodes.append({'box':c.box,'center':[(c.box[0]+c.box[2])/2,(c.box[1]+c.box[3])/2]});continue
        if w>95 and h<5 and any(inside(c.box,r) for r in regions):
            ports.append({'kind':'port','box':c.box});continue
        arrow=arrow_of(c)
        if arrow:arrows.append(arrow)
        else:remaining.append(c)
    if not nodes:raise ValueError('No editing junctions')
    figure_top=min([n['box'][1] for n in nodes]+[b[1] for b in frames])-15
    remaining=[c for c in remaining if c.box[1]>=figure_top]
    arrows=[a for a in arrows if a['box'][1]>=figure_top]
    groups=[]
    for c in sorted(remaining,key=lambda c:c.box[0]):
        for g in groups:
            b=union_box(g)
            if ((-3<=c.box[0]-b[2]<=15 and min(b[3],c.box[3])-max(b[1],c.box[1])>0)
                or (min(b[2],c.box[2])-max(b[0],c.box[0])>0 and -8<min(b[3],c.box[3])-max(b[1],c.box[1])<=0)):
                g.append(c);break
        else:groups.append([c])
    ocr=OCR();tokens=[];ignored=[]
    for g in groups:
        b=union_box(g);a=crop(ink,b);kind=icon_kind(a,24)
        if kind:tokens.append(Token(b,kind,0,'icon'));continue
        value,score=ocr.word(a)
        if score<.29:tokens.append(Token(b,value,score))
        else:ignored.append((value,score,b))
    cell_tokens=[]
    for entity in entities:
        enclosed=[t for t in tokens if inside(t.box,entity['box'])]
        if enclosed:
            enclosed.sort(key=lambda t:t.box[0])
            if len(enclosed)!=len(entity['cells']) or any(t.kind!='text' or len(t.value)!=1 or not t.value.isalpha() for t in enclosed):
                raise ValueError('Malformed filled character cell')
            entity['token']=Token(entity['box'],''.join(t.value.upper() for t in enclosed),max(t.score for t in enclosed))
            cell_tokens.extend(enclosed)
    # Read the printed use-once/closure instruction; never assume it from layout.
    outside=[t for t in tokens if not any(inside(t.box,r) for r in regions)]
    lines=[]
    for t in sorted(outside,key=lambda t:(t.box[3],t.box[0])):
        for line in lines:
            if min(t.box[3],line[0].box[3])-max(t.box[1],line[0].box[1])>5:line.append(t);break
        else:lines.append([t])
    # Two instruction columns share baselines. Split at genuine column gaps,
    # not at word spaces, before recognizing the six public constraints.
    columns=[]
    for line in lines:
        line.sort(key=lambda t:t.box[0]);parts=[]
        for t in line:
            if parts and t.box[0]-parts[-1][-1].box[2]<=90:parts[-1].append(t)
            else:parts.append([t])
        columns.extend(parts)
    lines=columns
    instruction_tokens=[];instructions=[]
    required={'use every edit once','replace in place','return to ?',
              'fit every card','repeats allowed','no turning or resizing'}
    for line in lines:
        line.sort(key=lambda t:t.box[0]);value=' '.join(t.value for t in line if t.value!='-').lower()
        if value in required:
            instructions.append(value);instruction_tokens.extend(line)
    if set(instructions)!=required:
        raise ValueError(f'Missing use-once / closure instructions: {[[t.value for t in line] for line in lines]}')
    modes={};headers=[]
    for region in regions:
        found=[t for t in tokens if inside(t.box,region) and t.value in ('Aa','speaker')]
        if len(found)!=1:raise ValueError('A region lacks a unique mode header')
        modes[region]='sound' if found[0].value=='speaker' else 'letters';headers.extend(found)
    # Picture cards outside the mode regions are a common bank. Empty frames
    # inside a region are operands. Derive their domains by rectangle fit;
    # no picture-to-branch correspondence is supplied by code or coordinates.
    cards=[];frame_tokens=[];empty_frames=[]
    for frame in frames:
        enclosed=[t for t in tokens if inside(t.box,frame)]
        if enclosed:
            if any(inside(frame,r) for r in regions) or len(enclosed)!=1 or enclosed[0].kind!='icon':
                raise ValueError(f'Malformed picture bank card in {path}: {frame}; enclosed={[(t.value,t.kind,t.box) for t in enclosed]}')
            cards.append({'box':frame,'picture':enclosed[0].value})
            frame_tokens.extend(enclosed)
        else:
            if not any(inside(frame,r) for r in regions):raise ValueError(f'Empty bank card {frame}; tokens={[(t.value,t.box) for t in tokens]}')
            empty_frames.append(frame)
    if not cards or len({c['picture'] for c in cards})!=len(cards):raise ValueError('Missing or duplicate bank pictures')
    fit_evidence=[]
    for frame in empty_frames:
        width,height=frame[2]-frame[0],frame[3]-frame[1]
        choices=sorted(c['picture'] for c in cards if c['box'][2]-c['box'][0]<=width+3 and c['box'][3]-c['box'][1]<=height+3)
        if not choices:raise ValueError('No picture fits a frame')
        entities.append({'kind':'operand','box':frame,'token':Token(frame,'|'.join(choices),0,'choice')})
        fit_evidence.append({'box':frame,'choices':choices})
    questions=[]
    for t in tokens:
        if t in headers or t in instruction_tokens or t in cell_tokens or t in frame_tokens or t.value in ('Aa','-'):continue
        if t.value=='?':questions.append(t);continue
        entities.append({'kind':'operand','box':t.box,'token':t})
    entities.extend(ports)
    if len(questions)!=1:raise ValueError(f'Expected one question at a word port: {[(t.value,t.box,t.score) for t in tokens]}; ignored={ignored}')
    q=questions[0]
    ranked=sorted((point_distance((q.box[2],q.box[3]),p['box']),i) for i,p in enumerate(ports))
    if not ranked or ranked[0][0]>75:raise ValueError('Question is disconnected from word ports')
    answer_port=ports[ranked[0][1]];answer_port['answer']=True
    for n in nodes:
        found=[r for r in regions if inside(n['box'],r)]
        n['kind']='node';n['mode']=modes[found[0]] if len(found)==1 else 'letters'
        n['calibration']=not found;entities.append(n)
    for i,e in enumerate(entities):e['id']=i
    def attach(point):
        ranked=sorted((point_distance(point,e['box']),e['id']) for e in entities)
        if ranked[0][0]>85 or (len(ranked)>1 and ranked[1][0]-ranked[0][0]<4):
            raise ValueError(f'Ambiguous or disconnected path endpoint {point}: {ranked[:3]}')
        return ranked[0][1]
    links=[]
    for a in arrows:
        source,target=attach(a['start']),attach(a['end'])
        if source==target:raise ValueError('Arrow has identical endpoints')
        links.append({'source':source,'target':target,**a})
    incoming=defaultdict(list);outgoing=defaultdict(list)
    for l in links:outgoing[l['source']].append(l['target']);incoming[l['target']].append(l['source'])
    orphaned=[e['id'] for e in entities if not incoming[e['id']] and not outgoing[e['id']]]
    if orphaned:raise ValueError(f'Unconnected entities: {orphaned}')
    examples=[];rows=[]
    for n in sorted(nodes,key=lambda n:(n['box'][1],n['box'][0])):
        ins=[entities[i] for i in incoming[n['id']]];outs=[entities[i] for i in outgoing[n['id']]]
        if n['calibration']:
            removed=[e for e in outs if e.get('token') and e['token'].kind=='slots']
            targets=[e for e in outs if e not in removed]
            if len(ins)!=1 or len(removed)!=1 or len(targets)!=1:raise ValueError('Calibration does not form one split')
            examples.append({'mode':'letters','tokens':[ins[0]['token'],Token((0,0,0,0),'-',0),removed[0]['token'],Token((0,0,0,0),'=',0),targets[0]['token']]})
            continue
        inputs=[e for e in ins if e['kind']=='port'];outputs=[e for e in outs if e['kind']=='port']
        if len(inputs)!=1 or len(outputs)!=1:raise ValueError('Edit lacks one input and one output word line')
        parsed=[]
        for sign,neighbors in [('-',outs),('+',ins)]:
            for e in neighbors:
                if e['kind']=='operand':parsed.extend([Token((0,0,0,0),sign,0),e['token']])
                elif e['kind']!='port':raise ValueError('Edits must be separate fragments')
        if not parsed:raise ValueError('Edit has no operand branch')
        rows.append({'mode':n['mode'],'mode_marker':'speaker' if n['mode']=='sound' else 'Aa','tokens':parsed,
                     'box':n['box'],'start':bool(inputs[0].get('answer')),'input_box':inputs[0]['box'],'output_box':outputs[0]['box'],
                     'required_pictures':sorted(c['picture'] for c in cards)})
    if sum(r['start'] for r in rows)!=1:raise ValueError('Question must identify one input')
    for p in ports:
        if len(incoming[p['id']])+len(outgoing[p['id']])!=1:raise ValueError('A word port has multiple links')
    return examples,rows,{'image':str(path),'regions':[{'box':r,'mode':modes[r]} for r in regions],
      'tokens':[(t.value,t.box,round(t.score,3)) for t in tokens], 'ignored':ignored,'instructions':instructions,
      'nodes':nodes,'links':links,'start_edit':next(i for i,r in enumerate(rows) if r['start']),
      'picture_bank':cards,'picture_frames':fit_evidence,
      'letter_cells':[{'box':e['box'],'count':len(e['cells']),'value':e['token'].value,'cells':e['cells']} for e in entities if 'cells' in e],
      'word_ports':[p['box'] for p in ports]}
