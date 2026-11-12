"""Infer read order from spatial example outputs, then use word confirmation.

run()['answer'] is a raw row scan, not a mandated extraction convention.
In particular do not assume row reading when the second example refutes it.
"""
import json
from pathlib import Path
from model import fit, run, readouts

def infer(spec):
    fitted=fit(spec)
    words=set(json.loads((Path(__file__).parent/'words_all.json').read_text()))
    answers=set(); candidates=[]
    for parameters in fitted['survivors']:
        allowed=None
        for example in spec['examples']:
            result=run(example['before'],parameters)
            orders={k for k,v in readouts(result).items() if v==example['output']}
            allowed=orders if allowed is None else allowed & orders
        result=run(spec['target'],parameters)
        readings=readouts(result) if result['status']=='stop' else {}
        matched={k:v for k,v in readings.items() if k in allowed and v in words}
        answers.update(matched.values())
        candidates.append({'parameters':parameters,'status':result['status'],
            'allowed_orders':sorted(allowed),'readings':readings,'word_matches':matched})
    return {'family':fitted,'answers':sorted(answers),'candidates':candidates}
