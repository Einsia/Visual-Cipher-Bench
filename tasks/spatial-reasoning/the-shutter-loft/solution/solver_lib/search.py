"""Independent necessary-point footprint screening; exact survivor checks follow."""
import random,math,json,subprocess,time,tempfile,hashlib,platform
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def inside(p,q):return all((b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0])>=-1e-9 for a,b in zip(p,p[1:]+p[:1]))
def in_union(polys,q):return any(inside(p,q) for p in polys)
def line_distance(a,b,p):return abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))/max(1e-30,math.hypot(b[0]-a[0],b[1]-a[1]))
def prepare(spec,npoints=384,seed=913):
 cards=spec['cards'];changes=spec['changes'];allp=[c['polygon'] for c in cards]+[p for o in changes for p in o['pieces']];extent=max(abs(z) for p in allp for v in p for z in v)+.25
 edges=[(a,b) for p in allp for a,b in zip(p,p[1:]+p[:1]) if a!=b];r=random.Random(seed);pts=[]
 while len(pts)<npoints:
  p=[r.uniform(-extent,extent),r.uniform(-extent,extent)]
  if min(line_distance(a,b,p) for a,b in edges)<.0001:continue
  pts.append(p)
 key={(k['family'],k['turn']):k for k in spec['key']};lines=[f"{len(cards)} {spec['readings']} {len(pts)}"]
 for c in cards:
  lines.append(str(len(c['polygon'])));lines+=[' '.join(map(str,p)) for p in c['polygon']];lines.append(' '.join(map(str,c['dot'])))
  lines.append(' '.join(f"{key[c['family'],(c['turn']+t)%4]['letter']} {key[c['family'],(c['turn']+t)%4]['count']}" for t in range(4)))
 lines+=[' '.join(map(str,p)) for p in pts];lines.append(str(len(changes)))
 for o in changes:
  lines.append(f"{o['from']} {o['to']}");lines.append(' '.join(str(int(in_union(o['pieces'],p))) for p in pts))
 if 'starting_turns' in spec:lines.append(' '.join(map(str,spec['starting_turns']['slot_quarters'])))
 return '\n'.join(lines)+'\n'

def search(spec,mode=1,workers=9,npoints=384,seed=913,input_text=None,rule=None):
 rule_ids={"below":0,"target_next":1,"departed_previous":2,"fixed_3":3}
 if rule is None:rule=["below","new_target",3]
 if rule[1:]!=["new_target",3] or rule[0] not in rule_ids:raise ValueError(("Unsupported inferred rule",rule))
 rule_id=rule_ids[rule[0]]
 started=time.perf_counter()
 lib=Path(__file__).resolve().parent
 manifest=json.loads((lib/'search_build.json').read_text())
 if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
  raise RuntimeError('Bundled search executable requires Linux x86_64; rebuild search.c for this platform.')
 exe=lib/'search_linux_x86_64'
 for path,key in [(lib/'search.c','source_sha256'),(exe,'executable_sha256')]:
  if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest[key]:
   raise RuntimeError('Search source/executable does not match search_build.json: '+path.name)
 with tempfile.TemporaryDirectory(prefix='relay_') as td:
  td=Path(td);inp=td/'input';inp.write_text(input_text if input_text is not None else prepare(spec,npoints,seed))
  def run(i):
   dest=td/f'{i}.txt';p=subprocess.run([str(exe),str(inp),str(dest),str(mode),str(i),str(workers),str(rule_id)],capture_output=True,text=True,check=True,timeout=560);return json.loads(p.stdout),dest.read_text().splitlines()
  with ThreadPoolExecutor(max_workers=workers) as ex:raw=list(ex.map(run,range(workers)))
 stats=[a for a,b in raw];lines=[l.split() for a,b in raw for l in b];keys=['permutations','states','survivors','ties_branched','area_queries','cache_hits','clip_calls','cpu_seconds','reveals','orientation_cases','coupling_rejections'];summary={k:sum(s[k] for s in stats) for k in keys};summary.update({'wall_seconds':time.perf_counter()-started,'workers':workers,'mode':mode,'point_witnesses':npoints,'nodes_by_depth':[sum(s['nodes_by_depth'][j] for s in stats) for j in range(spec['readings']+1)],'rejections':[sum(s['rejections'][j] for s in stats) for j in range(spec['readings']+1)]})
 return {'stats':summary,'answers':sorted({l[0] for l in lines}),'trajectory_classes':sorted({(l[2],l[3],l[4]) for l in lines}),'lines':lines}
