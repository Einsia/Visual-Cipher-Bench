"""Generic joint-image reconstruction. No puzzle answer or coordinate table."""
import itertools,string,time,math
import numpy as np
ABC=string.ascii_uppercase

def layers(templates,positions,width=1700):
 n=len(positions[0]);h,tw=templates.shape[1:];out=np.zeros((n,26,2,h,width),bool)
 for i in range(n):
  for v in range(2):
   cx=positions[v][i];out[i,:,v,:,cx-tw//2:cx+tw//2]=templates
 return out

def bitset(a):return int.from_bytes(np.packbits(a).tobytes(),'little')

def reconstruct(raw,masks,target,tolerance=0):
 t=time.perf_counter();n=raw.shape[0];candidates=[];costs=[]
 for i in range(n):
  opts=[];cc={}
  for k in range(26):
   vis=raw[i,k]&masks;outside=np.count_nonzero(vis&~target)
   if outside<=tolerance:
    opts.append((ABC[k],bitset(vis&target)));cc[ABC[k]]=int(outside)
  candidates.append(opts);costs.append(cc)
 # Every candidate is a subset of the measured ink. Remaining test is exact
 # coverage of every observed black pixel by the whole group, not per card.
 targetbits=bitset(target);order=sorted(range(n),key=lambda i:len(candidates[i]));suffix=[0]*(n+1)
 for j in range(n-1,-1,-1):
  suffix[j]=suffix[j+1]
  for ch,bits in candidates[order[j]]:suffix[j]|=bits
 nodes=0;sol=[];pick=['']*n
 def dfs(j,have):
  nonlocal nodes
  nodes+=1
  missing=(targetbits&~(have|suffix[j])).bit_count()
  if missing>tolerance:return
  if j==n:
   if (targetbits&~have).bit_count()<=tolerance:sol.append(''.join(pick))
   return
  i=order[j]
  for ch,bits in candidates[i]:pick[i]=ch;dfs(j+1,have|bits)
 dfs(0,0)
 return {'solutions':sol,'solution_count':len(sol),'candidate_sets':[[ch for ch,_ in cs] for cs in candidates],'product_after_white_space_constraints':math.prod(map(len,candidates)),'visited_nodes':nodes,'glyph_placements_tested':n*26,'seconds':time.perf_counter()-t,'outside_ink':costs}

def scene_for_word(raw,masks,word,rank):
 seq=['']*len(rank)
 for k,i in enumerate(rank):seq[i]=word[k]
 return np.logical_or.reduce([raw[i,ABC.index(ch)] for i,ch in enumerate(seq)])&masks
