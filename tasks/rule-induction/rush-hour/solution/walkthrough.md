# Rush Hour — Walkthrough

1. Read the three example rows as before/after states. A letter identifies a node even when the page position changes. The solid triangle and open square attach to nodes. Repeated diamonds indicate repeated use of the same unknown operation: two applications in rows 1 and 2, three in row 3. There is no displayed single application to inspect directly.

2. Use the strings below the outputs to determine the requested readout separately from the transformation. EDGACBF begins at the final triangle E and follows its arrows. DFEG follows the triangle's four-node loop but excludes the untouched ABC loop. EHGF excludes the other four-node loop ADCB. Thus the output is the final triangle loop, read once in arrow direction, including its starting letter.

3. Compare changes in adjacency and direction rather than page position. Test local reconnection at the two marks, reversal of the newly selected loop, and movement of the marks. Since only composite endpoints are shown, every proposed movement also changes the next reconnection. Keep a proposal only if its entire hidden history reaches the visible graph and both marker endpoints.

4. In the top row, the candidate outgoing-successor swap plus new-triangle-cycle reversal gives hidden cycles AG and BCDEF. Moving by the opposite saved input size 7 puts the triangle at G and the square at C. The next marked-cycle sizes are now 2 and 5; moving by 5 and 2 after the next structural change gives the visible final cycle ACBFEDG, triangle E, square F. The printed string is EDGACBF. Reusing seven or making a fixed one-step move does not supply this full observed history.

5. In the middle row both marks start in DEFG; ABC has neither mark. The same actions produce DGF and a singleton E alongside unchanged ABC. With saved sizes 4 and 4, the marks land on G and E. The next sizes are 3 and 1, so movement must now use 1 and 3. The visible result is ABC plus DFEG, triangle D, square F. The whole ABC loop is visibly unused by the readout, so reading every node is ruled out.

6. Use the third row to test remaining timing and identity choices. Starting ABCDEFGH with triangle A and square E, the hidden states are AHGF + BCDE (marks A/E), then AFGHEDCB (marks E/A), then ADCB + EHGF (marks E/A). This matches the printed output and EHGF. Swapping the identities of the two moving marks after each operation can imitate the even-power observations but fails this odd-power row. Moving before reversal with component-count/self-size distances also fails this row. Within these local reconnection, reversal, timing and movement alternatives, the three rows select saving opposite input-loop sizes, then swapping outgoing successors, then reversing the new triangle loop, then moving on the new arrows.

7. Apply that same operation to the bottom graph. Read the input from its marks: triangle M in MHLBGJF, square N in NDKC. The component sizes and marker destinations after each diamond are:

| Diamond | Saved triangle/square cycle sizes | New triangle/square |
|---|---|---|
| 1 | 7 / 4 | B / G |
| 2 | 11 / 11 | B / L |
| 3 | 1 / 10 | H / G |
| 4 | 11 / 11 | K / L |

Each row uses the graph created by the previous row, including the isolated B loop after the second operation. The derived directed loops after the four applications are, respectively: (BLHNCKDMFJG); (B) and (CKDMFJGLHN); (BLGJFMDKCNH); then (BLG) and (CKDMFJHN). Parentheses indicate following the arrows back to the starting node. These intermediate graphs are deductions from the visible input, not extra printed clues.

8. At the end, start at triangle K and follow K→D→M→F→J→H→N→C, stopping before repeating K. The remaining BLG loop is excluded, just as unmarked loops were excluded in the examples. The eight letters fill the eight strokes: **KDMFJHNC**.

These steps describe a hypothesis-and-check induction, not a claim that one example logically specifies an arbitrary function. No hidden intermediate state is assumed as a printed fact.

**Answer: KDMFJHNC**
