"""Interleaved, current-value-dependent row/column shifts."""
def evaluate(masks, letters=None, order=None):
 n=len(masks);inside={(r,c)for r in range(n)for c in range(n)if masks[r]>>c&1}
 counts=[[sum(((r,c)in inside)!=((r+dr,c+dc)in inside)for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)])for c in range(n)]for r in range(n)]
 # Payload IDs allow an independent check that values and letters stay together.
 ids=[[r*n+c for c in range(n)]for r in range(n)];flat=sum(counts,[]);values=[row[:]for row in counts];states=[{'ids':[x[:]for x in ids],'values':[x[:]for x in counts]}];steps=[]
 for op in (range(2*n) if order is None else order):
  i=op//2;axis='column' if op%2 else 'row'
  if True:
   coords=[(i,c)for c in range(n)]if axis=='row'else[(r,i)for r in range(n)]
   selected=[(r,c)for r,c in coords if(r,c)in inside]
   k=sum(values[r][c]for r,c in selected);before=[ids[r][c]for r,c in coords];nums=[values[r][c]for r,c in coords];moved=before[-(k%n):]+before[:-(k%n)]if k%n else before[:]
   newnums=nums[-(k%n):]+nums[:-(k%n)]if k%n else nums[:]
   crossings=[]
   for j,(r,c)in enumerate(coords):
    source=coords[(j-k)%n]
    if ((r,c)in inside)!=(source in inside):newnums[j]=4-newnums[j];crossings.append([list(source),[r,c]])
    values[r][c]=newnums[j]
   for(r,c),v in zip(coords,moved):ids[r][c]=v
   steps.append({'step':len(steps)+1,'axis':axis,'index':i,'sampled_cells':selected,'sum':k,'shift':k%n,'crossings':crossings})
   states.append({'ids':[x[:]for x in ids],'values':[row[:]for row in values]})
 final=states[-1]['values'];dest=[];final_letters=[['']*n for _ in range(n)]
 for r in range(n):
  for c in range(n):
   sr,sc=divmod(ids[r][c],n)
   if letters is not None:final_letters[r][c]=letters[sr][sc]
   if final[r][c]==3:dest.append([r,c,sr,sc])
 edges=set()
 for r,c in inside:
  for dr,dc,a,b in [(-1,0,(r,c),(r,c+1)),(0,1,(r,c+1),(r+1,c+1)),(1,0,(r+1,c),(r+1,c+1)),(0,-1,(r,c),(r+1,c))]:
   if(r+dr,c+dc)not in inside:edges.add(tuple(sorted([a,b])))
 return {'masks':list(map(int,masks)),'inside':sorted(inside),'edges':sorted(edges),'counts':counts,'steps':steps,'states':states,'final':final,'row_totals':list(map(sum,final)),'column_totals':[sum(final[r][c]for r in range(n))for c in range(n)],'selected':dest,'final_letters':final_letters,'answer':None if letters is None else ''.join(letters[sr][sc]for r,c,sr,sc in dest)}

def single_loop(masks):
 n=len(masks);edges=[]
 for r in range(n):
  for c in range(n):
   if not(masks[r]>>c&1):continue
   for dr,dc,a,b in [(-1,0,(r,c),(r,c+1)),(0,1,(r,c+1),(r+1,c+1)),(1,0,(r+1,c),(r+1,c+1)),(0,-1,(r,c),(r+1,c))]:
    rr,cc=r+dr,c+dc
    if not(0<=rr<n and 0<=cc<n and masks[rr]>>cc&1):edges.append((a,b))
 adj={}
 for a,b in edges:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 if not adj or any(len(ns)!=2 for ns in adj.values()):return False
 seen=set();todo=[next(iter(adj))]
 while todo:
  a=todo.pop()
  if a in seen:continue
  seen.add(a);todo.extend(adj[a]-seen)
 return len(seen)==len(adj)
