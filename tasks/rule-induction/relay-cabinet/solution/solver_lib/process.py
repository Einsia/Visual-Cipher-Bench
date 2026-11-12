"""Conditional tag propagation on the existing three-track process.
0=diamond, 1=hexagon, 2=cross. All state arrays are identity-indexed except order.
"""
import itertools
import numpy as np

TRUE_MODEL=(0,0,0,1,1,0,0,0)

def direct(st, bridges, trace=False, variant='current'):
    order=st['order'][:]; faces=st['faces'][:]; rec=st['records'][:]; hist=[]
    for lane,side in bridges:
        a,b=order[lane:lane+2]; chosen,other=(a,b) if side==0 else (b,a)
        target=rec[chosen]; oldrec=rec[:]; oldfaces=faces[:]
        if variant=='frozen_target': target=st['records'][chosen]
        if variant=='direct_flip': target=chosen
        faces[target]^=1
        gate=faces[other]
        if variant=='pre_face': gate=oldfaces[other]
        if variant=='initial_face': gate=st['faces'][other]
        if variant=='old_rule': gate=0
        if variant=='always_copy': gate=1
        if variant=='selected_face': gate=faces[chosen]
        if variant=='reverse_gate': gate=1-gate
        rec[chosen]=oldrec[other] if gate else other
        order[lane:lane+2]=[b,a]
        hist.append({'selected':chosen,'partner':other,'recipient':target,'old_records':oldrec,
          'old_faces':oldfaces,'partner_face_after_flip':faces[other], 'branch':'copy_tag' if gate else 'partner_identity',
          'new_record':rec[chosen],'state':{'order':order[:],'faces':faces[:],'records':rec[:]}})
    result={'order':order,'faces':faces,'records':rec}
    return (result,hist) if trace else result

def independent(st,bridges):
    """A second evaluator: lane-local mutable objects, no identity-indexed state update."""
    lanes=[{'id':i,'black':bool(st['faces'][i]),'tag':st['records'][i]} for i in st['order']]
    for lane,side in bridges:
        active=lanes[lane+side]; partner=lanes[lane+1-side]
        recipient=next(p for p in lanes if p['id']==active['tag'])
        recipient['black']=not recipient['black']
        active['tag']=partner['tag'] if partner['black'] else partner['id']
        lanes[lane],lanes[lane+1]=lanes[lane+1],lanes[lane]
    byid=sorted(lanes,key=lambda p:p['id'])
    return {'order':[p['id'] for p in lanes],'faces':[int(p['black']) for p in byid], 'records':[p['tag'] for p in byid]}

def models():
    # selector(8), flip recipient(5), white write(6), black write(6), gate(8),
    # tag attachment(2), exchange(2), write owner(3).
    return np.array(list(itertools.product(range(8),range(5),range(6),range(6),range(8),range(2),range(2),range(3))),dtype=np.int16)

def batch(st,bridges,ms):
    n=len(ms); idx=np.arange(n); slot=ms[:,5]==1
    order=np.tile(st['order'],(n,1)); f=np.tile(st['faces'],(n,1)); rec=np.tile(st['records'],(n,1))
    rec[slot]=np.array(st['records'])[np.array(st['order'])]
    for lane,side in bridges:
        a,b=order[:,lane].copy(),order[:,lane+1].copy(); fa,fb=f[idx,a].copy(),f[idx,b].copy()
        selectors=np.stack([np.full(n,side),np.full(n,1-side),np.zeros(n,int),np.ones(n,int),fa,1-fa,fb,1-fb],axis=1)
        low=selectors[idx,ms[:,0]]; c=np.where(low==0,a,b); o=np.where(low==0,b,a)
        ci=np.where(slot,lane+low,c); oi=np.where(slot,lane+1-low,o)
        rc=rec[idx,ci].copy(); ro=rec[idx,oi].copy(); third=order[:,2-2*lane]
        targets=np.stack([rc,c,o,ro,third],axis=1); target=targets[idx,ms[:,1]]
        ti=np.where(slot,np.argmax(order==target[:,None],axis=1),target)
        rt=rec[idx,ti].copy(); fc,fo,ft=f[idx,c].copy(),f[idx,o].copy(),f[idx,target].copy()
        f[idx,target]^=1
        gates=np.stack([fo,f[idx,o],fc,f[idx,c],ft,f[idx,target],fc^fo,f[idx,c]^f[idx,o]],axis=1)
        gate=gates[idx,ms[:,4]]
        writes=np.stack([o,ro,c,rc,third,rt],axis=1)
        val=writes[idx,np.where(gate==0,ms[:,2],ms[:,3])]
        own=ms[:,7]
        mask=own!=2; rec[idx[mask],ci[mask]]=val[mask]
        mask=own!=0; rec[idx[mask],oi[mask]]=val[mask]
        swap=ms[:,6]==0; order[idx[swap],lane]=b[swap];order[idx[swap],lane+1]=a[swap]
    outrec=rec.copy()
    for lane in range(3): outrec[idx[slot],order[slot,lane]]=rec[slot,lane]
    return np.concatenate([order,f,outrec],axis=1)

def encode(st):return np.array(st['order']+st['faces']+st['records'])
def evidence(s):return [(e['initial'],e['bridges'],e['final']) for e in s['examples']]+[(s['worked']['initial'],s['worked']['bridges'],s['worked']['final'])]
