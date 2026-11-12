# Latent Exposure — Walkthrough

1. The first image shows an Unexposed plate and a Developed tray in a darkroom; the seven small Apertures diagrams at the bottom left use checks and crosses to specify a closed loop that is non-empty, unbranched, does not touch itself, and has only one connected component. The loop may touch the outer frame of the grid.
2. The second image is a 4×4 Test Strip made with the same apparatus. On the Unexposed board the thick edges give the loop; the cells enclosed by it are the inside positions. The three fragments at the bottom (0N, 1L, 3E) show that each cell's hidden number counts the thick edges among its four sides; cells outside the loop are counted too. Counting this way gives the strip's initial numbers:

```
3 2 1 0
3 2 2 0
3 1 2 2
1 2 2 3
```

3. The circled numbers give the order: R1, R2, C1, C3, R3, C2, R4, C4. A horizontal arrow means the whole row is cyclically shifted right, and a vertical arrow means the whole column is cyclically shifted down. Numbers and letters move together. Each shift distance is the sum of the current numbers in that line's inside positions. The inside region belongs to the board and does not travel with the letters.
4. When a cell is carried from one position to another, compare the shading of its start and end positions: between two inside or two outside positions the number is unchanged; between an inside and an outside position, n becomes 4−n; letters are unchanged. Equivalently, the number is complemented once each time it crosses the loop along its cyclic route.
5. The Developed board shows only four boxed letters and the eight final sums, so the strip has to be replayed to check the rule. The letters alone do not pin down the shifts, but together with the sums they do. The sums actually sampled at the eight moves are 5, 2, 7, 4, 6, 9, 5, 2. These give shifts of 1, 2, 3, 0, 2, 1, 1, 2 (mod 4). Using the initial numbers at each step instead of the current ones, or failing to apply 4−n, does not reproduce the printed sums. The developed strip is:

```
2H 2G 2G 3L
1N 3E 3N 2G
2T 4C 3S 1L
1G 0N 2J 2F
```

   Its row sums 9, 9, 10, 5 and column sums 6, 9, 10, 8 match the printed margins. The four boxed cells are exactly the cells holding 3, and their letters read row by row give LENS.
6. Back to the first image: the Unexposed plate has only letters, no initial numbers, and no given inside region. The four question marks must be reconstructed together with the loop. The eight known circled numbers leave 24 permutations; the labels cannot be filled in by alternating rows and columns. For each legal closed loop, fill in the 36 initial values, then for each permutation of moves replay them in order and check the six row sums and six column sums on the tray.
7. The only interior shape that passes is:

```
..###.
######
###.##
#...#.
...##.
....#.
```

   The row labels are [5, 12, 10, 1, 3, 7] and the column labels are [11, 6, 8, 4, 2, 9].

| Step | Line | Current enclosed sum | Shift mod 6 |
|---:|---|---:|---:|
| 1 | R4 | 5 | 5 |
| 2 | C5 | 9 | 3 |
| 3 | R5 | 3 | 3 |
| 4 | C4 | 5 | 5 |
| 5 | R1 | 5 | 5 |
| 6 | C2 | 2 | 2 |
| 7 | R6 | 1 | 1 |
| 8 | C3 | 3 | 3 |
| 9 | C6 | 4 | 4 |
| 10 | R3 | 12 | 0 |
| 11 | C1 | 5 | 5 |
| 12 | R2 | 13 | 1 |

8. The replay gives:

```
2 4 2 2 2 2
3 1 4 3 1 1
2 2 3 2 3 3
3 3 3 1 2 3
1 3 4 2 4 1
2 0 2 0 1 2
```

   Row sums [14, 13, 15, 15, 15, 7] and column sums [13, 13, 18, 10, 13, 12] all agree with the image.
9. As in the Test Strip, take the letters of the cells holding 3 in the target's final state, row by row:

- r2c1 ← initial r4c1: **P**
- r2c4 ← initial r5c6: **H**
- r3c3 ← initial r4c3: **O**
- r3c5 ← initial r6c5: **T**
- r3c6 ← initial r5c3: **O**
- r4c1 ← initial r5c4: **G**
- r4c2 ← initial r2c2: **R**
- r4c3 ← initial r2c4: **A**
- r4c6 ← initial r3c5: **M**
- r5c2 ← initial r3c2: **S**

   This gives **PHOTOGRAMS**. This serves only as a self-check after the unique numerical solution; it is not used to filter loops.

**Answer: PHOTOGRAMS**
