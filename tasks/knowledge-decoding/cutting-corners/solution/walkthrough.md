# Cutting Corners — Walkthrough

Positions in the large crossword are counted from its top-left corner, 1-based: "row 7, column 1" is the seventh white-path row from the top, first column from the left. Rows and columns of the small example are described in words.

1. **Read the example (top band).**
   - BEFORE shows a small L-shaped crossword: a music-note picture cell, two empty ringed cells and two empty cells across; an empty cell, an empty ringed cell and an empty cell going down. Beside it is a small stencil carrying a D in its top-left corner and an O above a K in its right-hand column.
   - AFTER is the same grid filled in. Turned a quarter turn anticlockwise, the stencil puts O and K at the end of the across run and D at the foot of the down run; those three letters appear in bold. The rest reads NOTE + B, O, O, K = NOTEBOOK across and NOTE + P, A, D = NOTEPAD down.
   - So: every white run is a word; a picture cell is a whole word shared by the run across and the run down; each stencil is turned (never flipped) and laid on the grid so its letters fill empty cells; every other empty cell (ringed or not) takes one letter.
   - The three blanks under AFTER hold B, O, A: the ringed letters in the order you read a page (top row left to right, then down). The plain P is not copied. Column-by-column reading would give A, B, O, which is not what the blanks show.

2. **Place the stencils from the easy runs.** Each stencil fits the big grid in only a few ways (the E/O/H stencil in 8, the D/T/A stencil in 11, the A/O/G stencil in 18, the I/F stencil in 34), and only one choice for each leaves every run a word.
   - Row 7 starts at the tick mark (left edge) and reads tick plus four cells; the column below the tick is tick plus two cells. Turned half a turn, the D/T/A stencil puts A in row 7, column 3, T in row 8, column 6 and D in row 9, column 1. Row 7 becomes tick, empty, A, empty, empty: CHECK + MATE = CHECKMATE, so this tick stands for CHECK. Straight down from it, tick, empty, D = CHECKED.
   - Turned half a turn, the A/O/G stencil puts G and O in row 6, columns 7 and 8, and A in row 10, column 6. Turned a quarter turn anticlockwise, the I/F stencil puts F in row 6, column 10 and I in row 7, column 9.
   - Row 6 now ends GO _ F: GOLF, which puts L at the top of the column in row 6, column 9. That column reads L, I, empty, empty, then the second tick mark at the bottom: LIPS + TICK = LIPSTICK. Here the same tick picture is TICK, not CHECK.
   - Turned half a turn, the E/O/H stencil puts H in row 1, column 6, O in row 3, column 5 and E in row 5, column 6.
   - Under the flower (row 1, column 3) the column is flower, empty, empty: FLOWER + ED = FLOWERED, so the bottom cell (row 3, column 3) is D.

3. **Telephone (row 8, column 7).**
   - Its row reads empty, T, telephone: ST + RING = STRING, so the picture is read as RING; this also puts S under the pencil's column (row 8, column 5).
   - Its column reads telephone, ringed, ringed: RING + ER = RINGER. The last ringed cell is shared with the bottom row (row 10): A, ringed, empty, tick: ARC + TIC = ARCTIC. TIC is the tick mark's sound spelled another way, which confirms R and fills C.
   - Ringed letters found so far: E (row 9, column 7) and R (row 10, column 7).

4. **Pencil (row 5, column 5).**
   - Its column reads pencil, ringed, E (from CHECKMATE), S (from STRING). Nothing starting with PENCIL fits; the pencil's lead, said "led", does: LED + GES = LEDGES, so the ringed cell (row 6, column 5) is G.
   - Its row reads pencil, E, ringed: the same word spelled LEAD gives LEAD + EN = LEADEN, so that ringed cell (row 5, column 7) is N.

5. **Scales (row 3, column 7).**
   - Its row reads D (from FLOWERED), empty, O, empty, scales. Scales themselves give no word; what scales do, WEIGH, said "way", gives D-O-O-R + WAY = DOORWAY.
   - Its column reads scales, ringed, ringed, G. With N from LEADEN it is WEIGH + I + N + G = WEIGHING, so the ringed cell right under the scales (row 4, column 7) is I. (WEIGHT would force WAITING and DOOR + WAIT is not a word.)

6. **Flower (row 1, column 3).**
   - Its row reads flower, empty, ringed, H. FLOWER + three letters never ends in H; the same sound spelled FLOUR does: FLOUR + ISH = FLOURISH, so the ringed cell (row 1, column 5) is S.

7. **Read the ringed cells in reading order** (top row first, then down): row 1 S, row 4 I, row 5 N, row 6 G, row 9 E, row 10 R. Copy them onto the six blanks under the grid, as the example did: **SINGER**.

**Answer: SINGER**
