"""Offline PNG-only reference solver.
Both rigid motions, layer update and exit selection are inferred jointly from
opaque rehearsal endpoints. Only PNGs, generic code and font templates are read.
"""
import argparse,json,sys,time,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from pixels import Reader
from layout_map import OBS_ORIGIN,OBS_UNIT,OBS_BOUNDS
from infer import resolve,dilate
from search import search
from relay import simulate


def footprint_check(reader,spec,run):
    x0=int(OBS_ORIGIN[0]+OBS_UNIT*OBS_BOUNDS[0]); x1=int(OBS_ORIGIN[0]+OBS_UNIT*OBS_BOUNDS[1]); y0=int(OBS_ORIGIN[1]+OBS_UNIT*OBS_BOUNDS[2]); y1=int(OBS_ORIGIN[1]+OBS_UNIT*OBS_BOUNDS[3])
    unions=[]
    for k in spec['pair']:
        im=Image.new('1',(x1-x0,y1-y0));draw=ImageDraw.Draw(im);st=run['states'][k]
        for i in st['stack']:
            draw.polygon([(round(OBS_ORIGIN[0]+OBS_UNIT*x-x0),round(OBS_ORIGIN[1]+OBS_UNIT*y-y0)) for x,y in st['polygons'][i]],fill=1)
        unions.append(np.array(im))
    predicted=unions[0]^unions[1];a=reader.crop(3,(x0,y0,x1,y1));observed=(a>210)&(a<224)
    mismatch=int(np.count_nonzero(predicted&~dilate(observed,2)))+int(np.count_nonzero(observed&~dilate(predicted,2)))
    assert mismatch<80,('Footprint does not match',mismatch)
    return {'interior_pixel_mismatch':mismatch,'boundary_tolerance_pixels':2,'pixels_compared':int(predicted.size)}


def solve(images):
    start=time.perf_counter();reader=Reader(images);key=reader.key();example=reader.example(key)
    spec=reader.main(key);inference,result=resolve(reader,example,spec)
    # The rehearsals must select one rule before the main search is invoked.
    assert inference['unique_before_main_search'] and len(inference['candidate_rules'])==1
    if inference['inferred_rule']!=['below','new_target',3]:raise ValueError('Recovered rule is not supported by the exhaustive engine')
    assert len(result['answers'])==1 and result['lines'],result
    evidence=[]
    for line in result['lines']:
        stack=[int(c)-1 for c in line[1]];qs=[int(c) for c in line[5]]
        run=simulate(spec,stack,initial_quarters=qs)
        assert run['answer']==line[0]
        assert [t['selected'] for t in run['trace']]==[int(c) for c in line[2]]
        assert all(qs[t['selected']-1]==spec['starting_turns']['slot_quarters'][j] for j,t in enumerate(run['trace']))
        evidence.append({'stack_bottom_to_top':[i+1 for i in stack],'initial_quarters':qs,'departures':[t['selected'] for t in run['trace']],'footprint':footprint_check(reader,spec,run)})
    return {'answer':result['answers'][0],'unique':True,'input_source':'PNG pixels only','catalog_registration':reader.registration_audit,'image_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(images).glob('*.png'))},'inference':inference,'search':result['stats'],'abstract_layer_classes':len(result['lines']),'witnesses':evidence,'transcription':{'main':spec,'example':example},'pixel_read_audit':reader.audit,'elapsed_seconds':time.perf_counter()-start}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    r=solve(args.images);Path(args.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['answer','unique','elapsed_seconds','abstract_layer_classes']}))
