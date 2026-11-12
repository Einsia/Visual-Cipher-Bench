# The Shutter Loft — Walkthrough

1. Read the eight oriented stamp entries on sheet 1. They encode D/2, R/1, A/3, E/3 for the four corner marks, and S/2, I/1, T/1, M/3 for the four triangular marks.
2. Compare the rehearsal templates with the lower starting poses. The 90-degree overlay leaves the blade's own dot fixed. Its exit slot determines that initial turn. The complete Bottom-to-Top row describes a separate order.
3. Read sheet 2 left to right across each rehearsal band, then downward to the next band. The heading "Total exposed area" names the selection rule: in each opaque checkpoint, measure how much of every blade is visible on the grid, adding together the pieces of a blade that is split by blades above it. The blade with the largest total is the one removed. In band 0 the top blade 1 is largest; in the middle band, blade 4 beats the top blade. Blade 2's two exposed pieces are summed.
4. Follow the surviving numbered ring. Removal precedes counting. Absent identities are skipped. In the second band, the count wraps around through 2, 3, 2.
5. Sheet 2 shows only complete opaque checkpoints, so the two motions of each round must be inferred by matching the blade outlines, attached dots and stamps from one checkpoint to the next. The first motion: the counted blade turns clockwise 90° about the departing blade's current dot and is raised to the top. In band 0, blade 3 (counted) reappears on top in checkpoint 1 turned a quarter clockwise about the spot where blade 1's dot was. The second motion: the blade immediately beneath the raised blade then turns anticlockwise 90° about the raised blade's new dot. The one-round rehearsal at the upper right of sheet 2 settles which blade makes it: starting from Bottom→Top 1,3,4,2 with the printed initial angles, only moving the immediate underlayer (blade 3) anticlockwise 90° about the newly moved target dot reproduces checkpoint 1. Moving the next surviving number after the top blade or the previous one before the departing blade would move blade 1, and a fixed blade would move blade 4; both disagree with the drawn checkpoint. Track blade boundaries and attached dots through every round.
6. The fixed crosses and the two exclusive rectangle strips establish a registered symmetric difference, not union, intersection, or a freely translated shape match.
7. On sheet 3 trace the nine Loft inventory blade polygons and dots from the common grids. Jointly solve the nine unknown initial layers and the departure-dependent initial turns. An arbitrary forward run cannot assign its turns afterward: changing a starting turn changes the geometry and selection sequence.
8. A valid bottom-to-top order is 1, 3, 5, 7, 4, 8, 9, 2, 6. The angles by identity are 270, 180, 0, 180, 270, 0, 90, 90, 0 degrees. Execute the rounds as follows.

| Round | Exit | Exposed area | Read | Count | Raised blade | Underlayer | Departed pivot |
|---:|---:|---:|:---:|---:|---:|---:|---|
| 1 | 6 | 84.000000 | S | 2 | 8 | 2 | [0, 2] |
| 2 | 2 | 73.357143 | T | 1 | 3 | 8 | [4, 2] |
| 3 | 9 | 59.518455 | R | 1 | 1 | 3 | [0, -1] |
| 4 | 1 | 73.000000 | E | 3 | 5 | 3 | [0, -1] |
| 5 | 5 | 131.500000 | A | 3 | 3 | 8 | [-1, 1] |
| 6 | 4 | 99.833333 | M | 3 | 3 | 8 | [0, 2] |
| 7 | 7 | 69.893370 | E | 3 | 8 | 3 | [-1, 1] |
| 8 | 8 | 57.000000 | R | 1 | 3 | — | [-5, -4] |

9. Compare the occupied-union XOR after rounds 2 and 6 with the gray observation. STREAMER matches exactly. Another closure-compatible English output, ITERATED, does not.
10. Fill the eight Exit blanks chronologically with S T R E A M E R. Blade 3 remains in Stay and is unread.

**Answer: STREAMER**
