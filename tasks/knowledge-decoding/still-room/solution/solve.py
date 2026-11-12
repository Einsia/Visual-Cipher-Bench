"""Offline PNG-only reference solver."""
import argparse,json,time
from pathlib import Path
from solver_lib.pixels import read
from solver_lib.language import candidate_words
from solver_lib.search import candidates,solve

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--images',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 start=time.monotonic();cards,net=read(args.images)
 if len(set(net['extraction']))!=19:raise ValueError('Numbered labels must identify 19 distinct cells')
 words,explanations=candidate_words(cards)
 opts=candidates(words,net['loops']);solutions,nodes=solve(net['loops'],opts,net['givens'],limit=2)
 if len(solutions)!=1:raise ValueError(f'Expected a unique assignment, found {len(solutions)}')
 sol=solutions[0];letters={c:sol[i][2][j] for i,l in enumerate(net['loops']) for j,c in enumerate(l)}
 answer=''.join(letters[c] for c in net['extraction'])
 out={'answer':answer,'normalization':'upper_compact','seconds':time.monotonic()-start,'search_nodes':nodes,'cards':cards,'candidate_words':words,'circuits':sol,'explanations':explanations,'pixel_network':net}
 Path(args.output).write_text(json.dumps(out,indent=2));print(answer)
if __name__=='__main__':main()
