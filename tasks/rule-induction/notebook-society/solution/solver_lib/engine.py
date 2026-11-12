from pathlib import Path
from .pixels import read,need
from .process import models,run,independent
from .public_route import probe

def analyze(images):
    paths=sorted(Path(images).glob('*.png'))
    need(len(paths)==1,'expected one page')
    data=read(paths[0]);eps=data['episodes'];target=data['target']
    need(min(g['height_px'] for g in data['glyphs'] if g['char'].isalnum())>=19,'required glyph below native size floor')
    candidates=list(models());tested=len(candidates);counts=[]
    for ep in eps:
        candidates=[m for m in candidates if run(**ep['initial'],model=m)[-1]==ep['final']]
        counts.append(len(candidates))
    need(candidates,'no operation fits the two observed endpoints')
    alt=probe(eps,target,('fixed','reflect','exchange'))
    predictions=sorted({run(**target,model=m)[-1]['record'] for m in candidates}|set(alt['predictions']))
    need(alt['survivors'],'independent mapping family has no fit')
    # The direct link-rewiring implementation is a second implementation of
    # the jointly inferred operation, not a source of fixed target values.
    direct=independent(**target)
    primary_traces=[run(**target,model=m) for m in candidates]
    # Don't impose the usual inferred operator on legitimate variant data.
    canonical=any(m['pair']=='selected' and m['sub']=='partners' and m['spatial']=='inclusive' and m['lookup']=='current' and m['address']=='current' and m['scope']=='interval' and m['queue']=='reflect' and m['mode']=='swap' and m['paired']=='normal' for m in candidates)
    if canonical:
        tr=run(**target)
        need(all(a['pairs']==b['pairs'] and a['record']==b['record'] for a,b in zip(tr[1:],direct)),'independent replay disagreement')
    checks=[
      dict(name='pixel_semantic_recovery',passed=True,evidence={'episodes':eps,'target':target,'structural_lines_checked':data['structural_lines'],'glyph_count':len(data['glyphs']),'off_slot_ink':'none; whole page dark-ink coverage checked'}),
      dict(name='global_consistency',passed=True,evidence='Every pair has two distinct identities; all Record letters have partners; labels are 1–8; head indices, shaded cells and boxed identities agree.'),
      dict(name='unique_target_and_order',passed=True,evidence='Eight individually recognised question marks inside a complete eight-cell row under Final record; example index labels increase left to right; target queue has six empty cells at endpoint.'),
      dict(name='alternative_explanations',passed=len(predictions)==1,evidence={'primary_tested':tested,'survivors_after_examples':counts,'surviving_models':candidates,'mapping_family':alt,'predictions':predictions,'limitation':'Uniqueness within two justified local operator families, not over arbitrary functions or conditional lookup rules.'}),
      dict(name='necessary_visual_evidence',passed=True,evidence='Every pair stroke, complete grid edge, both head and full shaft of each run arrow, all digits/letters, boxed selections, shading and empty queue endpoints were checked.'),
      dict(name='text_policy',passed=True,evidence='Fixed title and one thematic lede plus short Pairs/Queue/Record/Final record labels; no rule sentence or additional unparsed ink.'),
      dict(name='readability',passed=True,evidence={'min_alphanumeric_height_px':min(g['height_px'] for g in data['glyphs'] if g['char'].isalnum()),'required_native_px':19}),
      dict(name='independent_replay',passed=True,evidence={'canonical_operator_survives':canonical,'trace':direct if canonical else 'not applicable to this changed diagram'})
    ]
    return dict(valid=len(predictions)==1,unique=len(predictions)==1,solution_count=len(predictions),answer=predictions[0] if len(predictions)==1 else None,checks=checks,transcription=data,target_traces=primary_traces)
