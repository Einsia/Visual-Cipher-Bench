# The Wax Automaton — Walkthrough

1. On Calibration, the four Spare reeds tiles fill the four indexed Opening reeds chambers. The shaded 04 and 02 match the two known chambers; the missing contents are 03 and 01. Gray headers are fixed positions, while white entries are values. Fresh wax is independently `03 04 02 01`.

2. Follow the first expanded module. The upper round 03 reads reed chamber 03 and obtains 01. The upper square 03 independently reads that chamber's 01; its connector ends on wax header 01. Thus the sample 01 replaces the old 03 there. In the lower lane, round 02 obtains sample 03; square 04 obtains destination 02. The connector ends on wax header 02, where 03 replaces old 04. Squares contain source indices, not literal destination addresses; no wax content serves as a lookup source.

3. The separate Exchange below the impressions swaps reed chambers 01 and 02. This follows both reads and writes: the bank changes from `04 03 01 02` to `03 04 01 02`. The module's two return paths refer to these two resolved chambers, not to the two printed square numbers.

4. In the four-row trace, module 02 is unchecked and leaves both snapshots unchanged. Modules 01, 03 and 04 are engaged, matching the count of three. Module 03 gives wax `03 03 02 02`, demonstrating legal duplicates and replacement; module 04 overwrites positions 03 and 01, giving `04 03 01 02`. This reproduces the opening bank. The closing bank satisfies the separate partial circular clues. The arrow from Final wax leads to the four two-digit output groups.

5. On Performance, use exactly the same mechanism with twelve Spare reeds tiles and twenty modules. Follow their snake-shaped numbered path, selecting exactly ten. Read the closing circular bank by fixed gray indices: position 05 contains 01 and position 06 contains 12. The Final wax strip is equated to the repeated Opening reeds strip; the long wire ties that strip back to the full opening disc. Equality is slotwise, not equality of multisets.

6. Solve the opening permutation and selections jointly. A complete reverse route enumerates all terminal permutations satisfying the two clues, chooses earlier selected modules, and undoes only self-consistent indirect exchanges. Each last surviving wax impression binds an opening value through the closure. Reject duplicate identities and impossible remaining exchange distances, then check the untouched Fresh wax positions at the initial boundary. This is a changing-address search, not twenty independent assignments.

7. The unique opening bank is `06 03 02 12 11 10 09 01 08 04 07 05`; engage modules 1, 5, 6, 7, 8, 11, 13, 14, 17, 18. Replay all ten selected modules in increasing numbered order:

| Module | Samples | Resolved wax positions | Reeds after exchange | Wax after impression |
|---|---|---|---|---|
| 01 | 01 12 | 02 09 | 06 08 02 12 11 10 09 01 03 04 07 05 | 05 01 04 07 01 03 12 10 12 06 02 08 |
| 05 | 08 11 | 08 05 | 06 08 02 12 01 10 09 11 03 04 07 05 | 05 01 04 07 11 03 12 08 12 06 02 08 |
| 06 | 06 08 | 01 09 | 03 08 02 12 01 10 09 11 06 04 07 05 | 06 01 04 07 11 03 12 08 08 06 02 08 |
| 07 | 06 09 | 06 07 | 03 08 02 12 01 09 10 11 06 04 07 05 | 06 01 04 07 11 06 09 08 08 06 02 08 |
| 08 | 06 11 | 10 12 | 03 08 02 12 01 09 10 11 06 05 07 04 | 06 01 04 07 11 06 09 08 08 06 02 11 |
| 11 | 09 04 | 02 10 | 03 05 02 12 01 09 10 11 06 08 07 04 | 06 09 04 07 11 06 09 08 08 04 02 11 |
| 13 | 10 04 | 06 04 | 03 05 02 09 01 12 10 11 06 08 07 04 | 06 09 04 04 11 10 09 08 08 04 02 11 |
| 14 | 02 05 | 03 12 | 03 05 04 09 01 12 10 11 06 08 07 02 | 06 09 02 04 11 10 09 08 08 04 02 05 |
| 17 | 01 03 | 08 02 | 03 11 04 09 01 12 10 05 06 08 07 02 | 06 03 02 04 11 10 09 01 08 04 02 05 |
| 18 | 07 12 | 11 04 | 03 11 04 07 01 12 10 05 06 08 09 02 | 06 03 02 12 11 10 09 01 08 04 07 05 |

8. The closing bank is `03 11 04 07 01 12 10 05 06 08 09 02` and meets both visible givens. Final wax is `06 03 02 12 11 10 09 01 08 04 07 05`, exactly the opening bank. Read wax positions 01 through 12 and preserve both digits per position. Submit `060302121110090108040705`.

**Answer: 060302121110090108040705**
