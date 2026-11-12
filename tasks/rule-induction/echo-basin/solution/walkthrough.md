# Echo Basin — Walkthrough

Read the circular controls as square lattices of sample positions. Each dial holds a 7 × 7 lattice; faint light-grey dots mark empty positions, and a black diamond or an open ring marks an occupied one. The outermost ring of lattice positions is always empty, so the active area is the inner 5 × 5. The small cycle in the header orders empty, diamond and ring. Treat them as 0, 1 and 2.

The three large vertical bays are consecutive calibration contacts. Their paired upper and lower diagrams show changes to both P and the named control. In particular, the lower A1 in bay 01 is repeated as the upper A1 in bay 03; the original A0 cannot be reused.

Subtract each upper P from its lower P around the cycle. The differences match a rotated version of the paired input A or B. Compare the rotation amounts to total counts of rings, diamonds or occupied positions in the two input objects. Only clockwise quarter-turns counted from rings in the incoming P agrees across these examples: P0, P1 and P2 hold 7, 12 and 5 rings, giving 3, 0 and 1 clockwise quarter-turns.

The returned named controls are not explained by another whole-dial rotation and a pointwise map. Try cyclic movements of individual rows and columns while requiring the same local input/output table to fit all three contacts. A consistent table only appears when the new P supplies the counts: rings move rows right; diamonds move columns down. Critically, the second counts come from the guide after its rows have moved. Counting on a frozen guide fails. The empty outer frame is not part of the wrap.

These are the shifts for the three printed contacts (listed for the five active rows top to bottom and the five active columns left to right). The second list is counted on the guide after the row movement.

| Contact | Clockwise turns | Row shifts right | Column shifts down |
|---|---|---|---|
| 01 | 3 | [2, 3, 2, 4, 1] | [1, 0, 1, 2, 2] |
| 02 | 0 | [2, 1, 1, 0, 1] | [0, 2, 2, 2, 1] |
| 03 | 1 | [0, 0, 0, 0, 0] | [5, 2, 2, 2, 1] |

Undo those movements on each displayed returned control. All nine combinations of incoming P state and aligned control state are present. All three contacts agree on this table (rows: incoming P state; columns: aligned control state; entry: unshifted return state):

| Old P / turned control | Empty | Diamond | Ring |
|---|---|---|---|
| Empty | Empty | Ring | Empty |
| Diamond | Empty | Diamond | Diamond |
| Ring | Ring | Ring | Diamond |

One compact description is to copy P and decrement it around the three-state cycle wherever the new P contains a diamond. Apply the row and then column movements to this local result.

Reproduce every output in all three calibration contacts, including both sides. The diamond-only F beneath P3 confirms which object supplies a letter.

For each small console on page 2, begin with its own P, A and B. Follow its printed A → B → A order. Keep A's returned state after the first contact and use that state at the third. The first return movement is essential: whole-grid rotations cannot substitute for it. The last returned A2 need not be calculated to read P3.

| Console | Incoming P ring counts | Final letter |
|---|---|---|
| 1 | [12, 14, 7] | S |
| 2 | [10, 12, 9] | I |
| 3 | [10, 11, 8] | D |
| 4 | [10, 6, 6] | E |
| 5 | [9, 8, 9] | W |
| 6 | [7, 6, 7] | A |
| 7 | [14, 6, 9] | Y |
| 8 | [7, 11, 7] | S |

The printed numbers order the eight final shapes: **SIDEWAYS**. None of these eight final shapes is printed on the page.

**Answer: SIDEWAYS**
