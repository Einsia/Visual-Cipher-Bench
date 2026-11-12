# PNG-only reference solver

`../solve.py` reads PNG pixels and only this directory's implementation, general font, general lexical database and CMU pronunciation dictionary. It contains no answer constant, coordinate-to-object table or fixed edit order.

`vision.py` reads the gray mode regions, letter cells, picture cards, receiving frames, ten word lines, circular junctions, picture silhouettes, glyphs and arrowheads. Cards outside the mode regions form the bank. Their outer widths/heights determine which fit inside each empty picture frame, without rotating/resizing. Every frame initially has two candidates, not a preassigned picture. The H and STONE→ONE example are OCR'd; empty letter cells supply only counts. The six printed constraints, including all-card use, reuse and no rotation/resizing, are read from the PNG.

`reasoning.py` searches the 77,235 generic lexical entries, the full set of ordinary object names, every fitting card assignment, every A–Z letter filling and every order of the five edits. Every bank card must occur; a repeated physical card keeps the same name. Substitutions act in place; standalone additions may occur anywhere. The exact spelling cycle closes at the question-marked input. The search does not assume the repeated card, cancellation of two sound operations, or the picture substitution pair.

The search uses word-deletion indices for missing letters and DFS for order/assignment. It does not narrow the lexical or object-name domains.

Recognition supports this upright line-art family, not arbitrary handwriting or artwork.
