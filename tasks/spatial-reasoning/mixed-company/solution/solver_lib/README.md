# PNG-only reference solver

Inputs are the three PNGs, with arbitrary filenames. Page roles, diagrams,
vertices, line supports, cuts and source-view pairs are inferred from pixels.
The only non-code asset read is a licensed generic DejaVuSans A–Z font.
No scene, target word, SVG, authored camera, saved coordinates or cut list is read.

1. Recover the end-cell outline and target projection lattices.
2. Calibrate the unknown extrusion metric from the spatial square projections.
3. Enumerate both side-face diagonals. Recover candidate face sets independently
   for all eight source projections. Infer a perfect matching of the unlabelled
   views jointly with a complete nonoverlapping shell cover.
4. Register cut markers across target views, quotient coordinate symmetries,
   require one spatial orbit and one source pairing, and develop the hinge tree.
5. Transport visible source pixels using camera-depth masks. This explicitly
   handles ink on the end caps and partial occlusion. Remove geometrical
   outlines without reconstructing missing ink.
6. Recognize ordinary text rows using generic A–Z shape comparisons and require
   a unique confident readout. Output derived measurements and a readout image.

The geometric family is an extruded square-cell solid, inferred from the end
outline; numerical metrics, instance topology, module IDs and pairings are not
constants. Runtime diagnostic images are derived outputs, never input caches.
