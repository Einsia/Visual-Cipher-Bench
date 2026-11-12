"""Connected components and content-relative image normalization."""
from PIL import Image
import numpy as np
from collections import defaultdict

def components(mask):
    # Run length connected components, with 8-connectivity.
    parents=[]; runs=[]; previous=[]
    def root(a):
        while parents[a]!=a:
            parents[a]=parents[parents[a]]; a=parents[a]
        return a
    for y,row in enumerate(mask):
        delta=np.diff(np.pad(row.astype(np.int8),(1,1)))
        starts=np.flatnonzero(delta==1); ends=np.flatnonzero(delta==-1)
        current=[]; k=0
        for x0,x1 in zip(starts,ends):
            i=len(parents); parents.append(i)
            while k<len(previous) and previous[k][1]<x0: k+=1
            j=k
            while j<len(previous) and previous[j][0]<=x1:
                parents[root(previous[j][2])]=root(i); j+=1
            runs.append((int(y),int(x0),int(x1),i)); current.append((x0,x1,i))
        previous=current
    groups=defaultdict(list)
    for y,x0,x1,i in runs: groups[root(i)].append((y,x0,x1))
    result=[]
    for rr in groups.values():
        result.append({'bbox':(min(r[1] for r in rr),rr[0][0],max(r[2] for r in rr),rr[-1][0]+1),'area':sum(r[2]-r[1] for r in rr),'runs':rr})
    return result

def normalize(path):
    with Image.open(path) as source:
        if source.format!='PNG': raise ValueError('Input must be a PNG image')
        rgba=source.convert('RGBA')
        im=Image.alpha_composite(Image.new('RGBA',rgba.size,'white'),rgba).convert('L')
    a=np.array(im); ys,xs=np.where(a<180)
    if not len(xs): raise ValueError('The PNG contains no visible diagram')
    im=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
    im=im.resize((1400,round(im.height*1400/im.width)),Image.Resampling.LANCZOS)
    return np.array(im)<160

