from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import json

ROOT=Path(__file__).resolve().parents[1]
def trim(a):
    yy,xx=np.where(a)
    if not len(xx): raise ValueError('empty glyph')
    return a[yy.min():yy.max()+1,xx.min():xx.max()+1]
def norm(a):
    return np.asarray(Image.fromarray(a.astype('uint8')*255).resize((24,32)))>127
templates={}
for family in ['DejaVuSansMono','DejaVuSans']:
    for size in [28,34]:
        f=ImageFont.truetype(str(ROOT/'solver_lib/fonts'/f'{family}.ttf'),size,layout_engine=ImageFont.Layout.BASIC)
        for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789?+−=–.,':
            im=Image.new('L',(100,100));ImageDraw.Draw(im).text((10,10),ch,font=f,fill=255)
            templates[family,size,ch]=norm(trim(np.asarray(im)>127))

def read(im,box,family='DejaVuSansMono',size=34,alphabet=None):
    x,y,u,v=box;a=np.asarray(im.convert('L'))[y:v,x:u]<128
    cols=a.any(axis=0);starts=np.where(cols&~np.r_[False,cols[:-1]])[0];ends=np.where(cols&~np.r_[cols[1:],False])[0]+1
    out=[]
    for l,r in zip(starts,ends):
        yy=np.where(a[:,l:r].any(axis=1))[0];top,bot=int(yy.min()),int(yy.max()+1)
        t=norm(a[top:bot,l:r]);scores=sorted((float(np.mean(t!=m)),ch)for (ff,ss,ch),m in templates.items()if ff==family and ss==size and (alphabet is None or ch in alphabet))
        out.append({'char':scores[0][1],'box':[int(x+l),y+top,int(x+r),y+bot],'height':bot-top,'error':scores[0][0],'next':scores[1]})
    return out

