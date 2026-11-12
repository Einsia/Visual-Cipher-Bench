Echo Vault — PNG reference solver

Only 01.png, 02.png and 03.png carry instance information at runtime. No
specification, instance, history or answer file is read, and no cached
transcript is used.

text_reader.py recovers glyphs using generic outline fonts and layout windows.
regions.json has no expected strings. geometry.json describes non-text layout;
geometry.py verifies every contour, connected shaft and arrowhead against the
actual raster, rejecting unexplained ink. It is not a source of specimen names,
ring digits, program pairs or observation words.

calibration.py infers the transfer addresses, which are not printed, by testing
1,024 natural readings of the five visible states and four input pairs. It
separately tests 20 extraction readings. Both must have exactly one survivor;
no hidden number is supplied as a constant. semantics.py recognizes the
observation snapshot by comparing its complete visible state and reads the two
bracket arms directly from PNG pixels, then counts slot intervals. The state and
interval must agree with the visible final-ring selectors.

finite_search.py / finite_engine.py solve all nine position/ring permutations,
eight transfers and eight observations. Terminal distance-ring values partition
the full problem into disjoint groups. Within every group, the complete P/B
assignment is blocked after each model and the search continues. Acceptance
requires all groups INFEASIBLE after blocking and exactly one history overall.
Every returned history is replayed independently with ordinary list swaps by
semantics.replay. A timeout is never a uniqueness certificate.

The CP-SAT native helper and its required libraries are bundled under vendor,
with upstream licenses. An alternative CDCL implementation is kept in
search.py / engine.cpp; it is not the default reference search.

Python runtime: 3.12, NumPy, Pillow, bundled native helper. No network, compiler,
API, external package install, answer vocabulary or dictionary is needed.
