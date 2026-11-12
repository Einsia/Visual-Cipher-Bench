#include <bits/stdc++.h>
using namespace std;
struct Config {array<int,5> l,s,r,end,order;};
vector<Config> configs(const vector<int>& nums,const vector<int>& tags){
 vector<Config> v;int n=nums.size();vector<int>pre(n+1);for(int i=0;i<n;i++)pre[i+1]=pre[i]+nums[i];
 for(int a=1;a<n-3;a++)for(int b=a+1;b<n-2;b++)for(int c=b+1;c<n-1;c++)for(int d=c+1;d<n;d++){
 array<int,5>ends={a,b,c,d,n},perm={0,1,2,3,4};
 do{Config q;int start=0;for(int k=0;k<5;k++){int id=perm[k];q.l[id]=ends[k]-start;q.s[id]=pre[ends[k]]-pre[start];q.r[id]=tags[ends[k]-1];q.end[id]=ends[k];q.order[k]=id;start=ends[k];}v.push_back(q);}while(next_permutation(perm.begin(),perm.end()));
 }return v;
}
chrono::steady_clock::time_point search_start;double first_seconds=-1;long long first_pairs=0;
long long pairs_seen=0,multiset_pass=0,nodes=0,tests=0,solutions=0;
int m,cap,mode;vector<int>edges;int statev[10],threshold[25],pathv[25];const Config *curA,*curB;
struct Model{Config a,b;vector<int> path;};vector<Model>models;
void dfs(unsigned mask,int depth){nodes++;
 if(depth==m){if(!solutions){first_seconds=chrono::duration<double>(chrono::steady_clock::now()-search_start).count();first_pairs=pairs_seen;}solutions++;Model q{*curA,*curB,{}};for(int i=0;i<m;i++)q.path.push_back(edges[pathv[i]]);models.push_back(q);return;}
 for(int k=0;k<m;k++)if(!(mask>>k&1)){tests++;int e=edges[k],a=e/5,b=5+e%5;if(statev[a]+statev[b]!=threshold[k])continue;
 pathv[depth]=k;if(mode!=1)swap(statev[a],statev[b]);dfs(mask|(1<<k),depth+1);if(mode!=1)swap(statev[a],statev[b]);if(solutions>=cap)return;
 }
}
template<class T> void arr(const T &a){cout<<"[";bool first=true;for(auto x:a){if(!first)cout<<",";first=false;cout<<x;}cout<<"]";}
void conf(const Config&q){cout<<"{\"lengths\":";arr(q.l);cout<<",\"sums\":";arr(q.s);cout<<",\"targets\":";arr(q.r);cout<<",\"ends\":";arr(q.end);cout<<",\"physical_order\":";arr(q.order);cout<<"}";}
int main(int argc,char**argv){ifstream f(argv[1]);int na,nb;f>>na>>nb>>m;vector<int>a(na),b(nb),ra(na),rb(nb);for(auto&x:a)f>>x;for(auto&x:ra)f>>x;for(auto&x:b)f>>x;for(auto&x:rb)f>>x;edges.resize(m);for(auto&x:edges)f>>x;
 if(!f||m>25||m<1)return 2;cap=argc>2?atoi(argv[2]):2;mode=argc>3?atoi(argv[3]):0;
 auto start=chrono::steady_clock::now();search_start=start;auto A=configs(a,ra),B=configs(b,rb);
 for(size_t ba=0;ba<A.size();ba+=120)for(size_t bb0=0;bb0<B.size();bb0+=120){
 for(int j=0;j<5;j++){statev[j]=A[ba].s[j];statev[j+5]=B[bb0].s[j];}
 uint64_t possible[8]={};for(int i=0;i<10;i++)for(int j=i+1;j<10;j++){int s=statev[i]+statev[j];if(s<512)possible[s>>6]|=1ULL<<(s&63);}
 for(size_t ia=ba;ia<ba+120;ia++){const auto&aa=A[ia];curA=&aa;for(size_t ib=bb0;ib<bb0+120;ib++){const auto&bb=B[ib];curB=&bb;pairs_seen++;
 bool ok=true;for(int k=0;k<m;k++){int e=edges[k],i=e/5,j=e%5;int t;
 if(mode==2)t=aa.l[i]*bb.l[aa.r[i]]+bb.l[j]*aa.l[bb.r[j]];
 else t=aa.l[i]*aa.l[bb.r[j]]+bb.l[j]*bb.l[aa.r[i]];
 threshold[k]=t;if(t>=512||!(possible[t>>6]>>(t&63)&1)){ok=false;break;}}
 if(!ok)continue;multiset_pass++;for(int j=0;j<5;j++){statev[j]=aa.s[j];statev[j+5]=bb.s[j];}dfs(0,0);if(solutions>=cap)goto done;
 }}}
 done:cout<<"{\"solutions\":"<<solutions<<",\"complete\":"<<(solutions<cap?"true":"false")<<",\"mode\":"<<mode<<",\"configs_A\":"<<A.size()<<",\"configs_B\":"<<B.size()<<",\"pairs_seen\":"<<pairs_seen<<",\"multiset_pass\":"<<multiset_pass<<",\"schedule_nodes\":"<<nodes<<",\"card_tests\":"<<tests<<",\"seconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<",\"first_solution_seconds\":"<<first_seconds<<",\"first_solution_pairs\":"<<first_pairs<<",\"models\":[";
 for(int i=0;i<models.size();i++){if(i)cout<<",";cout<<"{\"A\":";conf(models[i].a);cout<<",\"B\":";conf(models[i].b);cout<<",\"schedule\":";arr(models[i].path);cout<<"}";}cout<<"]}\n";
}
