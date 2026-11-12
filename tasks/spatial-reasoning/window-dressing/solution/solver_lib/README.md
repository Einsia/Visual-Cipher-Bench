# PNG-only recognition resources

`solve.py` reads only the supplied PNG directory and these generic resources. It uses no word list.

- `templates340.npz`: the complete A–Z uppercase family, 26 masks at the displayed main cap height, each on a 440 × 500 registration canvas. It contains no selected glyph list or position/permutation table. Letter scale and family follow the puzzle's illustrated convention.
- `DejaVuSans*.ttf` and `LICENSE-DejaVu.txt`: general fonts used solely to read the small printed example letters and rank digits.
- `pixel_structure.py`: checks the independent frame tabs, the empty space between the two windows, answer slots, H merge, HAT ordering and the indirect union examples from pixels. Example ROIs describe page layout, not the answer.
- `joint_model.py`: generic full-alphabet visible-white rejection and visible-black union coverage.
- `unpaired_model.py`: solves each independently positioned view, joins equal letter multisets and enumerates every glyph-preserving bijection, including repeated letters. No all-different assumption. A separate check also enumerates View B permutations independently.

The final diagrams need no OCR network, font download or installation. The solver works from the PNGs, with an absolute total mismatch budget of 200 pixels for antialiasing. A complete final fit has 84 differing pixels.
