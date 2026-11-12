# Reference solver support

`pixels.py` measures the worksheet geometry, recognizes isolated glyphs and pictograms using the bundled class templates, and traces connected bracket pixels to recover the exchanged sides. A whole-word input is recognized by OCR when its input region is not a pictogram. RASH, the operation list and the target column are not embedded as solver answers or state data.

`reasoning.py` enumerates spelling states over the licensed CMUdict/WordNet intersection. It solves the incomplete example first: the printed outputs and English-word constraint determine every missing word and cut, with exactly one terminal path. It then solves the main graph with broad pictogram aliases. Literal-letter alternatives are also tested.

`solve.py` and this directory suffice for a network-disabled run; only the puzzle image and the files here are read. Visual templates are isolated, labelled glyph/object classes, not a full-page image or a mapping of whole images to answers.
