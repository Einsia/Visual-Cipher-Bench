"""Offline PNG-only reference solver. Run: solve.py --images DIR --output FILE.
The solver library contains code, a generic search binary, and a generic
font atlas.
"""
import argparse,json,sys,time,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent/'solver_lib'))
from pixels import Reader
from infer import infer,dilate
from search import search
from relay import simulate


def footprint_check(reader,spec,run,pair):
    x0,y0,x1,y1=270,1540,710,1985
    unions=[]
    for k in pair:
        im=Image.new('1',(x1-x0,y1-y0));draw=ImageDraw.Draw(im);st=run['states'][k]
        for i in st['stack']:
            draw.polygon([(round(460+14*x-x0),round(1715+14*y-y0)) for x,y in st['polygons'][i]],fill=1)
        unions.append(np.array(im))
    predicted=unions[0]^unions[1];a=reader.crop(3,(x0,y0,x1,y1));observed=(a>210)&(a<224)
    mismatch=int(np.count_nonzero(predicted&~dilate(observed,2)))+int(np.count_nonzero(observed&~dilate(predicted,2)))
    assert mismatch<80,('Footprint does not match',mismatch)
    return {'interior_pixel_mismatch':mismatch,'boundary_tolerance_pixels':2,'pixels_compared':int(predicted.size)}


def solve(images):
    start=time.perf_counter();reader=Reader(images);key=reader.key();example=reader.example(key)
    inference=infer(reader,example)
    # Dispatch only the rule actually recovered from the pictures. Other winners
    # are rejected, never silently replaced with the intended interpretation.
    if (inference['inferred_rule']!=['below','new_target',3] or inference['first_motion']!=['departed',1,True] or inference['selection_metric']!='exposed'):raise ValueError('Recovered rule is not supported by the exhaustive engine')
    spec=reader.main(key)
    # main() also verifies the circled identities and Exit headings
    # from the PNGs, and checks all nine registration centers in the separated catalog cells.
    assert sum(a['kind']=='registration' for a in reader.audit)==len(spec['cards'])
    inp=reader.footprint_input(spec,1000)
    result=search(spec,mode=1,workers=16,npoints=1000,input_text=inp)
    assert len(result['answers'])==1 and result['lines'],result
    evidence=[]
    for line in result['lines']:
        stack=[int(c)-1 for c in line[1]];qs=[int(c) for c in line[5]]
        run=simulate(spec,stack,initial_quarters=qs)
        assert run['answer']==line[0]
        assert [t['selected'] for t in run['trace']]==[int(c) for c in line[2]]
        assert all(qs[t['selected']-1]==spec['starting_turns']['slot_quarters'][j] for j,t in enumerate(run['trace']))
        pair=list(map(int,line[6:8]));assert len(pair)==2 and 0<=pair[0]<pair[1]<=spec['readings']
        evidence.append({'inferred_checkpoints':pair,'stack_bottom_to_top':[i+1 for i in stack],'initial_quarters':qs,'departures':[t['selected'] for t in run['trace']],'footprint':footprint_check(reader,spec,run,pair)})
    return {'answer':result['answers'][0],'unique':True,'input_source':'PNG pixels only','image_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(images).glob('*.png'))},'inference':inference,'search':result['stats'],'inferred_checkpoint_pairs':sorted({tuple(map(int,l[6:8])) for l in result['lines']}),'checkpoint_pairs_searched':36,'abstract_layer_classes':len(result['lines']),'witnesses':evidence,'transcription':{'main':spec,'example':example},'pixel_read_audit':reader.audit,'elapsed_seconds':time.perf_counter()-start}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    r=solve(args.images);Path(args.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['answer','unique','elapsed_seconds','abstract_layer_classes']}))
