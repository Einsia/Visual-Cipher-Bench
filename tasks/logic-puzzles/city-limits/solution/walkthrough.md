# City Limits — Walkthrough

Every cell belongs to one orthogonally connected region containing exactly one numbered arrow. Heavy given internal edges separate different regions. Write A_i for its cell count. For the edge i→j, k=A_j must name an existing numbered region, and the jump from i is the positive distance |A_i−A_k| along its printed arrow. The landing belongs to region j, stays inside the grid, and may cross intermediate cells/boundaries. All ten successor edges form one directed cycle. The grid itself carries no letters: the letter bank under it is poured into the regions in increasing region number, and inside each region the cells are filled in reading order (rows top to bottom, left to right within a row). The double circle fixes the start; collect one letter at each landing, including the closing arrival. No lexical constraint is used to find the configuration.

Every region is a receiver, so every region area is one of the printed identities 1–10. Enumerating all connected subsets of sizes 1–10 rooted at each arrow and containing no other arrow is complete: a spanning-tree growth order reaches every connected set. Any subset containing both endpoints of a given heavy separator is excluded, even if it can reconnect around that edge. The independent cycle and cover programs select a non-overlapping exact cover and enforce every indexed-area jump, then enumerate complete cycles with rotation fixed. The domain-propagation verifier separately uses cell support, area/jump support, permutation constraints and proper-subcycle rejection. Necessary optimistic pruning never accepts a model by itself; final models satisfy every exact condition.

Unique ownership matrix (not printed):

```
 3  7  8  8  2  2
 3  7  7  8  2  2
 9  9  5  8  4  2
 9 10  6  4  4  2
10 10  6  4  1  1
10 10 10  4  1  1
```

## Filling the letter bank

The bank reads ONEOTSRERIASENAAIOAOTLSNETSNCLENAAFD (36 letters, no breaks). The region areas in number order are 4, 6, 2, 5, 1, 2, 3, 4, 3, 6, so the bank splits as

1:ONEO, 2:TSRERI, 3:AS, 4:ENAAI, 5:O, 6:AO, 7:TLS, 8:NETS, 9:NCL, 10:ENAAFD.

Placing each piece into its region's cells in reading order gives the letter grid:

```
A T N E T S
S L S T R E
N C O S E R
L E A N A I
N A O A O N
A F D I E O
```

A letter's position depends on the region shapes, not just on the cell coordinate, so the partition must be solved before any landing can be read.

## The loop

| Source | Area | Receiver area | Lookup ID | Lookup area | Jump | Landing | Next | Letter |
|---|---|---|---|---|---|---|---|---|
| 1 | 4 | 6 | 6 | 2 | 2 | r3c6 | 2 | R |
| 2 | 6 | 6 | 6 | 2 | 4 | r4c2 | 10 | E |
| 10 | 6 | 3 | 3 | 2 | 4 | r2c2 | 7 | L |
| 7 | 3 | 1 | 1 | 4 | 1 | r3c3 | 5 | O |
| 5 | 1 | 3 | 3 | 2 | 1 | r3c2 | 9 | C |
| 9 | 3 | 2 | 2 | 6 | 3 | r1c1 | 3 | A |
| 3 | 2 | 4 | 4 | 5 | 3 | r2c4 | 8 | T |
| 8 | 4 | 5 | 5 | 1 | 3 | r6c4 | 4 | I |
| 4 | 5 | 2 | 2 | 6 | 1 | r5c3 | 6 | O |
| 6 | 2 | 4 | 4 | 5 | 3 | r5c6 | 1 | N |

The literal output is **RELOCATION**. The completed example reads LEAF. In its first row, source and receiver both have area 3, but the receiver area addresses region 3 of area 2, so the jump is 1. This refutes direct subtraction of receiver area. Negative differences still travel in the printed direction; the absolute value sets distance. Intermediate arrow cells do not stop a jump.

## The example bank

The example's bank SFTQMAXRELIK matches its completed diagram region by region: region 1 (3 cells) receives SFT, region 2 (4 cells) QMAX, region 3 (2 cells) RE, region 4 (3 cells) LIK, each in reading order. All twelve letters are distinct, so the completed example pins down both the region order (increasing number) and the in-region order (top to bottom, then left to right); no other region ordering or scan direction reproduces the printed letters.

## The sparse teaching table

The four rows under the Arrow and Jump headings show only the source arrow badge, an unlabelled silhouette of the lookup region, and the numeric absolute-difference equation. The receiver, the lookup region's number, the landing letter and the next badge are not printed in the table.

Recover the missing relationship by matching each oriented silhouette to the completed diagram. Read the arrow's arrival circle from its spatial location, find its enclosing region, and count that region's cells. In source order 1,4,3,2, the receivers are 4,3,2,1; their areas are 3,2,4,3. The silhouettes belong to regions 3,2,4,3 respectively. Thus the receiving area addresses a numbered region, whose area supplies the second operand. No identity of this lookup is printed in the teaching table.

The first row has equally sized source and receiving regions (both 3), yet a one-cell jump, so direct source/receiver subtraction fails. The next two rows have negative signed differences but follow their printed arrow directions, so distance is absolute. The last example arrow passes an intermediate arrow and a boundary. The complete LEAF readout includes the closing arrival.

`solver_lib/inference.py` checks ten declared elementary address readings. Exactly receiving-area survives all four observed shape/path pairs. This is evidence for the ordinary diagrammatic convention, not a claim that finitely many examples exclude every artificial interpolation. Full uniqueness is separately proved for all connected partitions and Hamiltonian cycles under the inferred convention.

**Answer: RELOCATION**
