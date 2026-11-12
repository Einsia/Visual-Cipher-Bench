"""Independently check optional C identity rules on all small rehearsal starts.
No instance truth data: geometry/key/angles are read from the supplied PNGs.
"""
import argparse,itertools,json,copy
from pathlib import Path
from pixels import Reader
from infer import run
from search import search


def verify(images):
    reader=Reader(images);e=reader.example(reader.key());slots=[e['initial_quarters'][i] for i in e['exit_order']]
    spec={'cards':e['cards'],'key':e['key'],'readings':3,'changes':[],
          'starting_turns':{'slot_quarters':slots}}
    checks=[]
    for selector in ['below','target_next','departed_previous','fixed_3']:
        expected=set();enumerated=0
        for qs in sorted(set(itertools.permutations(slots))):
            for stack in itertools.permutations(range(4)):
                x=dict(e,stack=list(stack),initial_quarters=list(qs))
                states,trace=run(x,selector,'new_target',3);enumerated+=1
                exits=[t['chosen'] for t in trace]+states[-1]['stack']
                if [qs[i] for i in exits]!=slots:continue
                expected.add((''.join(t['letter'] for t in trace),
                              ''.join(str(i+1) for i in stack),
                              ''.join(str(i+1) for i in exits[:-1]),
                              ''.join(str(t['target']+1) for t in trace),
                              ''.join(str(t['echo'][0]+1) if t['echo'] else '0' for t in trace),
                              ''.join(map(str,qs))))
        result=search(spec,mode=0,workers=4,npoints=1,rule=[selector,'new_target',3])
        actual={tuple(line) for line in result['lines']}
        lazy=search(spec,mode=1,workers=4,npoints=1,rule=[selector,'new_target',3])
        project=lambda row:tuple([row[0]]+list(row[2:]))
        expected_traces={project(row) for row in expected}
        lazy_traces={project(row) for row in lazy['lines']}
        check={'selector':selector,'python_initial_cases':enumerated,'python_survivors':len(expected),
               'c_survivors':len(actual),'match':actual==expected and lazy_traces==expected_traces,
               'lazy_search_matches_all_exhaustive_traces':lazy_traces==expected_traces,
               'lazy_missing':sorted(expected_traces-lazy_traces),'lazy_extra':sorted(lazy_traces-expected_traces),
               'missing':sorted(expected-actual),'extra':sorted(actual-expected)}
        checks.append(check)
    return {'valid':all(c['match'] for c in checks),'checks':checks}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    report=verify(a.images);Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));raise SystemExit(0 if report['valid'] else 1)
