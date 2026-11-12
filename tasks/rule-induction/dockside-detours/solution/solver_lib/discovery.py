"""Fit complete observed intervals; intermediate actions are inferred."""
from .model import rule_family,rule_fits

def canonical(rule):
    # For an n-position ring, moving -(n-h) is exactly moving +h modulo n.
    r=dict(rule)
    if r['hop']=='unchanged' and r['offset']==0:
        r['hop']='changed';r['direction']=-r['direction']
    return tuple(sorted(r.items()))

def search(demonstrations):
    family=list(rule_family());individual=[];sets=[]
    for d in demonstrations:
        ids=[i for i,r in enumerate(family) if rule_fits(r,[d])]
        sets.append(set(ids));individual.append(len(ids))
    ids=set.intersection(*sets)
    survivors=[family[i] for i in sorted(ids)]
    classes={canonical(r) for r in survivors}
    return dict(searched=len(family),survivors=survivors,
        semantic_classes=len(classes),individual_survivor_counts=individual,
        individual_semantic_classes=[len({canonical(family[i]) for i in ids}) for ids in sets],
        individual_survivors=[[family[i] for i in sorted(ids)] for ids in sets],
        scope='All printed letters, counts, pointer circles and actual time labels are matched by repeated transitions; intermediate states are derived, never supplied. Updated/before/initial selection, old/new keys, six comparisons, self/zero membership, three rotation directions, two hop origins, six hop quantities, two walk directions and two counting offsets.',
        equivalence_proof='If h positions change, n-h are unchanged. Anticlockwise n-h from the same origin equals clockwise h modulo n for every n and every state. These two descriptions are the same dynamics, not distinct solutions.')
