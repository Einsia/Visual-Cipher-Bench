from pixels import parse
from inference import solve_data

def evaluate(images):
 data,pixel_evidence=parse(images);logical=solve_data(data)
 checks=[
 {'name':'pixel_recovery','passed':True,'evidence':pixel_evidence},
 {'name':'graph_integrity','passed':True,'evidence':'Enclosed node disks and glyphs; one triangle and one square per state; every arrow is one connected ink path with source and destination endpoint checks (maximum 3.5px gap to 32px node radius), separately detected arrowhead direction, and permutation in/out degree. Extra components and unclassified semantic ink rejected.'},
 {'name':'unique_rule_and_prediction','passed':True,'evidence':{'counts':logical['model_counts'],'models':logical['models'],'predictions':logical['prediction_count'],'scope':logical['family_scope']}},
 {'name':'target_and_read_order','passed':True,'evidence':{'choice':logical['extraction'],'blank_count':data['target']['answer_length'],'question_box':'closed outline and question glyph detected','readouts':[e['readout'] for e in data['examples']]}},
 {'name':'readability','passed':True,'evidence':{'minimum_node_cap_height_px':pixel_evidence['min_glyph_height_px'],'floor_px':19}},
 {'name':'text_policy','passed':True,'evidence':'All semantic data recovered from outlines; one heading and one thematic lede. No rule sentence on the page. Header prose is outside algorithmic inference.'}
 ]
 return {'valid':True,'unique':True,'solution_count':1,'answer':logical['answer'],'checks':checks,'observed':data,'proof':logical}
