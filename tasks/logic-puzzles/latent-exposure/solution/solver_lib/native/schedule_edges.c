#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
static int rt[6],ct[6],want,orders[720][12],no,solorder[1000],start,goal,counts[36],pin[36],sol[1000][6],adj[49][4],degree[49],prefix=-1;
static uint64_t suffix[7][7],full=(1ULL<<49)-1,left,right;
static long long nodes,cycles,accepted;static uint64_t current_inside;
static void change(int a,int b,int sign){int ar=a/7,ac=a%7,br=b/7,bc=b%7;if(ar==br){int c=ac<bc?ac:bc;if(ar>0)counts[(ar-1)*6+c]+=sign;if(ar<6)counts[ar*6+c]+=sign;}else{int r=ar<br?ar:br;if(ac>0)counts[r*6+ac-1]+=sign;if(ac<6)counts[r*6+ac]+=sign;current_inside^=suffix[r][ac];}}

static void simulate(){
 int initial[36],inside[36];for(int q=0;q<36;q++){inside[q]=(current_inside>>q)&1;initial[q]=(counts[q]-2)*(inside[q]?-1:1);}
 for(int oi=0;oi<no;oi++){
  int z[36],temp[6];memcpy(z,initial,sizeof(z));
  for(int step=0;step<12;step++){
   int op=orders[oi][step],i=op/2,k=0;
   if(!(op&1)){
    for(int c=0;c<6;c++)if(inside[6*i+c])k+=2-z[6*i+c];k%=6;
    for(int c=0;c<6;c++)temp[(c+k)%6]=z[6*i+c];for(int c=0;c<6;c++)z[6*i+c]=temp[c];
   }else{
    for(int r=0;r<6;r++)if(inside[6*r+i])k+=2-z[6*r+i];k%=6;
    for(int r=0;r<6;r++)temp[(r+k)%6]=z[6*r+i];for(int r=0;r<6;r++)z[6*r+i]=temp[r];
   }
  }
  int rs[6]={0},cs[6]={0};for(int q=0;q<36;q++){int v=2+(inside[q]?-1:1)*z[q];rs[q/6]+=v;cs[q%6]+=v;}
  int good=1;for(int i=0;i<6;i++)if(rs[i]!=rt[i]||cs[i]!=ct[i]){good=0;break;}
  if(good){if(accepted<1000){for(int r=0;r<6;r++)sol[accepted][r]=(current_inside>>(6*r))&63;solorder[accepted]=oi;}accepted++;}
 }
}
static int reachable(int p,uint64_t used){uint64_t allow=full&~used;allow|=1ULL<<p;allow&=full<<(start+1);uint64_t f=1ULL<<p,seen=f;while(f){if(f>>goal&1)return 1;f=(((f&~left)>>1)|((f&~right)<<1)|(f>>7)|(f<<7))&allow&~seen;seen|=f;}return 0;}
static void dfs(int p,uint64_t used,int len){nodes++;if(p==goal){if(len<=3 && (prefix>>(2*(len-1)))!=0)return;change(p,start,1);cycles++;simulate();change(p,start,-1);return;}
 if(len%8==0&&!reachable(p,used))return;
 for(int k=0;k<degree[p];k++){if(prefix>=0&&len<=3&&k!=((prefix>>(2*(len-1)))&3))continue;int q=adj[p][k];if(q<=start||(used>>q&1))continue;change(p,q,1);dfs(q,used|(1ULL<<q),len+1);change(p,q,-1);}
}
int main(int argc,char**argv){FILE*f=fopen(argv[1],"r");if(!f)return 2;int nt;if(fscanf(f,"%d%d",&nt,&no)!=2||nt!=1||no>720)return 3;for(int i=0;i<6;i++)if(fscanf(f,"%d",rt+i)!=1)return 4;for(int i=0;i<6;i++)if(fscanf(f,"%d",ct+i)!=1)return 4;for(int o=0;o<no;o++)for(int i=0;i<12;i++)if(fscanf(f,"%d",&orders[o][i])!=1)return 5;fclose(f);if(argc>3)prefix=atoi(argv[3]);int shard=atoi(argv[2]);start=(shard/6)*7+shard%6;goal=start+7;
 for(int r=0;r<7;r++){left|=1ULL<<(7*r);right|=1ULL<<(7*r+6);for(int c=0;c<7;c++){int p=r*7+c;if(r)adj[p][degree[p]++]=p-7;if(c)adj[p][degree[p]++]=p-1;if(r<6)adj[p][degree[p]++]=p+7;if(c<6)adj[p][degree[p]++]=p+1;}}
 for(int r=0;r<6;r++)for(int c=0;c<=6;c++)for(int k=c;k<6;k++)suffix[r][c]|=1ULL<<(r*6+k);
 clock_t st=clock();change(start,start+1,1);dfs(start+1,(1ULL<<start)|(1ULL<<(start+1)),1);change(start,start+1,-1);
 printf("{\"nodes\":%lld,\"cycles\":%lld,\"solution_count\":%lld,\"cpu_seconds\":%.6f,\"solutions\":[",nodes,cycles,accepted,(double)(clock()-st)/CLOCKS_PER_SEC);
 for(int i=0;i<accepted&&i<1000;i++){if(i)printf(",");printf("{\"target\":0,\"order_index\":%d,\"masks\":[",solorder[i]);for(int r=0;r<6;r++)printf("%s%d",r?",":"",sol[i][r]);printf("]}");}printf("]}\n");return accepted>1000?4:0;}
