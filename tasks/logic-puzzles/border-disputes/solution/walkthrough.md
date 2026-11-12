# Border Disputes — Walkthrough

The top of the page is a 4×4 example: its Original grid with circled move numbers, a partial board After 5, and a partial Final board with signed sums and the readout ECHO. The middle holds seven small loop-legality diagrams and the sum key. The bottom holds the 6×6 target. Blank cells on the two partial boards are simply not shown; they are not zeros. All positions and values below are read from this image.

1. Look at the small check/cross diagrams: the thick lines run along cell edges and form a closed loop that is non-empty, single, unbranched and does not touch itself; the outer border may be part of the loop. The cells inside this loop are its interior. The loop is drawn identically on all three example boards, so it stays fixed while the contents move.

2. The sum key shows a boxed (inside) cell counting **+** and an outside cell counting **−**. So each printed row or column sum is the sum of the values inside the loop minus the sum of the values outside it.

3. The example's interior is r1c2; r2c1–r2c3; r3c3–r3c4; r4c2–r4c3 (eight cells). The example only gives letters at the start, so the starting numbers must be inferred. The natural reading that makes all the partial observations work is: each cell starts with the number of its four edges that are thick (cells outside the loop are counted too). For the example this gives

```
2 3 2 0
3 1 2 2
1 3 1 3
1 3 2 2
```

4. The circled numbers give the order of moves: on the left, top to bottom, 1, 2, 5, 7; along the top, left to right, 3, 4, 6, 8. So row 1 moves first, then row 2, column 1, column 2, row 3, column 3, row 4, column 4. A move takes the **current** values in the interior cells of that line, adds them, and cyclically shifts the whole line (number and letter together) that many places, modulo the line length, to the right for a row or down for a column. When a number lands in a cell with different membership (inside versus outside) than the one it left, it becomes 4 − n; otherwise it is unchanged.

   In the example the current interior sums are 3, 6, 2, 7, 4, 6, 5, 3, giving shifts 3, 2, 2, 3, 0, 2, 1, 3. Checks against the page:

   - After 5, r1c3 holds 0C and r2c3 holds 3O, which is exactly what the first five moves produce from the starting numbers above.
   - At step 6, column 3's current interior values sum to 6 (shift 2). Its original interior values would sum to 5 (shift 1); shifting by original values throughout would leave, for example, 2F at r1c3 instead of the printed 3E. So the shift always uses current values.
   - Final has 3E, 3C, 3H and 3O in the shown positions, and 4C at r3c3. The completed Final is

```
1 2 3 3
3 1 2 1
1 1 4 3
2 2 2 2
```

     whose signed row sums are −5, 5, 5, 0 and signed column sums −1, 4, 5, −3, exactly as printed. For instance, the top row gives −1 + 2 − 3 − 3 = −5 because only its second cell is inside.

5. The framed cells in the example Final are exactly the cells whose final number is 3, and reading them in the usual row-by-row order gives ECHO. The unframed 4C shows that other values are not read. So the answer is read from the final value-3 cells.

6. The target gives only letters and an empty Final grid with signed sums. Its arrows are labelled 1–12, but the circles for R1, C2, R4 and C5 contain question marks. The eight known numbers leave 1, 4, 7, 10 to fill these four places, and they cannot be fixed in advance by position or parity. Both the loop and the order are unknown; together they must make the signed sums on the right and bottom of Final hold.

7. A finite enumeration is now possible: try the closed loops that satisfy the legal shapes; each loop determines 36 initial numbers, then try the 24 arrangements of the four missing labels. Step by step, sum the current interior cells, shift the whole row or column, and update the numbers that cross the boundary. Keep only the combinations in which all six signed row sums and six signed column sums of the final state are correct. This process does not use whether the letters form words or the length of the answer. The full enumeration leaves only the following interior shape:

```
...##.
#...##
#..##.
#####.
#.##..
...#..
```

   The row labels, top to bottom, are [7, 3, 5, 4, 9, 11], and the column labels, left to right, are [2, 1, 6, 8, 10, 12]. So column 2 moves first, then column 1, then rows 2, 4 and 3; this is not an alternating order. The initial numbers (thick-edge counts) are:

```
1 0 1 3 2 2
3 1 0 3 1 3
2 2 2 2 1 2
1 2 1 0 2 1
3 3 2 1 2 0
1 0 2 3 1 0
```

8. Recomputing with the determined order of moves, the current sum and shift at each step are as follows. A shift of 0 still counts as performing that move; later labels must not be brought forward.

| Step | Line | Current enclosed sum | Shift mod 6 |
|---:|---|---:|---:|
| 1 | C2 | 2 | 2 |
| 2 | C1 | 9 | 3 |
| 3 | R2 | 7 | 1 |
| 4 | R4 | 9 | 3 |
| 5 | R3 | 6 | 0 |
| 6 | C3 | 5 | 5 |
| 7 | R1 | 5 | 5 |
| 8 | C4 | 11 | 5 |
| 9 | R5 | 8 | 2 |
| 10 | C5 | 7 | 1 |
| 11 | R6 | 2 | 2 |
| 12 | C6 | 1 | 1 |

9. The final numbers are:

```
3 0 1 4 3 2
3 1 2 2 2 1
3 0 1 3 1 3
0 2 2 1 1 2
2 0 3 2 1 3
2 0 2 2 1 1
```

   Counting interior cells as + and the rest as −, the row sums are [1, 1, 3, 4, 3, −4] and the column sums are [3, 1, −1, 10, 5, −10], matching the page.

10. As in the example, read only the cells whose final number is 3, row by row:

- r1c1 ← original r5c2: S
- r1c5 ← original r6c5: Q
- r2c1 ← original r2c6: U
- r3c1 ← original r6c1: A
- r3c4 ← original r1c1: T
- r3c6 ← original r2c5: T
- r5c3 ← original r2c1: E
- r5c6 ← original r4c3: R

   In order this gives **SQUATTER**.

**Answer: SQUATTER**
