#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#define MAX 10
#define HS (1<<22)
typedef struct{double x,y;}Pt;
typedef struct{int n;Pt p[80];}Poly;
typedef struct{Poly p[MAX];Pt dot[MAX];int turn[MAX],order[MAX],n,unknown;unsigned short below[MAX];}State;
static int coupled,phases[MAX],initialturn[MAX],remaining[4]; static long orientation_index,orientation_cases,coupling_rejects; static State baseinit;
static int N,READS,NP,mode,shard,shards;static State init;
/* Optional rule inferred from PNGs: 0=underlayer, 1=next target identity,
   2=previous departed identity, 3=fixed identity 4. */
static int echo_rule,last_echo;
static char letters[MAX][4];static int counts[MAX][4];
static Pt sample[1024];static int observed[MAX],obsfrom[MAX],starts[MAX],want[MAX][1024];
#define FH (1<<18)
static uint64_t fkeys[FH],fsigs[FH][16],history[MAX][16],wanted[MAX][16];static int fw;static long fentries,fhits,fqueries;
static uint64_t keys[HS];static double vals[HS];static long entries,queries,hits,clips,states,perms,survivors,ties,rejects[MAX],seqnodes[MAX];
static int initialorder[MAX],used[MAX],trace[MAX],targets[MAX];static char output[MAX+1];static FILE *out;
double cross(Pt a,Pt b,Pt p){return(b.x-a.x)*(p.y-a.y)-(b.y-a.y)*(p.x-a.x);}
Poly clip(Poly p,Pt a,Pt b,int inside){Poly q={0};if(!p.n)return q;Pt v=p.p[p.n-1];double sv=cross(a,b,v)*(inside?1:-1);for(int j=0;j<p.n;j++){Pt w=p.p[j];double sw=cross(a,b,w)*(inside?1:-1);if((sv>=-1e-10)!=(sw>=-1e-10)){double t=sv/(sv-sw);q.p[q.n++]=(Pt){v.x+t*(w.x-v.x),v.y+t*(w.y-v.y)};}if(sw>=-1e-10)q.p[q.n++]=w;v=w;sv=sw;}clips++;return q;}
double area(Poly p){double a=0;for(int j=0;j<p.n;j++){Pt b=p.p[(j+1)%p.n];a+=p.p[j].x*b.y-p.p[j].y*b.x;}return fabs(a)*.5;}
double uncovered(Poly p,int mask,State *s){if(!mask)return area(p);int i=__builtin_ctz(mask);mask&=mask-1;Poly q=s->p[i];double v=0;for(int j=0;j<q.n && p.n;j++){Pt a=q.p[j],b=q.p[(j+1)%q.n];Poly r=clip(p,a,b,0);if(area(r)>1e-9)v+=uncovered(r,mask,s);p=clip(p,a,b,1);}return v;}
typedef struct {uint64_t hash;int pose[3*MAX];int tag;double value;} Cache;
static Cache cache[1<<18];static long cacheused;
double vis(int i,int above,State *s,uint64_t prefix){
 int pose[3*MAX]={0};int mask=above|(1<<i),tag=i*1024+above;uint64_t h=1469598103934665603ull;
 for(int j=0;j<N;j++)if(mask&(1<<j)){pose[j*3]=(int)llround(s->dot[j].x*2);pose[j*3+1]=(int)llround(s->dot[j].y*2);pose[j*3+2]=s->turn[j];}
 h^=tag;h*=1099511628211ull;for(int j=0;j<3*N;j++){h^=(unsigned int)pose[j];h*=1099511628211ull;}if(!h)h=1;
 int idx=h&((1<<18)-1);queries++;
 while(cache[idx].hash && (cache[idx].hash!=h || cache[idx].tag!=tag || memcmp(cache[idx].pose,pose,sizeof(pose))))idx=(idx+1)&((1<<18)-1);
 if(cache[idx].hash){hits++;return cache[idx].value;}
 double a=uncovered(s->p[i],above,s);cache[idx].hash=h;cache[idx].tag=tag;memcpy(cache[idx].pose,pose,sizeof(pose));cache[idx].value=a;cacheused++;
 if(cacheused>(1<<18)*.8){memset(cache,0,sizeof(cache));cacheused=0;}return a;
}
int inside(Poly p,Pt a){for(int j=0;j<p.n;j++)if(cross(p.p[j],p.p[(j+1)%p.n],a)<-1e-9)return 0;return 1;}
void signature(State *s,uint64_t prefix,uint64_t *bits){
 memset(bits,0,fw*sizeof(uint64_t));for(int j=0;j<NP;j++){int b=0;for(int k=0;k<s->n&&!b;k++)b=inside(s->p[s->order[k]],sample[j]);for(int k=0;k<N&&!b;k++)if(s->unknown&(1<<k))b=inside(s->p[k],sample[j]);if(b)bits[j/64]|=1ull<<(j%64);}
}
int match(State *s,int step,uint64_t prefix){if(!observed[step])return 1;uint64_t acc[16];signature(s,prefix,acc);for(int j=0;j<fw;j++)if((acc[j]^history[obsfrom[step]][j])!=wanted[step][j]){rejects[step]++;return 0;}return 1;}
Pt rot(Pt a,Pt c){return(Pt){c.x-(a.y-c.y),c.y+(a.x-c.x)};}
Pt invrot(Pt a,Pt c){return(Pt){c.x+(a.y-c.y),c.y-(a.x-c.x)};}
void remove_id(State *s,int id){if(s->unknown&(1<<id)){s->unknown&=~(1<<id);return;}int at=0;while(at<s->n&&s->order[at]!=id)at++;for(int j=at;j<s->n-1;j++)s->order[j]=s->order[j+1];s->n--;}
int gettarget(State *s,int take,int count){int mask=s->unknown;for(int j=0;j<s->n;j++)mask|=1<<s->order[j];mask&=~(1<<take);int t=take;for(int j=0;j<count;j++){do{t=(t+1)%N;}while(!(mask&(1<<t)));}return t;}
State advance(State s,int take,int count,int *target){Pt pivot=s.dot[take];int t=gettarget(&s,take,count);*target=t;remove_id(&s,take);remove_id(&s,t);
 for(int j=0;j<s.p[t].n;j++)s.p[t].p[j]=rot(s.p[t].p[j],pivot);s.dot[t]=rot(s.dot[t],pivot);s.turn[t]=(s.turn[t]+1)%4;
 int alive=s.unknown;for(int j=0;j<s.n;j++)alive|=1<<s.order[j];int e=-1;
 if(echo_rule==0){if(s.n)e=s.order[s.n-1];}
 else if(echo_rule==3){if(alive && ((alive&(1<<3)) || t==3))e=3;}
 else if(alive){int start=echo_rule==1?t:take,dir=echo_rule==1?1:-1;
  for(int d=1;d<=N;d++){int k=(start+dir*d+N)%N;if(alive&(1<<k)){e=k;break;}}}
 last_echo=e;
 if(e>=0){Pt p=s.dot[t];for(int j=0;j<s.p[e].n;j++)s.p[e].p[j]=invrot(s.p[e].p[j],p);s.dot[e]=invrot(s.dot[e],p);s.turn[e]=(s.turn[e]+3)%4;}
 s.order[s.n++]=t;return s;
}
static int echoes[MAX];static long reveals;
void emit(State *s){if(coupled){int left=s->unknown;for(int j=0;j<s->n;j++)left|=1<<s->order[j];for(int i=0;i<N;i++)if((left&(1<<i))&&initialturn[i]!=phases[READS]){coupling_rejects++;return;}}survivors++;fprintf(out,"%s ",output);
 if(mode==0)for(int j=0;j<N;j++)fprintf(out,"%d",initialorder[j]+1);
 else {int done=0;for(int k=0;k<N;k++){for(int j=0;j<N;j++)if(!(done&(1<<j)) && !(s->below[j]&~done)){fprintf(out,"%d",j+1);done|=1<<j;break;}}}
 fprintf(out," ");for(int j=0;j<READS;j++)fprintf(out,"%d",trace[j]+1);fprintf(out," ");for(int j=0;j<READS;j++)fprintf(out,"%d",targets[j]+1);fprintf(out," ");for(int j=0;j<READS;j++)fprintf(out,"%d",echoes[j]+1);if(coupled){fprintf(out," ");for(int j=0;j<N;j++)fprintf(out,"%d",initialturn[j]);}fprintf(out,"\n");}
void walk(State *s,int step,uint64_t prefix);
State reveal(State s,int i){s.unknown&=~(1<<i);s.below[i]|=s.unknown;for(int j=s.n;j>0;j--)s.order[j]=s.order[j-1];s.order[0]=i;s.n++;reveals++;return s;}
void perform(State *s,int step,int i){
 if(coupled && initialturn[i]!=phases[step]){coupling_rejects++;return;}
 int t=s->turn[i],target=gettarget(s,i,counts[i][t]);int otherknown=0;for(int j=0;j<s->n;j++)if(s->order[j]!=i&&s->order[j]!=target)otherknown++;
 int otherunknown=s->unknown&~(1<<i)&~(1<<target);
 if(echo_rule==0 && !otherknown && otherunknown){for(int j=0;j<N;j++)if(otherunknown&(1<<j)){State q=reveal(*s,j);perform(&q,step,i);}return;}
 output[step]=letters[i][t];trace[step]=i;State q=advance(*s,i,counts[i][t],&targets[step]);echoes[step]=last_echo;
 if(match(&q,step+1,0))walk(&q,step+1,0);
}
void walk(State *s,int step,uint64_t prefix){states++;seqnodes[step]++;if(starts[step])signature(s,0,history[step]);if(step==READS){emit(s);return;}
 double lo[MAX],hi[MAX],best=-1;int knownmask=0;for(int j=s->n-1;j>=0;j--){int i=s->order[j];lo[i]=hi[i]=vis(i,knownmask,s,0);knownmask|=1<<i;}
 int alive=knownmask|s->unknown;
 if(mode==1 && s->unknown){for(int i=0;i<N;i++)if(s->unknown&(1<<i)){hi[i]=vis(i,knownmask,s,0);lo[i]=vis(i,knownmask|(s->unknown&~(1<<i)),s,0);}
  int certain=-1;for(int i=0;i<N;i++)if(alive&(1<<i)){int yes=1;for(int j=0;j<N;j++)if(j!=i&&(alive&(1<<j))&&lo[i]<=hi[j]+1e-8)yes=0;if(yes){certain=i;break;}}
  if(certain>=0){perform(s,step,certain);return;}
  for(int i=0;i<N;i++)if(s->unknown&(1<<i)){if(step==0&&s->n==0&&!coupled&&i%shards!=shard)continue;State q=reveal(*s,i);walk(&q,step,0);}return;
 }
 for(int i=0;i<N;i++)if(alive&(1<<i)&&hi[i]>best)best=hi[i];int nt=0;for(int i=0;i<N;i++)if((alive&(1<<i))&&fabs(hi[i]-best)<1e-8)nt++;if(nt>1)ties++;
 for(int i=0;i<N;i++)if((alive&(1<<i))&&fabs(hi[i]-best)<1e-8)perform(s,step,i);
}
void enumerate(int depth){if(depth==N){perms++;State s=init;memcpy(s.order,initialorder,N*sizeof(int));walk(&s,0,0);return;}for(int i=0;i<N;i++)if(!used[i]){if(depth==0&&!coupled&&i%shards!=shard)continue;used[i]=1;initialorder[depth]=i;enumerate(depth+1);used[i]=0;}}

void orientations(int depth){
 if(depth==N){long ix=orientation_index++;if(ix%shards!=shard)return;orientation_cases++;init=baseinit;
  for(int i=0;i<N;i++){for(int t=0;t<initialturn[i];t++)for(int j=0;j<init.p[i].n;j++)init.p[i].p[j]=rot(init.p[i].p[j],init.dot[i]);init.turn[i]=initialturn[i];}
  if(mode==0)enumerate(0);else{init.unknown=(1<<N)-1;init.n=0;walk(&init,0,0);}return;
 }
 for(int t=0;t<4;t++)if(remaining[t]){remaining[t]--;initialturn[depth]=t;orientations(depth+1);remaining[t]++;}
}

int main(int argc,char**argv){if(argc<6)return 2;echo_rule=argc>6?atoi(argv[6]):0;if(echo_rule<0||echo_rule>3)return 4;FILE*f=fopen(argv[1],"r");out=fopen(argv[2],"w");if(!f||!out)return 3;mode=atoi(argv[3]);shard=atoi(argv[4]);shards=atoi(argv[5]);fscanf(f,"%d%d%d",&N,&READS,&NP);init.n=N;fw=(NP+63)/64;for(int i=0;i<N;i++){Poly*p=&init.p[i];fscanf(f,"%d",&p->n);for(int j=0;j<p->n;j++)fscanf(f,"%lf%lf",&p->p[j].x,&p->p[j].y);fscanf(f,"%lf%lf",&init.dot[i].x,&init.dot[i].y);for(int t=0;t<4;t++)fscanf(f," %c%d",&letters[i][t],&counts[i][t]);init.order[i]=i;}
for(int j=0;j<NP;j++)fscanf(f,"%lf%lf",&sample[j].x,&sample[j].y);int n;fscanf(f,"%d",&n);for(int j=0;j<n;j++){int k,a;fscanf(f,"%d%d",&a,&k);observed[k]=1;obsfrom[k]=a;starts[a]=1;for(int t=0;t<NP;t++){fscanf(f,"%d",&want[k][t]);if(want[k][t])wanted[k][t/64]|=1ull<<(t%64);}}coupled=fscanf(f,"%d",&phases[0])==1;if(coupled){remaining[phases[0]]++;for(int i=1;i<N;i++){fscanf(f,"%d",&phases[i]);remaining[phases[i]]++;}}fclose(f);baseinit=init;double start=(double)clock()/CLOCKS_PER_SEC;if(coupled)orientations(0);else if(mode==0)enumerate(0);else {init.unknown=(1<<N)-1;init.n=0;walk(&init,0,0);}fclose(out);printf("{\"mode\":%d,\"permutations\":%ld,\"states\":%ld,\"survivors\":%ld,\"ties_branched\":%ld,\"area_queries\":%ld,\"cache_hits\":%ld,\"clip_calls\":%ld,\"cpu_seconds\":%.6f,\"nodes_by_depth\":[",mode,perms,states,survivors,ties,queries,hits,clips,(double)clock()/CLOCKS_PER_SEC-start);for(int j=0;j<=READS;j++)printf("%s%ld",j?",":"",seqnodes[j]);printf("],\"rejections\":[");for(int j=0;j<=READS;j++)printf("%s%ld",j?",":"",rejects[j]);printf("],\"reveals\":%ld,\"orientation_cases\":%ld,\"coupling_rejections\":%ld}\n",reveals,orientation_cases,coupling_rejects);}
