// Own CDCL implementation: watched literals, first-UIP learning, VSIDS, Luby restarts.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <vector>
using namespace std;
struct Sat {
 struct Clause { vector<int> a; bool learnt; int lbd; uint64_t touch; };
 int n; vector<Clause> clauses;vector<vector<int>> watches;
 vector<int8_t> assigns,phase;vector<int> level,reason,trail,limits,heap,hpos;vector<double> activity;
 vector<uint8_t> seen;size_t qhead=0;double inc=1;uint64_t conflicts=0,decisions=0;bool ok=true;
 chrono::steady_clock::time_point deadline;
 Sat(int nn,double sec):n(nn),watches(2*n),assigns(n,-1),phase(n,1),level(n),reason(n,-1),hpos(n,-1),activity(n),seen(n){deadline=chrono::steady_clock::now()+chrono::milliseconds((long long)(sec*1000));for(int v=0;v<n;v++)insert(v);}
 int value(int lit){int a=assigns[lit/2];return a<0?-1:a^(lit&1);}
 int dl(){return limits.size();}
 bool less(int a,int b){return activity[a]>activity[b]||(activity[a]==activity[b]&&a<b);}
 void up(int i){int v=heap[i];while(i){int p=(i-1)/2;if(!less(v,heap[p]))break;heap[i]=heap[p];hpos[heap[i]]=i;i=p;}heap[i]=v;hpos[v]=i;}
 void down(int i){int v=heap[i];for(;;){int j=2*i+1;if(j>=(int)heap.size())break;if(j+1<(int)heap.size()&&less(heap[j+1],heap[j]))j++;if(!less(heap[j],v))break;heap[i]=heap[j];hpos[heap[i]]=i;i=j;}heap[i]=v;hpos[v]=i;}
 void insert(int v){if(hpos[v]>=0)return;hpos[v]=heap.size();heap.push_back(v);up(hpos[v]);}
 int pick(){while(!heap.empty()){int v=heap[0];hpos[v]=-1;int b=heap.back();heap.pop_back();if(!heap.empty()){heap[0]=b;hpos[b]=0;down(0);}if(assigns[v]<0)return v;}return -1;}
 void bump(int v){activity[v]+=inc;if(activity[v]>1e100){for(auto &a:activity)a*=1e-100;inc*=1e-100;}if(hpos[v]>=0)up(hpos[v]);}
 bool enqueue(int lit,int r){int z=value(lit);if(z>=0)return z==1;int v=lit/2;assigns[v]=1^(lit&1);level[v]=dl();reason[v]=r;trail.push_back(lit);return true;}
 int add(vector<int> a,bool learned=false){
  if(!learned){sort(a.begin(),a.end());vector<int>b;for(int l:a){if(!b.empty()&&l==(b.back()^1))return -1;if(!b.empty()&&l==b.back())continue;int val=value(l);if(val==1)return -1;if(val!=0)b.push_back(l);}a=move(b);}
  if(a.empty()){ok=false;return -1;}
  if(a.size()==1){if(!enqueue(a[0],-1))ok=false;return -1;}
  int ci=clauses.size();int lbd=0;vector<int> levels;for(int l:a)levels.push_back(level[l/2]);sort(levels.begin(),levels.end());lbd=unique(levels.begin(),levels.end())-levels.begin();clauses.push_back({move(a),learned,lbd,conflicts});auto &c=clauses.back().a;watches[c[0]^1].push_back(ci);watches[c[1]^1].push_back(ci);return ci;
 }
 int propagate(){
  while(qhead<trail.size()){
   int p=trail[qhead++],falseLit=p^1;auto &ws=watches[p];size_t j=0;
   for(size_t i=0;i<ws.size();i++){
    int ci=ws[i];auto &c=clauses[ci].a;if(c.empty())continue;if(c[0]==falseLit)swap(c[0],c[1]);
    if(value(c[0])==1){ws[j++]=ci;continue;}
    bool moved=false;for(size_t k=2;k<c.size();k++)if(value(c[k])!=0){swap(c[1],c[k]);watches[c[1]^1].push_back(ci);moved=true;break;}
    if(moved)continue;ws[j++]=ci;
    if(value(c[0])==0){for(size_t k=i+1;k<ws.size();k++)ws[j++]=ws[k];ws.resize(j);return ci;}
    enqueue(c[0],ci);
   }
   ws.resize(j);
  }
  return -1;
 }
 void cancel(int lvl){if(dl()<=lvl)return;int from=limits[lvl];for(int i=(int)trail.size()-1;i>=from;i--){int v=trail[i]/2;phase[v]=assigns[v];assigns[v]=-1;reason[v]=-1;insert(v);}trail.resize(from);qhead=from;limits.resize(lvl);}
 pair<vector<int>,int> analyze(int ci){
  vector<int> out(1,-1),touched;int path=0,p=-1,index=(int)trail.size()-1;
  do{
   clauses[ci].touch=conflicts;auto &c=clauses[ci].a;
   for(int l:c){int v=l/2;if(p>=0&&v==p/2)continue;if(!seen[v]&&level[v]>0){seen[v]=1;touched.push_back(v);bump(v);if(level[v]==dl())path++;else out.push_back(l);}}
   while(!seen[trail[index]/2])index--;p=trail[index--];seen[p/2]=0;path--;ci=reason[p/2];
  }while(path>0);
  out[0]=p^1;
  // A learned literal is redundant if its antecedents already occur in the cut.
  size_t keep=1;
  for(size_t i=1;i<out.size();i++){
   int v=out[i]/2,ri=reason[v];bool redundant=ri>=0;
   if(redundant)for(int l:clauses[ri].a)if(l/2!=v&&level[l/2]>0&&!seen[l/2]){redundant=false;break;}
   if(!redundant)out[keep++]=out[i];
  }
  out.resize(keep);int bt=0,best=1;for(size_t i=1;i<out.size();i++)if(level[out[i]/2]>bt){bt=level[out[i]/2];best=i;}
  if(out.size()>1)swap(out[1],out[best]);for(int v:touched)seen[v]=0;return {move(out),bt};
 }
 void reduce(){
  vector<uint8_t> locked(clauses.size());for(int r:reason)if(r>=0)locked[r]=1;
  vector<int> removable;
  for(size_t i=0;i<clauses.size();i++)if(clauses[i].learnt&&clauses[i].a.size()>2&&clauses[i].lbd>2&&!locked[i])removable.push_back(i);
  sort(removable.begin(),removable.end(),[&](int a,int b){if(clauses[a].lbd!=clauses[b].lbd)return clauses[a].lbd<clauses[b].lbd;return clauses[a].touch>clauses[b].touch;});
  for(size_t j=removable.size()/2;j<removable.size();j++){vector<int>().swap(clauses[removable[j]].a);}
 }
 static int luby(int x){int size=1,seq=0;while(size<x+1){size=2*size+1;seq++;}while(size-1!=x){size=(size-1)/2;seq--;x%=size;}return 1<<seq;}
 int solve(){
  if(!ok)return 0;uint64_t restartAt=conflicts+100,reduceAt=conflicts+20000;int restartIndex=0;
  for(;;){
   if((conflicts&1023)==0&&chrono::steady_clock::now()>deadline)return -1;
   int ci=propagate();
   if(ci>=0){conflicts++;if(!dl())return 0;auto [learned,bt]=analyze(ci);cancel(bt);int first=learned[0];int id=add(move(learned),true);if(!ok)return 0;if(id>=0)enqueue(first,id);inc/=0.95;
    if(conflicts>=restartAt){cancel(0);restartAt=conflicts+100*luby(++restartIndex);}
    if(conflicts>=reduceAt){reduce();reduceAt=conflicts+20000;}
   }else{int v=pick();if(v<0)return 1;decisions++;limits.push_back(trail.size());enqueue(2*v+(phase[v]?0:1),-1);}
  }
 }
};
// The optional block list contains the Boolean indicators of every P/B cell.
// Blocking this complete history ignores auxiliary selector assignments.
int main(){
 int n,m;double seconds;cin>>n>>m>>seconds;
 if(!cin||n<1||m<0||seconds<=0)return 3;
 Sat s(n,seconds);
 for(int i=0;i<m;i++){int k;cin>>k;vector<int>a(k);for(int &l:a)cin>>l;s.add(move(a));}
 int nb=0;vector<int> blockvars;
 if(cin>>nb){blockvars.resize(nb);for(int &v:blockvars)cin>>v;if(!cin)return 3;}
 int first=s.solve(),second=-2;vector<vector<int8_t>> models;
 if(first==1){
  models.push_back(s.assigns);
  if(nb){
   vector<int> block;for(int v:blockvars)block.push_back(2*v+(s.assigns[v]?1:0));
   s.cancel(0);s.add(move(block));second=s.solve();
   if(second==1)models.push_back(s.assigns);
  }
 }
 cout<<"{\"result\":"<<first<<",\"second\":"<<second<<",\"conflicts\":"<<s.conflicts<<",\"decisions\":"<<s.decisions<<",\"models\":[";
 for(size_t j=0;j<models.size();j++){if(j)cout<<',';cout<<'[';for(int i=0;i<n;i++){if(i)cout<<',';cout<<int(models[j][i]);}cout<<']';}
 cout<<"]}\n";
}
