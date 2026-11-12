from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).parent/'solver_lib'))
from pixel_reader import read
from compute import compute
p=argparse.ArgumentParser();p.add_argument('--images',required=True);p.add_argument('--output',required=True);args=p.parse_args()
try:
 data=read(args.images);r=compute(data)
 result={'answer':r['answer'],'valid':r['valid'],'unique':r['unique'],'solution_count':r['solution_count'],'pixel_data':data,'proof':r}
except (ValueError,OSError) as e:result={'answer':None,'valid':False,'unique':False,'solution_count':0,'error':str(e)}
Path(args.output).write_text(json.dumps(result,indent=2))
print(json.dumps({k:result[k] for k in ['answer','valid','unique','solution_count']}))
sys.exit(0 if result['valid'] else 1)
