"""Read actual raster cells and arrowheads.
The class bank contains individual drawings and all 100 two-digit seal labels.
It contains neither page crops nor positioned answers. Geometry locates cells;
classification and arrow direction always depend on the input pixels.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from .structure import inspect
ROOT=Path(__file__).resolve().parent

def classify(a,templates):
    scores=[]
    for label,t in templates:
        scores.append((float(np.mean(np.abs(a.astype(float)-t))),label))
    scores.sort()
    if scores[0][0]>8 or scores[1][0]-scores[0][0]<.25:
        raise ValueError(f'Unrecognised or ambiguous raster cell: {scores[:3]}')
    return scores[0][1],scores[0][0],scores[1][0]

def read(images):
    bank=[]
    for p in sorted((ROOT/'templates').glob('*.png')):
        bank.append((p.stem,np.asarray(Image.open(p).convert('L'))))
    files=sorted(Path(images).glob('*.png'))
    if len(files)!=2:raise ValueError('Expected both stock sheets')
    edges=[];seals=set();pictures=set();trace=[];start=None;pages=[]
    for p in files:
        im=Image.open(p).convert('L')
        if im.size!=(1600,2000):raise ValueError('Unsupported raster dimensions')
        a=np.asarray(im)
        pages.append(a)
        for row in range(4):
            for col in range(2):
                x=80+740*col;y=330+290*row
                items=[];recognitions=[]
                for k in range(3):
                    xx=x+30+240*k;yy=y+54
                    label,best,nextbest=classify(a[yy:yy+160,xx:xx+160],bank)
                    if label.startswith('seal_'):
                        token=str(int(label[5:]));seals.add(token)
                    else:token='@'+label[5:];pictures.add(token)
                    items.append(token);recognitions.append({'class':label,'mae':best,'next_mae':nextbest})
                directions=[]
                for k in range(2):
                    xx=x+202+240*k;cy=y+134
                    # A filled triangular head has off-axis ink; the shaft doesn't.
                    patch=a[cy-11:cy+12,xx-1:xx+58]<128
                    patch[8:15,:]=False
                    left=int(patch[:,:23].sum());right=int(patch[:,35:].sum())
                    if max(left,right)<40 or abs(left-right)<30:raise ValueError('No clear arrowhead')
                    d=1 if right>left else -1;directions.append(d)
                    u,v=items[k:k+2]
                    edges.append((u,v) if d==1 else (v,u))
                trace.append({'file':p.name,'row':row,'column':col,'nodes':items,'directions':directions,'recognition':recognitions})
        # Read the labelled starting circle from either sheet, using just numeral ink.
        # Register on sheet I is at a different location; its matching error is high.
        crop=a[1620:1670,190:250]
        ys,xs=np.where(crop<128)
        if len(xs)>10:
            ink=crop[ys.min():ys.max()+1,xs.min():xs.max()+1]
            ink=np.asarray(Image.fromarray(ink).resize((64,40),Image.Resampling.BILINEAR))
            scored=[]
            for label,t in bank:
                if not label.startswith('seal_'):continue
                q=t[20:65,30:130];qy,qx=np.where(q<128)
                q=q[qy.min():qy.max()+1,qx.min():qx.max()+1]
                q=np.asarray(Image.fromarray(q).resize((64,40),Image.Resampling.BILINEAR))
                scored.append((float(np.abs(ink.astype(float)-q).mean()),label))
            scored.sort()
            if scored[0][0]<18:
                if start is not None:raise ValueError('Multiple route start labels')
                start=str(int(scored[0][1][5:]))
    if start is None or start not in seals:raise ValueError('Missing route start')
    vocab=json.loads((ROOT/'picture_vocabulary.json').read_text())
    structure=inspect(pages[0],pages[1],bank,seals,start)
    return {'seals':sorted(seals,key=int),'picture_domains':{p:vocab[p[1:]] for p in pictures},'edges':edges,'start':start,'visual_structure':structure},trace
