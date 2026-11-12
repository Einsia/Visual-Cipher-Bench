#include <stdint.h>
#include <string.h>
static int n,m,k,rows[32][4],init[16],goal[16],p[16],fw[16],w0[16],sel[16],ans[64],cap,mode;
static uint64_t nodes,ends,leaves,sols,conflicts,distances,preds;
static void dfs(int i,int depth,unsigned assigned,unsigned used){
 if(cap&&sols>=cap)return;
 nodes++;int rem=k-depth;if(i+1<rem)return;
 int wrong=0;
 for(int j=0;j<n;j++){int target=(mode!=1&&(assigned&(1<<j)))?fw[j]:init[j];if(target>=0)wrong+=p[j]!=target;}
 int touched=wrong;
 if(mode!=1)for(int j=0;j<n;j++)if(!(assigned&(1u<<j)) && init[j]<0 && p[j]!=w0[j])touched++;
 if(touched>2*rem){distances++;return;}
 /* Exact minimum arbitrary transpositions to satisfy the currently fixed
    initial positions. Wrong requirements form disjoint directed paths and
    cycles: a path of L edges costs L swaps, a cycle costs L-1. Later selected
    transitions are transpositions, so this is an admissible lower bound. */
 if(mode!=1 && wrong>rem){
  int pos[16],edge[16],cycles=0;unsigned done=0;
  for(int j=0;j<n;j++)pos[p[j]]=j;
  for(int j=0;j<n;j++){
   int target=(assigned&(1<<j))?fw[j]:init[j];
   edge[j]=(target>=0 && p[j]!=target)?pos[target]:-1;
  }
  for(int j=0;j<n;j++)if(!(done&(1u<<j))){
   unsigned path=0;int v=j;
   while(v>=0 && !(done&(1u<<v)) && !(path&(1u<<v))){path|=1u<<v;v=edge[v];}
   if(v>=0 && (path&(1u<<v)))cycles++;
   done|=path;
  }
  if(wrong-cycles>rem){distances++;return;}
 }
 if(!rem){
  leaves++;unsigned mask=0;
  for(int j=0;j<n;j++){
   if(init[j]>=0&&p[j]!=init[j])return;
   int value=(assigned&(1<<j))?fw[j]:w0[j];mask|=1<<value;
   if(mode!=1&&value!=p[j])return;
  }
  if(mode==1&&__builtin_popcount(mask)!=n)return;
  sols++;if(sols==1){memcpy(ans,p,4*n);for(int j=0;j<k;j++)ans[n+j]=sel[k-1-j];}
  return;
 }
 /* Skipped rows do not change state or remaining count. Enumerate the
    next selected row directly instead of recomputing identical bounds. */
 for(int rowi=i;rowi>=rem-1;rowi--){
 int a=rows[rowi][0],b=rows[rowi][1],c=rows[rowi][2],d=rows[rowi][3];
 int cu[32],cv[32],nc=0;
 #define ADD(U,V) do{cu[nc]=(U);cv[nc]=(V);nc++;}while(0)
 if(mode==2){ADD(c,d);}
 else{
  int qc=p[c],qd=p[d];
  /* Neither endpoint is a source position: the values determine the pair. */
  if(qc!=c && qc!=d && qd!=c && qd!=d){ADD(qc,qd);}
  /* Only c is touched. Either q[d]=c and the other endpoint is fixed,
     or the other endpoint is q[d] and its current value is c. */
  if(qd==c){for(int z=0;z<n;z++)if(z!=c&&z!=d&&p[z]==z){ADD(c,z);}}
  else if(qd!=d && p[qd]==c){ADD(c,qd);}
  /* Only d is touched, symmetrically. */
  if(qc==d){for(int z=0;z<n;z++)if(z!=c&&z!=d&&p[z]==z){ADD(d,z);}}
  else if(qc!=c && p[qc]==d){ADD(d,qc);}
  if((qc==c&&qd==d)||(qc==d&&qd==c)){ADD(c,d);}
 }
 for(int zpair=0;zpair<nc;zpair++){
  if(cap&&sols>=cap)return;
  int u=cu[zpair],v=cv[zpair];
  preds++;int t=p[u];p[u]=p[v];p[v]=t;
  int dest[2]={mode==2?c:p[c],mode==2?d:p[d]},values[2]={p[a],p[b]};unsigned am=assigned,um=used;int bad=0,old[2]={fw[dest[0]],fw[dest[1]]};
  for(int z=0;z<2;z++){
   int slot=dest[z],value=values[z];if(am&(1<<slot))continue;
   if((um&(1<<value))||(mode!=1&&init[slot]>=0&&init[slot]!=value)){bad=1;break;}
   fw[slot]=value;am|=1<<slot;um|=1<<value;
  }
  if(bad)conflicts++;else{sel[depth]=rowi;dfs(rowi-1,depth+1,am,um);}
  fw[dest[0]]=old[0];fw[dest[1]]=old[1];t=p[u];p[u]=p[v];p[v]=t;
 }
 }
}
static void terminal(int j,unsigned mask){
 if(cap&&sols>=cap)return;
 if(j==n){ends++;memcpy(p,goal,4*n);memset(fw,-1,sizeof(fw));dfs(m-1,0,0,0);return;}
 if(goal[j]>=0){terminal(j+1,mask);return;}
 for(int v=0;v<n;v++)if(!(mask&(1<<v))){goal[j]=v;terminal(j+1,mask|(1<<v));goal[j]=-1;}
}
void solve_reverse(int nn,int mm,int kk,int*r,int*st,int*end,int*wr,int limit,int md,uint64_t*stats,int*out){
 n=nn;m=mm;k=kk;memcpy(rows,r,m*16);memcpy(init,st,n*4);memcpy(goal,end,n*4);memcpy(w0,wr,n*4);cap=limit;mode=md;
 nodes=ends=leaves=sols=conflicts=distances=preds=0;memset(ans,-1,sizeof(ans));unsigned mask=0;
 for(int j=0;j<n;j++)if(goal[j]>=0)mask|=1<<goal[j];terminal(0,mask);
 stats[0]=nodes;stats[1]=ends;stats[2]=leaves;stats[3]=sols;stats[4]=conflicts;stats[5]=distances;stats[6]=preds;memcpy(out,ans,(n+k)*4);
}
