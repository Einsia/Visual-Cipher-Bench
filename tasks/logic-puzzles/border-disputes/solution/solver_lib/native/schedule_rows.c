#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#define N 6
#define K 64
static int rows[8],matrix[36],mode;
static int targets[16][12],nt,orders[720][12],no;
static int solorder[1000],soltarget[1000];
static unsigned char ok[K][K],v[K][K][K][6],sm[K][K][K],th[K][K][K],bad[K][K][K];
static long long nodes,leaves,topology,simulations,accepted;
static int sols[1000][6];
static int conn(){uint64_t mask=0,vis=0;for(int r=0;r<N;r++)mask|=(uint64_t)rows[r+1]<<(r*N);if(!mask)return 0;
 uint64_t all=(1ULL<<36)-1,left=0,right=0;for(int r=0;r<N;r++){left|=1ULL<<(6*r);right|=1ULL<<(6*r+5);}uint64_t f=mask&-mask;vis=f;while(f){f=(((f&~left)>>1)|((f&~right)<<1)|(f>>6)|(f<<6))&mask&~vis;vis|=f;}if(vis!=mask)return 0;
 uint64_t outside=(~mask)&all,border=left|right|63ULL|(63ULL<<30);f=outside&border;vis=f;while(f){f=(((f&~left)>>1)|((f&~right)<<1)|(f>>6)|(f<<6))&outside&~vis;vis|=f;}return vis==outside;}


/* Candidates and topology are enumerated exhaustively. Each uint64 bit lane is
   one candidate. Store u=n outside and u=4-n inside: u travels without changes,
   while flip(u,inside) recovers the current value. No answer/candidate cache.

   All 24 (or supplied) schedules are paths in a prefix trie. When both the row
   and column of a cell have executed, that cell is final. Each final signed contribution is offset by four into [0,8].
   For k final cells, the offset sum lies in [target+24-8*(6-k), target+24].
   These conservative bounds become exact equality at k=6. Membership is
   fixed by each candidate loop; positive-part sums cannot be used as bounds. A child operates only on surviving
   bit lanes; restoring its active line restores the parent state exactly. */
#define MAX_TRIE 9000
struct Node {int child[12],op,oi,depth,ncheck; unsigned done; int line[12],num[12],pos[12][6],lo[12],hi[12];};
static struct Node trie[MAX_TRIE];static int nn=1;
static int linepos[12][6];
typedef struct {uint64_t x[3];} Bits;
static Bits payload[36];static uint64_t inside[36];static int batch_rows[64][6],batch_n;
static long long batches;
static long long trie_moves,pruned;
static void setup_trie(void){
 for(int o=0;o<no;o++){
  int node=0;
  for(int step=0;step<12;step++){
   int op=orders[o][step];
   if(!trie[node].child[op]){
    int z=nn++;if(nn>=MAX_TRIE){fprintf(stderr,"trie overflow\n");exit(7);}
    trie[node].child[op]=z;trie[z].op=op;trie[z].oi=-1;trie[z].depth=step+1;trie[z].done=trie[node].done|(1u<<op);
    for(int line=0;line<12;line++){
     if(!(trie[z].done>>line&1))continue;
     int cells[6],n=0,oldn=0;
     for(int j=0;j<6;j++){
      int other=2*j+(1-(line&1));
      if(trie[z].done>>other&1)cells[n++]=linepos[line][j];
      if((trie[node].done>>line&1)&&(trie[node].done>>other&1))oldn++;
     }
     if(n==oldn)continue;
     int target=targets[0][(line&1)?6+line/2:line/2];
     target+=24;
     if(target>=8*n && target<=8*(6-n))continue;
     int k=trie[z].ncheck++;trie[z].line[k]=line;trie[z].num[k]=n;
     trie[z].lo[k]=target-8*(6-n);trie[z].hi[k]=target;
     for(int j=0;j<n;j++)trie[z].pos[k][j]=cells[j];
    }
    /* Check the tightest (smallest final margin) first. */
    for(int i=0;i<trie[z].ncheck;i++)for(int j=i+1;j<trie[z].ncheck;j++)if(trie[z].hi[j]<trie[z].hi[i]){
     int t=trie[z].line[i];trie[z].line[i]=trie[z].line[j];trie[z].line[j]=t;
     t=trie[z].num[i];trie[z].num[i]=trie[z].num[j];trie[z].num[j]=t;
     t=trie[z].lo[i];trie[z].lo[i]=trie[z].lo[j];trie[z].lo[j]=t;
     t=trie[z].hi[i];trie[z].hi[i]=trie[z].hi[j];trie[z].hi[j]=t;
     for(int k=0;k<6;k++){t=trie[z].pos[i][k];trie[z].pos[i][k]=trie[z].pos[j][k];trie[z].pos[j][k]=t;}
    }
   }
   node=trie[node].child[op];
  }
  trie[node].oi=o;
 }
}

static inline Bits flip(Bits a,uint64_t mask){Bits b={{a.x[0],a.x[1]^(a.x[0]&mask),a.x[2]^(mask&~(a.x[0]|a.x[1]))}};return b;}
static inline void add_value(uint64_t sum[5],Bits a){
 uint64_t carry=0;
 for(int i=0;i<5;i++){
  uint64_t b=i<3?a.x[i]:0,old=sum[i],v=old^b;
  sum[i]=v^carry;carry=(old&b)|(v&carry);
 }
}
static inline uint64_t leq(uint64_t a[5],int k,uint64_t mask){
 uint64_t equal=mask,less=0;
 for(int i=4;i>=0;i--){if(k>>i&1){less|=equal&~a[i];equal&=a[i];}else equal&=~a[i];}
 return less|equal;
}
static inline void add_signed(uint64_t sum[6],Bits a,uint64_t in){
 // Offset each signed value by four: inside n+4, outside 4-n.
 Bits n=flip(a,in),z=flip(n,~in);
 uint64_t b[4]={z.x[0],z.x[1],z.x[2]^in,z.x[2]&in};
 uint64_t carry=0;
 for(int i=0;i<6;i++){uint64_t v=i<4?b[i]:0,old=sum[i],t=old^v;sum[i]=t^carry;carry=(old&v)|(t&carry);}
}
static inline uint64_t leq_signed(uint64_t a[6],int k,uint64_t mask){
 uint64_t equal=mask,less=0;
 for(int i=5;i>=0;i--){if(k>>i&1){less|=equal&~a[i];equal&=a[i];}else equal&=~a[i];}
 return less|equal;
}
static void walk(int node,uint64_t mask){
 struct Node *t=trie+node;int op=t->op,*lp=linepos[op];Bits old[6],current[6];uint64_t sum[5]={0},ks[6]={0};
 trie_moves++;
 for(int j=0;j<6;j++){
  int q=lp[j];old[j]=current[j]=payload[q];Bits v=flip(payload[q],inside[q]);
  for(int b=0;b<3;b++)v.x[b]&=inside[q];add_value(sum,v);
 }
 for(int k=0;k<=24;k++){
  uint64_t hit=mask;
  for(int b=0;b<5;b++)hit&=(k>>b&1)?sum[b]:~sum[b];ks[k%6]|=hit;
 }
 for(int bit=0;bit<3;bit++){
  uint64_t select=0;for(int k=0;k<6;k++)if(k>>bit&1)select|=ks[k];
  Bits next[6];int step=1<<bit;
  for(int j=0;j<6;j++)for(int b=0;b<3;b++){uint64_t x=current[j].x[b],y=current[(j+6-step)%6].x[b];next[j].x[b]=x^((x^y)&select);}
  for(int j=0;j<6;j++)current[j]=next[j];
 }
 for(int j=0;j<6;j++)payload[lp[j]]=current[j];
 for(int i=0;i<t->ncheck;i++){
  uint64_t sum[6]={0};for(int j=0;j<t->num[i];j++){int q=t->pos[i][j];add_signed(sum,payload[q],inside[q]);}
  mask=leq_signed(sum,t->hi[i],mask);
  if(t->lo[i]>0)mask&=~leq_signed(sum,t->lo[i]-1,mask);
  if(!mask){pruned++;goto restore;}
 }
 if(t->depth==12){
  while(mask){int b=__builtin_ctzll(mask);mask&=mask-1;
   if(accepted<1000){for(int r=0;r<6;r++)sols[accepted][r]=batch_rows[b][r];solorder[accepted]=t->oi;soltarget[accepted]=0;}accepted++;
  }
 }else for(int i=0;i<12;i++)if(t->child[i])walk(t->child[i],mask);
restore:
 for(int j=0;j<6;j++)payload[lp[j]]=old[j];
}
static void flush_batch(void){
 if(!batch_n)return;batches++;uint64_t mask=batch_n==64?~0ULL:(1ULL<<batch_n)-1;
 for(int i=0;i<12;i++)if(trie[0].child[i])walk(trie[0].child[i],mask);
 memset(payload,0,sizeof(payload));memset(inside,0,sizeof(inside));batch_n=0;
}
static void run(){
 uint64_t bit=1ULL<<batch_n;
 for(int r=0;r<6;r++){
  batch_rows[batch_n][r]=rows[r+1];
  for(int c=0;c<6;c++){
   int q=6*r+c,in=rows[r+1]>>c&1,n=matrix[q];
   if(in){inside[q]|=bit;n=4-n;}
   for(int b=0;b<3;b++)if(n>>b&1)payload[q].x[b]|=bit;
  }
 }
 if(++batch_n==64)flush_batch();
}
static void dfs(int depth,int total,int n3){nodes++;int end=depth==7?1:64;
 for(int x=0;x<end;x++){int b=rows[depth-1];if(!ok[b][x])continue;rows[depth]=x;if(depth==1){dfs(2,0,0);continue;}
  int r=depth-2,a=rows[depth-2];if(bad[a][b][x])continue;
  int ss=total+sm[a][b][x],tt=n3+th[a][b][x],rem=6-r-1;
  
  int good=1;for(int c=0;c<6;c++){matrix[6*r+c]=v[a][b][x][c];}if(!good)continue;
  if(depth!=7){dfs(depth+1,ss,tt);continue;}leaves++;
  if(mode!=2){if(!conn())continue;topology++;}
  simulations+=no;run();
 }
}

int main(int argc,char**argv){
 FILE*f=fopen(argv[1],"r");if(!f)return 2;
 if(fscanf(f,"%d%d",&nt,&no)!=2||nt!=1||no<1||no>720)return 3;
 for(int t=0;t<nt;t++)for(int i=0;i<12;i++)if(fscanf(f,"%d",&targets[t][i])!=1)return 4;
 for(int o=0;o<no;o++)for(int i=0;i<12;i++)if(fscanf(f,"%d",&orders[o][i])!=1)return 5;fclose(f);
 for(int a=0;a<64;a++)for(int b=0;b<64;b++){ok[a][b]=1;for(int c=0;c<5;c++){int t=((a>>c)&3)|(((b>>c)&3)<<2);if(t==6||t==9)ok[a][b]=0;}for(int d=0;d<64;d++)for(int c=0;c<6;c++){int z=(b>>c)&1;int k=(z!=((a>>c)&1))+(z!=((d>>c)&1))+(z!=(c?((b>>(c-1))&1):0))+(z!=(c<5?((b>>(c+1))&1):0));v[a][b][d][c]=k;sm[a][b][d]+=k;th[a][b][d]+=(k==3);bad[a][b][d]|=k==4;}}
 for(int op=0;op<12;op++)for(int j=0;j<6;j++)linepos[op][j]=(op&1)?6*j+op/2:6*(op/2)+j;
 setup_trie();
 clock_t st=clock();rows[1]=atoi(argv[2]);dfs(2,0,0);flush_batch();
 printf("{\"nodes\":%lld,\"local_geometry_leaves\":%lld,\"topology_pass\":%lld,\"candidate_schedule_pairs\":%lld,\"bit_batches\":%lld,\"trie_moves\":%lld,\"pruned_prefixes\":%lld,\"solution_count\":%lld,\"cpu_seconds\":%.6f,\"solutions\":[",nodes,leaves,topology,simulations,batches,trie_moves,pruned,accepted,(double)(clock()-st)/CLOCKS_PER_SEC);
 for(int i=0;i<accepted&&i<1000;i++){if(i)printf(",");printf("{\"target\":%d,\"order_index\":%d,\"masks\":[",soltarget[i],solorder[i]);for(int r=0;r<6;r++)printf("%s%d",r?",":"",sols[i][r]);printf("]}");}printf("]}\n");return accepted>1000?6:0;
}
