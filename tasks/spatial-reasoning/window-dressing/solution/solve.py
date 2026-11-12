"""PNG-only solver for unpaired occluded displays.
Reads frame locations, slats, glyph ink and ordering example from PNGs.
Only generic full-alphabet/font resources are loaded from solver_lib.
"""
import argparse,json,time,sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'solver_lib'))
from joint_model import layers,ABC
from unpaired_model import infer
from pixel_structure import main_structure,example_structure

def runs(v):
 ids=np.flatnonzero(v)
 return [] if not len(ids) else [r for r in np.split(ids,np.flatnonzero(np.diff(ids)>1)+1) if len(r)]

def recover(images):
 t=time.perf_counter();files=sorted(Path(images).glob('*.png'));choices=[]
 for f in files:
  im=Image.open(f).convert('L');a=np.asarray(im);black=a<100;rows=runs(black.sum(axis=1)>1300)
  centers=[int(round(q.mean())) for q in rows]
  if len(centers)==4 and centers[1]-centers[0]>300:choices.append((f,a,centers))
 if len(choices)!=1:raise ValueError('Expected one question page with two deep framed views')
 f,a,frames=choices[0];black=a<160;ink_black=a<80;at,ab,bt,bb=frames
 def tabs(bottom):
  rr=[]
  for y in range(bottom+18,bottom+45):
   row=black[y].copy()
   # Grey registration stems can cross a black tab's bottom edge.
   for gap in runs(~row):
    if len(gap)<=3 and gap[0]>0 and gap[-1]<len(row)-1:
     row[gap]=True
   spans=[r for r in runs(row) if 26<=len(r)<=33]
   if len(spans)>len(rr):rr=spans;yy=y
  if len(rr)<3:raise ValueError('No exposed registration tabs')
  return [int(round((r[0]+r[-1])/2)) for r in rr],yy
 aa,ay=tabs(ab);bs,by=tabs(bb);n=len(aa)
 if len(bs)!=n:raise ValueError('Unequal card counts')
 structural=main_structure(a,frames,aa,bs,[])
 example=example_structure(images,f.name)
 templates=np.load(HERE/'solver_lib/templates340.npz')['templates'];h=templates.shape[1]
 if any(abs(end-start-h)>2 for start,end in [(at,ab),(bt,bb)]):raise ValueError('Unexpected observation height')
 target=[];masks=[]
 for top in [at,bt]:
  band=a[top:top+h];mask=np.ones(a.shape[1],bool)
  for span in runs(np.mean((band>200)&(band<230),axis=0)>.80):
   if len(span)>=20:mask[span]=False
  ink=band<80;ink[:5]=False;ink[-5:]=False;ink[:,:140]=False;ink[:,1560:]=False
  masks.append(mask);target.append(ink)
 masks=np.array(masks)[:,None,:];target=np.array(target)
 raw=layers(templates,[aa,bs]);r=infer(raw,masks,target,tolerance=200)
 if r['solution_count']!=1:raise ValueError('Unpaired scene failed: '+str({'solutions':r['solutions'],'positions':[aa,bs],'view_counts':[v['solution_count'] for v in r['views']]}))
 solution=r['solutions'][0];seq=solution['a'];bbpos=[bs[j] for j in solution['mapping']]
 ds=[b-x for x,b in zip(aa,bbpos)]
 if min(ds)<=0 or len(set(ds))!=n:raise ValueError('Motion is not a positive strict order')
 rank=sorted(range(n),key=lambda i:ds[i],reverse=example['descending']);answer=''.join(seq[i] for i in rank)
 return {'answer':answer,'normalization':'upper_compact','unique':True,'solution_count':1,
  'question_image':f.name,'image_size':[a.shape[1],a.shape[0]],'frames':frames,'tabs':[aa,bs],
  'paired_b':bbpos,'inferred_mapping':solution['mapping'],'displacements':ds,
  'screen_order':seq,'b_screen_order':solution['b'],'rank_order_one_based':[i+1 for i in rank],
  'candidate_sets':[v['candidate_sets'] for v in r['views']],
  'single_view_solution_counts':[v['solution_count'] for v in r['views']],
  'global_search_nodes':sum(v['visited_nodes'] for v in r['views']),
  'joint_pixel_error':solution['pixel_error'],
  'opaque_columns':[[[int(q[0]),int(q[-1])+1] for q in runs(~m[0])] for m in masks],
  'seconds':time.perf_counter()-t,'structure':structural,'example':example,
  'scope':'Independent position sets; no correspondence input, design transcription, answer lookup or distinct-letter assumption; difficulty untested.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args();r=recover(args.images);Path(args.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
