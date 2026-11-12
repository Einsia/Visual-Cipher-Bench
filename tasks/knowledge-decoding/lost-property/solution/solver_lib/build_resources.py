"""Reproducible whole-dictionary extraction; never used to read a puzzle."""
from pathlib import Path
from collections import Counter
import re
import argparse
parser=argparse.ArgumentParser(description='Extract complete general WordNet resources offline')
parser.add_argument('--wordnet',type=Path,required=True,help='WordNet 3.1 dict directory')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
src=args.wordnet
dst=args.output
dst.mkdir(parents=True,exist_ok=True)
lemmas=set(); phrases=Counter()
for path in src.glob('data.*'):
 for line in path.read_text().splitlines():
  if not line or line.startswith(' '):continue
  head,gloss=line.split('|',1)
  parts=head.split(); n=int(parts[3],16)
  for i in range(n):
   w=parts[4+2*i]
   if w==w.lower() and all(c in 'abcdefghijklmnopqrstuvwxyz_-' for c in w): lemmas.add(w)
  for phrase in re.split('[^a-zA-Z -]+',gloss):
   words=re.findall('[a-z]+',phrase.lower())
   phrases.update(zip(words,words[1:]))
(dst/'wordnet_lexical.txt').write_text('\n'.join(sorted(lemmas))+'\n')
(dst/'wordnet_phrases.tsv').write_text(''.join(f'{a}\t{b}\t{n}\n' for (a,b),n in sorted(phrases.items())))
print(len(lemmas),len(phrases))
import json,gzip
ontology={}
for line in (src/'data.noun').read_text().splitlines():
 if not line or line.startswith(' '): continue
 parts=line.split('|',1)[0].split(); n=int(parts[3],16)
 words=[parts[4+2*i] for i in range(n)]
 k=4+2*n; num=int(parts[k]);k+=1
 parents=[]
 for j in range(num):
  sym,target,pos,scope=parts[k:k+4];k+=4
  if sym in ('@','@i') and pos=='n':parents.append(target)
 ontology[parts[0]]={'words':words,'parents':parents}
with gzip.open(dst/'wordnet_nouns.json.gz','wt',encoding='utf-8') as stream:
 json.dump(ontology,stream,separators=(',',':'))
