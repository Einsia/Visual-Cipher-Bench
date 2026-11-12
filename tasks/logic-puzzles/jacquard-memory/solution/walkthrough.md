# Jacquard Memory — Walkthrough

1. The first image is the loom to be repaired (Pattern Carriage), and the second is the Test Strip. First look at the check/cross diagrams at the very bottom of the second image: the thick lines must form a closed loop that is non-empty, single, unbranched and does not touch itself. The board is not shaded grey: determine the inside positions by following the thick loop, or flood-fill from the outside by crossing non-thick edges. The inside positions do not move with the letters.
2. Match the starting grid at the top left of the Test Strip with the three close-ups at the bottom of the first image: each cell's initial value equals the number of thick lines on its four edges, and cells outside the loop are counted the same way. The target gives only letters, so the initial values must be recovered together with the loop being solved for.
3. The circled numbers on the top-left grid of the second image are not the default row/column alternation. Following 1 to 8, the moves are R2, C3, C2, R3, R4, C1, C4, R1 in turn. The inside cells framed in the first move have values 3 and 2, totalling 5; the whole row is cyclically shifted one place to the right, with numbers and letters travelling together. Tracing the movement of M, A, O, L through the full states, and whether each is inside or outside, shows that a value crossing between inside and outside becomes 4−n; P and E, which move within the same region, are unchanged. The small 0K→4K diagram in the middle of the second image covers the 0/4 case that does not appear in the full states (white 0K → grey 4K, i.e. 0 becomes 4 when crossing between inside and outside).
4. In After 5, the current values of the inside cells of the first column are 2, 3, 1, summing to 6; After 6 shows the whole column cyclically shifted down two places. Here the original inside values summed to 7, so you cannot keep using the initial values, nor the sum of all cells in the column. The modulus is the current grid width; for the target it is 6.
5. The four question marks on the target in the first image are R3, R4, C5, C6. The remaining labels are [1, 3, 6, 8], giving 24 permutations. For each legal closed loop, build the initial values, try each of these 24 move orders in turn, and finally check all six row sums and six column sums together. Whether the letters form words plays no part in the filtering.
6. The full enumeration leaves exactly one solution:

```
...###
....##
######
###...
#.##..
......
```

   Row labels [5, 4, 3, 8, 10, 9], column labels [7, 11, 12, 2, 6, 1]; the question marks are filled as {'R3': 3, 'R4': 8, 'C5': 6, 'C6': 1}.

| Step | Row or column | Current inside sum | Shift |
|---:|---|---:|---:|
| 1 | C6 | 5 | 5 |
| 2 | C4 | 8 | 2 |
| 3 | R3 | 11 | 5 |
| 4 | R2 | 3 | 3 |
| 5 | R1 | 5 | 5 |
| 6 | C5 | 7 | 1 |
| 7 | C1 | 5 | 5 |
| 8 | R4 | 5 | 5 |
| 9 | R6 | 0 | 0 |
| 10 | R5 | 7 | 1 |
| 11 | C2 | 2 | 2 |
| 12 | C3 | 5 | 5 |

7. The final values are:

```
1 1 2 1 4 4
3 0 1 1 1 3
1 3 1 1 3 2
1 1 1 1 0 1
4 3 3 2 2 1
0 3 1 3 1 2
```

   Row sums [13, 9, 11, 5, 15, 10] and column sums [10, 11, 9, 9, 11, 13] all match the puzzle image.
8. The boxes in the second image's Run-out, together with the 3 → LOOM beside them, show that only the letters whose final value is 3 are taken, read in the usual row-by-row order. For the target, in order:

- r2c1 ← loaded r3c2: **T**
- r2c6 ← loaded r2c3: **A**
- r3c2 ← loaded r1c3: **P**
- r3c5 ← loaded r2c2: **E**
- r5c2 ← loaded r3c3: **S**
- r5c3 ← loaded r6c3: **T**
- r6c2 ← loaded r4c3: **R**
- r6c4 ← loaded r4c4: **Y**

   The answer is **TAPESTRY**.

**Answer: TAPESTRY**
