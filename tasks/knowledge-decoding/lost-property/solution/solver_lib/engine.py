"""Read a compound-word diagram exclusively from its pixels."""
from itertools import combinations
from .perception import normalize,dashed_boxes,frames,entities,arrows
from .lexicon import load_relations,load_phrases,solve_domains,NounTaxonomy

def enclosed(entity,frame):
    x,y,r,b=entity['bbox']; a,c,d,f=frame
    return a<x and c<y and r<d and b<f

def solve_page(path):
    mask=normalize(path)
    boxes=dashed_boxes(mask)
    if not boxes:raise ValueError('No dashed word boxes found')
    frame_boxes=frames(mask)
    if not frame_boxes:raise ValueError('No extraction frame found')
    nodes,line_mask=entities(mask,boxes)
    links=arrows(line_mask,nodes,frame_boxes,min(b[1] for b in boxes))
    for link in links:
        if link['frame'] is None and (link['source'] is None or link['target'] is None):
            raise ValueError('A diagram arrow has an unresolved endpoint')
    edges=[(a['source'],a['target']) for a in links if a['source'] is not None and a['target'] is not None]
    if len(set(edges))!=len(edges):raise ValueError('Duplicate arrow trace; geometry is ambiguous')
    unknown={i for i,n in enumerate(nodes) if n['kind']=='box' and n['word'] is None}
    if not unknown:raise ValueError('No missing words found')
    if not unknown<={i for pair in edges for i in pair}:raise ValueError('A missing word has no recognized connections')
    extraction=[]; examples=[]
    for index,frame in enumerate(frame_boxes):
        members={i for i,n in enumerate(nodes) if n['kind']=='box' and enclosed(n,frame)}
        internal=[(a,b) for a,b in edges if a in members and b in members]
        output=[a for a in links if a['frame']==index]
        if len(members)!=2 or len(internal)!=1 or len(output)!=1:
            raise ValueError('A solid frame does not enclose one directed word pair')
        a,b=internal[0]
        if members & unknown:
            extraction.append((a,b))
        else:
            target=output[0]['target']
            if target is None or nodes[target]['word']!=nodes[a]['word']+nodes[b]['word']:
                raise ValueError('The pictured example does not confirm arrow-order concatenation')
            examples.append((a,b))
    if len(extraction)!=1:raise ValueError('Expected one unresolved extraction frame')
    forward,backward=load_relations(); phrases=load_phrases(); taxonomy=NounTaxonomy()
    # No completed frame is required. Recover the convention from
    # printed, asymmetric lexical connections, wherever they occur on the page.
    calibration=[(a,b) for a,b in edges
                 if nodes[a]['word'] and nodes[b]['word']
                 and nodes[a]['kind']!='icon' and nodes[b]['kind']!='icon']
    if not calibration:raise ValueError('No printed connection calibrates word order')
    if not all(nodes[b]['word'] in forward[nodes[a]['word']] for a,b in calibration):
        raise ValueError('Printed calibration is not a lexical concatenation')
    if not any(nodes[a]['word'] not in forward[nodes[b]['word']] for a,b in calibration):
        raise ValueError('Printed calibration does not determine arrow order')
    grounded_edges=[(a,b) for a,b in edges if nodes[b]['kind']=='icon']
    # Dictionaries omit some separately written phrases. Systematically relax
    # every possible edge, in increasing number of phrase witnesses, not a
    # page-specific list of missing relations.
    valid={}; witnesses={}
    for relaxed_count in range(3):
        for relaxed in combinations(edges,relaxed_count):
            candidates=solve_domains(nodes,edges,forward,backward,relaxed=set(relaxed),phrases=phrases)
            for assignment in candidates:
                if not all(taxonomy.is_kind_of(assignment[a]+assignment[b],assignment[b]) for a,b in grounded_edges):
                    continue
                key=tuple(sorted(assignment.items()))
                valid[key]=assignment;witnesses[key]=relaxed
        if valid:break
    if not valid:raise ValueError('No dictionary-supported solution matches all recognized clues')
    if len(valid)!=1:raise ValueError(f'Clues admit {len(valid)} assignments in the bundled dictionary')
    key,assignment=next(iter(valid.items()))
    a,b=extraction[0];answer=(assignment[a]+assignment[b]).upper()
    trace={
        'entities':[dict(n,bbox=[int(v) for v in n['bbox']],resolved=assignment.get(i,n['word'])) for i,n in enumerate(nodes)],
        'arrows':links,
        'frames':[[int(v) for v in box] for box in frame_boxes],
        'extraction_edge':[a,b],
        'phrase_edges':[list(edge) for edge in witnesses[key]],
        'relations':[[assignment[a],assignment[b]] for a,b in edges],
        'calibration_edges':[list(edge) for edge in calibration],
        'calibration_reverse_rejected':True,
        'assignment_count':len(valid),
        'relaxation_level':relaxed_count,
        'worked_frame_count':len(examples),
    }
    return answer,trace

def solve_directory(directory):
    paths=sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower()=='.png')
    if not paths:raise ValueError('The input directory contains no PNG images')
    results=[solve_page(path) for path in paths]
    answers={answer for answer,trace in results}
    if len(answers)!=1:raise ValueError('The PNG pages produce different answers')
    return next(iter(answers)),{path.name:result[1] for path,result in zip(paths,results)}
