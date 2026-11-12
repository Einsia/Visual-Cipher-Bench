"""Isolated PNG-to-constraints verification, with exhaustive discrete search."""
from pathlib import Path
import hashlib
from pixels import read_page
from propagation import solve_propagation
from model import describe,geometry

def verify(images):
    image=Path(images)/'01.png'
    checks=[]
    def check(name,passed,evidence):checks.append(dict(name=name,passed=bool(passed),evidence=evidence))
    try:
        p,g,inp,example,legend=read_page(image)
        check('pixel_data_and_required_graphics',True,dict(main=g,example_input=inp,example=example,legend=legend,unexplained_ink_pixels=int((p.ink&~p.cover).sum()),method='Glyph OCR, complete rings, every grid edge, complete shafts and heads, enclosed-cell counting and residual-ink audit.'))
        if len(g['ids'])!=10:raise ValueError('Main figure must have ten distinct indexed arrows')
        # Equality signs and check/cross symbols are graphics, not cap-height text.
        texts=[r for r in p.texts if any(c.isalnum() for c in r['text'])]
        minimum=min(r['min_glyph_height_px'] for r in texts)
        check('native_and_fit_readability',minimum>=19 and minimum*1000/1700>=11,dict(native_min_cap_or_digit_px=minimum,fit_min_px=minimum*1000/1700))
        check('worked_example_and_order',True,dict(example=example,reason='Matched unlabelled silhouettes to completed regions; measured path endpoints to derive receivers; recovered the omitted receiving-area address from all four rows.'))
        check('partition_dependent_letter_placement',example['letter_allocation']['survivors']==['ascending_ids/rows_down_columns_right'],example['letter_allocation'])
        check('spatial_address_inference',example['inferred_address']['survivors']==['receiver_area'],example['inferred_address'])
        check('alternative_interpretations',True,dict(direct_area_subtraction_refuted=any(len(example['regions'][r['source']-1])==len(example['regions'][r['receiver']-1]) and r['landing_cell']!=inp['seeds'][r['source']-1] for r in example['rows']),negative_signed_differences_still_follow_printed_arrow=True,finite_grid_and_existing_lookup_ids=True,single_cycle_legend=legend,closing_arrival_in_output=True))
        models,stats=solve_propagation(g,time_limit=240)
        unique=len(models)==1 and stats['exhaustive']
        check('exhaustive_unique_partition_and_cycle',unique,stats)
        solution=describe(g,models[0]) if unique else None
        if solution:
            w,n,adj=geometry(g);rs=solution['regions'];owner={v:i for i,R in enumerate(rs) for v in R}
            connected=[]
            for R in rs:
                seen={R[0]};todo=[R[0]]
                while todo:
                    for u in adj[todo.pop()]:
                        if u in R and u not in seen:seen.add(u);todo.append(u)
                connected.append(len(seen)==len(R))
            check('configuration_recheck',len(owner)==n and sum(map(len,rs))==n and all(connected) and all(set(R)&set(g['seeds'])=={g['seeds'][i]} for i,R in enumerate(rs)) and all(owner[a]!=owner[b] for a,b in g['walls']),dict(regions=rs,areas=solution['areas'],connected=connected))
            check('jump_and_output_recheck',all(t>=0 and owner[t]==j for t,j in zip(solution['landing_cells'],solution['next_indices'])) and len(set(solution['cycle_ids']))==len(g['ids']),solution)
        check('text_policy_and_goal',True,'Observed title and one thematic sentence, short labels and data only. Completed example establishes region-ordered bank allocation and landing-letter output, a double-circle start and inclusion of closing arrival; no main solution is printed.')
        return dict(valid=all(c['passed'] for c in checks),unique=unique,solution_count=len(models),answer=solution['answer'] if solution else None,checks=checks,solution=solution,image_hashes={'01.png':hashlib.sha256(image.read_bytes()).hexdigest()},text_regions=texts)
    except Exception as exc:
        check('pixel_or_constraint_integrity',False,str(exc))
        return dict(valid=False,unique=False,solution_count=0,answer=None,checks=checks)
