"""Read public PNG glyphs and recover the unprinted example data geometrically.

fields/geometry are sampling locations and alphabets, never clue values.
No numeric instance or answer is stored or opened.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .pixels import Reader

def runs(xs):
    out=[]
    for x in xs:
        if not out or x>out[-1][-1]+1:out.append([int(x)])
        else:out[-1].append(int(x))
    return [int(round(np.mean(q))) for q in out]

def parse(path,geometry=True):
    with Image.open(path) as im:
        if im.info:raise ValueError('PNG must not contain metadata')
    r=Reader(path)
    if r.image.size!=(1700,2193):raise ValueError('Unexpected canvas')
    rgb=np.asarray(r.image)
    if np.max(rgb.max(axis=2)-rgb.min(axis=2))>3:raise ValueError('Nonmonochrome page')
    fields=json.loads(Path(__file__).with_name('fields.json').read_text())
    v={f['id']:r.read(f['id'],f['region'],f['allowed'],f['size']) for f in fields}
    if any(q['glyph_height_px'] is not None and q['glyph_height_px']<19 for q in r.reads):raise ValueError('Required glyph too small')
    def t(i):return v['text_'+str(i)]
    def ref(i,side):
        q=t(i)
        if len(q)!=2 or q[0]!=side or q[1] not in '12345':raise ValueError('Bad reference '+q)
        return int(q[1])-1
    nums_a=[int(t(141+4*i)) for i in range(14)]
    refs_a=[ref(143+4*i,'B') for i in range(14)]
    nums_b=[int(t(202+4*i)) for i in range(14)]
    refs_b=[ref(204+4*i,'A') for i in range(14)]
    from .graph import read_cards
    cards,graph_evidence=read_cards(v)
    if len({(c['a'],c['b']) for c in cards})!=15:raise ValueError('Repeated pair')
    if any(len(c['letter'])!=1 or not c['letter'].isupper() for c in cards):raise ValueError('Bad card letter')
    for i,side in [(199,'A'),(260,'B')]:
        if t(i)!='{'+','.join(side+str(j) for j in range(1,6))+'}':raise ValueError('Bad inventory')
    if (t(139),t(200))!=('A','B'):raise ValueError('Missing tape names')
    # Infer unit boundaries and black chosen cuts by scanning the tapes.
    exnums=[[int(t(i)) for i in [4,8,12,16]],[int(t(i)) for i in [30,34,38]]]
    exrefs=[[t(i) for i in [6,10,14,18]],[t(i) for i in [32,36,40]]]
    names=[[t(22),t(27)],[t(44),t(49)]]
    lens={};sums={};refs={};partitions=[]
    for side,(left,right) in enumerate([(270,710),(1030,1360)]):
        # A digit is not a full-height vertical stroke. Grid lines are gray;
        # thick cuts and outside frames are black.
        crop=r.gray[520:576,left-3:right+4]
        grid=runs(np.flatnonzero((crop<210).all(axis=0))+left-3)
        cuts=runs(np.flatnonzero((crop<128).all(axis=0))+left-3)
        if len(grid)!=len(exnums[side])+1 or len(cuts)!=len(names[side])+1:raise ValueError('Invalid example divisions')
        unit=np.diff(grid)
        if max(unit)-min(unit)>2:raise ValueError('Unequal example unit cells')
        ends=[min(range(len(grid)),key=lambda i:abs(grid[i]-x)) for x in cuts]
        if any(abs(grid[e]-x)>2 for e,x in zip(ends,cuts)):raise ValueError('Cut misses cell edge')
        for name,lo,hi in zip(names[side],ends,ends[1:]):
            lens[name]=hi-lo;sums[name]=sum(exnums[side][lo:hi]);refs[name]=exrefs[side][hi-1]
        partitions.append(dict(grid=grid,cuts=cuts,cell_indices=ends,names=names[side]))
    if len(lens)!=4 or set(lens)!=set(refs.values()):raise ValueError('Bad example names')
    if [t(354),t(356)]!=names[0] or [t(361),t(363)]!=names[1]:raise ValueError('Name inventory disagrees')
    col=[t(i) for i in [90,91,92,93]]
    initial=[int(t(i)) for i in [95,97,99,101]]
    if initial!=[sums[n] for n in col]:raise ValueError('Initial sums disagree with cells')
    inv=[tuple(t(i+k) for k in [0,2,4]) for i in [368,374,380]]
    exe=[tuple(t(i+k) for k in [0,2,4]) for i in [386,396,406]]
    if sorted(inv)!=sorted(exe) or [inv[i] for i in [1,2,0]]!=exe:raise ValueError('Not use-once')
    from .structure import check_structure
    structure=check_structure(r,fields) if geometry else None
    # Decode the two area panels from full vertical/horizontal strokes.
    panels=[]
    for left,right,top,bottom in [(790,836,770,816),(1160,1242,734,816)]:
        crop=r.gray[top:bottom,left:right]
        vert=runs(np.flatnonzero((crop[7:-7]<210).all(axis=0))+left)
        horiz=runs(np.flatnonzero((crop[:,7:-7]<210).all(axis=1))+top)
        if len(vert)<2 or len(horiz)<2:raise ValueError('Missing area boundary/grid')
        spacings=list(np.diff(vert))+list(np.diff(horiz))
        if min(spacings)<30 or max(spacings)-min(spacings)>2:raise ValueError('Area cells not square')
        panels.append(dict(width=len(vert)-1,height=len(horiz)-1,vertical=vert,horizontal=horiz))
    # Frame correspondence: single marks r(B1), double marks r(A1).
    # Full reference paths and frame outlines have already been pixel checked.
    # Read the names at the actual width dimensions; no factor values stored.
    by_pos={tuple(f['region']):v[f['id']] for f in fields}
    area_text=[(f,v[f['id']]) for f in fields if f['id'].startswith('area_')]
    width_names=[q for f,q in sorted(area_text,key=lambda z:z[0]['region'][0]) if f['region'][1]>835]
    if len(width_names)!=2:raise ValueError('Missing width names')
    a,b=exe[0][1:]
    if width_names!=[a,b]:raise ValueError('Areas must correspond to the first card')
    for panel,own,target in zip(panels,[a,b],[refs[b],refs[a]]):
        if (panel['width'],panel['height'])!=(lens[own],lens[target]):raise ValueError('Area dimensions disagree with framed source lengths')
    expected_words=['Areas','Sums','A1+B1','=','+']
    words=[q for f,q in area_text if f['region'][1]<835]
    if sorted(words)!=sorted(expected_words):raise ValueError('Area/sum relation unreadable')
    if sum(p['width']*p['height'] for p in panels)!=sums[a]+sums[b]:raise ValueError('Areas do not balance current totals')
    # Blank states are inferred by reading the checked directed connections.
    strokes=json.loads(Path(__file__).with_name('geometry.json').read_text())
    arrows={s['command_id']:s['line'] for s in strokes if 'arrow' in s}
    states=[initial];trace=[]
    xs=[1070,1205,1340,1475]
    for k,(letter,a,b) in enumerate(exe):
        lhs=sums[a]+sums[b];rhs=lens[a]*lens[refs[b]]+lens[b]*lens[refs[a]]
        if lhs!=rhs:raise ValueError('Inferred example transition fails')
        before=[sums[n] for n in col];after=[None]*4
        for j in range(4):
            x,y,xx,yy=arrows['old_'+str(102+12*k+j)]
            src=xs.index(int(x));dst=xs.index(int(xx));after[dst]=before[src]
        want=before.copy();ia,ib=col.index(a),col.index(b);want[ia],want[ib]=want[ib],want[ia]
        if after!=want:raise ValueError('State arrows do not exchange selected sums')
        states.append(after);sums=dict(zip(col,after))
        if t(415+3*k)!=letter:raise ValueError('Wrong chronological extraction')
        # Interior of every later state must be genuinely empty.
        for x in xs:
            if (r.gray[1045+95*k:1082+95*k,x-24:x+24]<210).any():raise ValueError('Unexpected value in blank state')
        trace.append(dict(card=letter,lhs=lhs,rhs=rhs,before=before,after=after))
    # The rejected initial A is inferred, not printed.
    a,b=exe[1][1:];initial_map=dict(zip(col,initial))
    if initial_map[a]+initial_map[b]==lens[a]*lens[refs[b]]+lens[b]*lens[refs[a]]:raise ValueError('Example fails to distinguish current and static sums')
    return dict(nums_a=nums_a,refs_a=refs_a,nums_b=nums_b,refs_b=refs_b,cards=cards,graph=graph_evidence,reads=r.reads,structure=structure,
                example=dict(partitions=partitions,lengths=lens,references=refs,area_panels=panels,states=states,trace=trace,
                inferred_rule='V(a)+V(b)=L(a)*L(r(b))+L(b)*L(r(a)); then exchange V(a),V(b)'))
