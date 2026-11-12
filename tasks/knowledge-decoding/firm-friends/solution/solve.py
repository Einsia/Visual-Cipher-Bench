#!/usr/bin/env python3
"""Recover the puzzle from PNG pixels, then solve all free placements.

Runtime resources are isolated pictogram/glyph vocabularies, naming alternatives,
and general dictionaries. Only the puzzle PNGs and these resources are read.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'solver_lib'))
from pixels import parse
from engine import pair_first
from geometry import restore

def solve(images):
    model,observations=parse(images)
    result=pair_first(model,Path(__file__).parent/'solver_lib'/'cmudict.dict')
    answers=result['answers']
    restorations={tuple(map(tuple,restore([p[k] for p in sol['pairs'] for k in ('entry_i','entry_j')],model['occupied']))) for sol in result['solutions']}
    if len(restorations)!=1:raise ValueError('Missing boundaries are not uniquely recoverable')
    direction_maps={tuple(sorted((p['source_'+k],p['entry_'+k]['dx'],p['entry_'+k]['dy']) for p in sol['pairs'] for k in ('i','j'))) for sol in result['solutions']}
    pairings={tuple(sorted(tuple(sorted((p['source_i'],p['source_j']))) for p in sol['pairs'])) for sol in result['solutions']}
    if len(direction_maps)!=1 or len(pairings)!=1:raise ValueError('Directions or spatial pairing are not uniquely recoverable')
    return {'direction_map_count':len(direction_maps),'pairing_count':len(pairings),'valid':len(answers)==1,'unique':len(answers)==1,'solution_count':len(answers),
            'answer':answers[0] if len(answers)==1 else None,'answers':answers,
            'restoration_count':len(restorations),'restored_horizontal_boundaries':[list(t) for t in sorted(restorations)],'observations':observations,'search':result}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    try:result=solve(a.images)
    except Exception as exc:result={'valid':False,'unique':False,'solution_count':0,'answer':None,'error':str(exc)}
    Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ['observations','search']}))
    sys.exit(0 if result['valid'] else 1)
