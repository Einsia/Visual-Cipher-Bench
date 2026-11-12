PNG-only reference solver for Front Desk.

Runtime: Python standard library, NumPy, Pillow, bundled static SAT engine.
No network or compiler is needed; solve.py reads only the page images and the
resources in this directory.

text_reader.py reads generic glyphs at value-free text windows. geometry.py
checks contours, interval brackets, arrows, slots and unexpected ink. semantics.py
recovers all eight separation panels: horizontal endpoints establish left/right
by x position; a stacked pair marked Either order establishes absolute distance
only. It checks all four worked exchanges and the extraction example.
wires.py measures extraction paths from pixels without a stored connection table.

model.py uses signed or absolute distance according to the recovered panel.
packing.py enumerates both orientations of each unsigned edge before applying
its necessary packing filter. search.py partitions the full state space,
blocks the complete history after a first solution, and certifies uniqueness
only if every partition is exhausted. cnf.py and engine implement the Boolean
encoding and a small CDCL solver.

regions.json: font metrics and text windows, no transcripts.
geometry.json: non-text drawing contours, no endpoint names or solutions.
glyphs.json: generic font outlines. Every instance name is read from the PNG.
