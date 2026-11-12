# Parting Faces — Walkthrough

1. At the left of page 1, read each black mark by its orientation. The four corner marks give I/2, S/1, A/3 and O/3; the four triangular marks give C/2, N/1, T/1 and R/3. The letter is recorded and the circled number controls the count. The three worked columns on page 2 show I, A, N in time order.

2. In page 1's Exit/Stay strip, card 1 goes first, card 4 second, card 2 third and card 3 stays. The angles under these slots lead down to their starting poses. The initial rotation is demonstrated inside the second starting-pose slot on page 1: circled 4 and its 90° angle lead directly to a gray template/black result overlay in one fixed registered grid. The gray outline is template 4 in its catalog position; the gray dot and the black dot coincide at the grid point 3 right and 3 up from the registration cross, and the Pivot leader ends at that common point. Measured from the cross (x right, y up), the gray template has vertices (1,1), (1,5), (6,5), (4,-1) and the black result has vertices (-1,2), (1,5), (5,5), (5,0), i.e. the template turned 90° clockwise about its dot. It is not a rotation about the registration cross or a later departing card. Hence on page 3 the unknown departure order also assigns the initial turns: Exit slots 1–8 carry 0°, 90°, 180°, 270°, 0°, 90°, 180°, 270° and Stay carries 0°. The 3×3 catalog is a set of templates, not a known initial stack. The initial-layer convention is carried by a complete row of identity cells. Page 1 shows Bottom → [2][3][4][1] → Top feeding the checkpoint-0 overlap directly. Its order differs from Exit (1,4,2,3); it describes the actual opaque stack, while the separate ring is used only for counting. Page 3 uses the identical cell form with nine unknown identities and no connector from an Exit slot or the ring. Each template is used once; the layer permutation is jointly solved with the departure-dependent starting angles.

3. Page 2 establishes the selector. Each example column is labelled Exposed area, and the card that leaves is the one with the largest visible area, counting every visible piece and allowing for occlusion by higher cards. At checkpoint 0 card 1 is on top and leaves. At checkpoint 1 the top card 3 shows about 12.50 squares, but card 4 shows about 16.25 and is the one that leaves; card 2's two disconnected visible pieces (about 0.21 and 3.80) are added together. Neither topmost-card selection nor largest single exposed patch works, and the label rules out reading it as whole-card area.

4. Follow Remove and the surviving numbered ring. The first example counts 2→3 after card 1 leaves. The second counts 2→3→2 after card 4 leaves, skipping absent 1 and wrapping. The registered scenes in the lower half of page 2 show what the count does. Compare card 3 at checkpoint 0 with the first lower scene: the chosen survivor has turned 90° clockwise around the departed card's current dot and been raised to the top, giving the intermediate stack 2 → 4 → 3. The next scene (checkpoint 1) differs only in card 4: the immediately lower card has turned 90° anticlockwise around the top card's new dot. Card 2, drawn alone underneath both scenes in the same pose, shows that cards further down do not move. The last column has no lower card, so only the survivor turns.

5. The two overlapping rectangles at page 1's bottom retain only their two exclusive strips. Thus Changed footprint means symmetric difference of occupied unions, with shared coverage removed. The fixed crosses prevent sliding one silhouette to fit another. The question shows two unknown checkpoint indices (?→?). Infer them jointly with the execution by comparing all 36 pairs 0≤a<b≤8; the example's 0→2 establishes that the indices count completed full rounds.

6. Use the shared grids to trace the nine polygons and dots. Jointly try starting turns and layers, execute the established operations, and reject any hypothesis whose actual departure slot prescribes a different initial angle. After the eighth departure check the survivor's initial angle too. This simultaneous consistency is necessary; choosing angles after completing an arbitrary forward run would change that run's geometry.

7. One compatible starting order, bottom to top, is 1, 3, 6, 9, 2, 7, 5, 8, 4. Cards 1–9 start at 90°, 90°, 180°, 180°, 270°, 0°, 0°, 0°, 270°. The following table records the resulting readings and moving identities; all areas include occlusion by higher cards.

| Step | Exit | Exposed area | Letter | Count | Target | Underlayer | Pivot |
|---:|---:|---:|:---:|---:|---:|---:|---|
| 1 | 8 | 65.666667 | C | 2 | 1 | 4 | [4, -1] |
| 2 | 1 | 85.500000 | O | 3 | 4 | 5 | [3, -3] |
| 3 | 4 | 51.000000 | N | 1 | 5 | 7 | [2, 2] |
| 4 | 5 | 85.500000 | T | 1 | 6 | 7 | [2, 1] |
| 5 | 7 | 74.811111 | A | 3 | 3 | 6 | [2, 7] |
| 6 | 2 | 108.000000 | C | 2 | 6 | 3 | [2, 2] |
| 7 | 3 | 73.000000 | T | 1 | 6 | 9 | [-5, -14] |
| 8 | 9 | 62.000000 | S | 1 | 6 | — | [-4, -42] |

8. Only the checkpoint pair (1,5) is consistent with a valid full execution. Overlay the occupied shapes at those checkpoints and remove shared coverage. The resulting gray region matches the question at its registration cross. Checking all coupled assignments leaves one output; other compatible initial lower-layer orders do not change it. None of the gray pieces is a whole card in any orientation, so the region has to be compared as a whole against full executions; a word guess alone is insufficient.

9. Read the eight Exit letters left to right, exactly as the IAN example does, and leave card 6 in Stay unread: **CONTACTS**.

Note: the first-round intermediate stack is 2 → 4 → 3; only 4 changes in the second motion. The new dot of 3 supplies its pivot. The two registered scenes on page 2 and the isolated card 2 under them demonstrate this. Eight numbered Exit identity slots establish eight readings. The separate eight letter blanks at the bottom of page 3 are indexed by Exit 1–8; Stay has no reading or letter blank. The two identity rows are mechanism data.

**Answer: CONTACTS**
