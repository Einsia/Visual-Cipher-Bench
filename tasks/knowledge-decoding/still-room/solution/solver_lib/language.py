"""General lexical containment, with no puzzle answers or selected-word table."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent

def dictionary():
 return {s for line in (P/'cmudict.dict').read_text().splitlines() if re.fullmatch('[A-Z]+',s:=line.split()[0].split('(')[0].upper())}

def candidate_words(cards):
 lex=dictionary();labels=json.loads((P/'object_lexicon.json').read_text());allwords=[];explanations={}
 for k,card in enumerate(cards):
  found=set()
  for a in labels[card['outer']]:
   for b in labels[card['inner']]:
    a=a.upper();b=b.upper()
    for split in range(1,len(a)):
     w=a[:split]+b+a[split:]
     if w in lex:
      found.add(w);explanations.setdefault(f'{k}:{w}',[]).append([a,b,split])
  if not found:raise ValueError(f'No lexical reading for picture {k+1}: {card}')
  allwords.extend((k,w) for w in sorted(found))
 return allwords,explanations
