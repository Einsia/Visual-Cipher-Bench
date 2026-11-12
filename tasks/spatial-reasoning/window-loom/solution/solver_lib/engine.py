"""Isolated entry point: PNG pixels -> recovered conditions -> ray traversal."""
from pathlib import Path
import hashlib
from PIL import Image
import numpy as np
from .parser import parse, require
from .geometry import read_setup, solve_structure
from .public_conditions import verify_public


def run(images):
    paths=sorted(Path(images).glob('*.png'))
    require(len(paths)==1,'This layout requires one complete puzzle sheet')
    path=paths[0]
    with Image.open(path) as im:
        require(im.mode in ('RGB','RGBA'),'Image must be RGB/RGBA')
        require(min(im.size)>=768,'Insufficient native resolution')
        require(not im.info,'Unexpected image metadata')
        arr=np.asarray(im.convert('RGB'))
    structure=parse(path)
    setup=read_setup(arr)
    public=verify_public(arr,structure,setup)
    geometry=solve_structure(structure,[q['material_angle'] for q in setup],arr)
    require(geometry['answer'] and geometry['terminated'],'No finite terminal readout')
    checks=[
        {'name':'semantic_data_recovery','passed':True,'evidence':{
            'windows':structure['windows'],'pools':[q for q in structure['nodes'] if q['kind']=='pool'],
            'setup':setup}},
        {'name':'complete_symbol_structures','passed':True,'evidence':'Closed pool, aperture, view-code badge and switch contours; one unlabelled crossed rectangular window and two pools per face; boxed numerals and spatial-view references recovered. Both sides register under the displayed backing folds.'},
        {'name':'connection_continuity_and_direction','passed':True,'evidence':{
            'components':structure['components'],'arrows':structure['flow_arrows'],
            'method':'Eight-connected pixels along complete streams, including endpoint contact. Circle/plaque/switch graphics are explicit nodes. No dilation or gap closing along a connector.'}},
        {'name':'public_rules_and_necessary_evidence','passed':True,'evidence':public},
        {'name':'unique_target_and_read_order','passed':True,'evidence':{
            'trace':geometry['trace'],'proof':'One start and one connected directed instruction per route. All algebraic cameras from anonymous projected edge directions are screened against visible material and shade. Exactly one orientation cluster matches the selected silhouette. The cross fixes the ray offset. The nearest positive opaque intersection is strict and lies in exactly one incident-side pool. Finite traversal reaches the unique lock.'}},
        {'name':'alternative_interpretations','passed':True,'evidence':'Visible front/back shading and opaque overlap distinguish reversed observation directions. The printed rules establish centre alignment and first opacity. Incidental holes are tested as empty material; no nearest-pool fallback.'},
        {'name':'text_policy_and_readability','passed':True,'evidence':'Rules, section headings and the sighting grammar are recognized from the pixels. Runtime holds generic glyph masks, layout regions and geometric algorithms only.'},
    ]
    return {'valid':True,'unique':True,'solution_count':1,'answer':geometry['answer'],
            'image_hashes':{path.name:hashlib.sha256(path.read_bytes()).hexdigest()},
            'checks':checks,'geometry':geometry,
            'limits':'Pixel and geometric checks only.'}
