"""PNG-only solver: infer missing correspondences jointly with all glyphs.
"""
import argparse,json,time,sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'solver_lib'))
from joint_model import layers,ABC
from partial_pairing import reconstruct_matching
from pixel_structure import main_structure,example_structure,canonical,arrow_endpoint

def runs(v):
 ids=np.flatnonzero(v)
 return [] if not len(ids) else [r for r in np.split(ids,np.flatnonzero(np.diff(ids)>1)+1) if len(r)]

def recover(images):
 t=time.perf_counter();files=sorted(Path(images).glob('*.png'));choices=[]
 for f in files:
  im=Image.open(f).convert('L');native=np.asarray(im);a=canonical(native);black=a<60;rows=runs(black.sum(axis=1)>1300)
  centers=[int(round(q.mean())) for q in rows]
  if len(centers)==4 and centers[1]-centers[0]>300:choices.append((f,a,centers,native))
 if len(choices)!=1:raise ValueError('Expected one question page with two deep framed views')
 f,a,frames,native=choices[0];black=a<160;ink_black=a<80;at,ab,bt,bb=frames
 def tabs(bottom):
  # Read the two side rails: a routed stem may lengthen the bottom edge.
  spans=runs(black[bottom+18:bottom+28].mean(axis=0)>.4)
  rails=[int(round(r.mean())) for r in spans if 1<=len(r)<=4]
  centers=[int((x+z)/2) for x,z in zip(rails,rails[1:]) if z-x==28]
  if len(centers)<3:raise ValueError('No exposed registration tabs')
  return centers,bottom+30
 aa,ay=tabs(ab);bs,by=tabs(bb);n=len(aa)
 if len(bs)!=n:raise ValueError('Unequal card counts')
 # Distinct row of each arrow, paired by measured endpoints, independent of lane.
 row_data=[]
 for y in range(by+15,2050):
  rr=[r for r in runs(black[y]) if len(r)>=30]
  if rr:
   g=max(rr,key=len);row_data.append((y,int(g[0]),int(g[-1]),len(g)))
 groups=[]
 for q in row_data:
  if not groups or q[0]>groups[-1][-1][0]+1:groups.append([])
  groups[-1].append(q)
 pair={};arrows=[]
 for g in groups:
  width=max(q[3] for q in g);best=[q for q in g if q[3]==width];q=best[0];y=int(round(np.mean([r[0] for r in best])));left,right=q[1:3]
  recovered=arrow_endpoint(a,left,right,y,aa,bs)
  if recovered is None:continue
  i,j,arrow=recovered
  bs[j]=arrow['b']  # Thin arrow tip refines a tab crossed by a grey stem.
  # Full straight/dogleg connectivity is checked from PNG pixels below.
  if i in pair:raise ValueError('Two arrows for one old position')
  pair[i]=j;arrows.append(arrow)
 if not pair or len(set(pair.values()))!=len(pair):raise ValueError('Invalid given arrow correspondence')
 structural=main_structure(a,frames,aa,bs,arrows,native)
 example=example_structure(images,f.name)
 templates=np.load(HERE/'solver_lib/templates332.npz')['templates'];h=templates.shape[1]
 if any(abs(end-start-h)>2 for start,end in [(at,ab),(bt,bb)]):raise ValueError('Unexpected observation height')
 target=[];masks=[]
 for top in [at,bt]:
  band=a[top:top+h];mask=np.ones(a.shape[1],bool)
  for span in runs(np.mean((band>200)&(band<230),axis=0)>.80):
   if len(span)>=20:mask[span]=False
  ink=band<80;ink[:5]=False;ink[-5:]=False;ink[:,:140]=False;ink[:,1560:]=False
  masks.append(mask);target.append(ink)
 masks=np.array(masks)[:,None,:];target=np.array(target)
 raw=layers(templates,[aa,bs]);r=reconstruct_matching(raw,masks,target,pair,tolerance=200)
 if r['solution_count']!=1:raise ValueError('Partial correspondence scene is not unique: '+str(r))
 solution=r['solutions'][0];seq=solution['screen_order'];full_pair=solution['pairing']
 bbpos=[bs[j] for j in full_pair];ds=[b-x for x,b in zip(aa,bbpos)]
 if min(ds)<=0 or len(set(ds))!=n:raise ValueError('Motion is not a positive strict order')
 rank=sorted(range(n),key=lambda i:ds[i],reverse=example['descending']);answer=''.join(seq[i] for i in rank)
 # Only after joint reconstruction may the two views be indexed as linked layers.
 raw=layers(templates,[aa,bbpos])
 r['candidate_sets']=[sorted(set(ch for j,ch in options if j==full_pair[i])) for i,options in enumerate(r['candidate_pairs_and_glyphs'])]
 fitted=np.logical_or.reduce([raw[i,ABC.index(c)] for i,c in enumerate(seq)])&masks
 diff=int(np.count_nonzero(fitted!=target))
 if diff>200:raise ValueError('Rendered ink disagrees with measured scene: '+str(diff))
 return {'answer':answer,'normalization':'upper_compact','unique':True,'solution_count':1,'question_image':f.name,'image_size':[native.shape[1],native.shape[0]],'frames':frames,'tabs':[aa,bs],'paired_b':bbpos,'arrows':arrows,'displacements':ds,'screen_order':seq,'rank_order_one_based':[i+1 for i in rank],'candidate_sets':r['candidate_sets'],'matching':r,'global_search_nodes':r['visited_nodes'],'joint_pixel_error':diff,'opaque_columns':[[[int(q[0]),int(q[-1])+1] for q in runs(~m[0])] for m in masks],'seconds':time.perf_counter()-t,'structure':structural,'example':example,'scope':'Pixel reconstruction from the puzzle images.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args();r=recover(args.images);Path(args.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
