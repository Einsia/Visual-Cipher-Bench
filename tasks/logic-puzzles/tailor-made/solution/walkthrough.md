# Tailor Made — Walkthrough

Start with the example below the heading. Its A tape is covered by A2 then A1, and its B tape by B1 then B2. The name sets point to those brackets: all named pieces occur once, are nonempty, and cover each whole tape. No lengths are printed; count the grey cell divisions inside each thick cut. A2 has 3 cells and A1 has 1; B1 has 2 and B2 has 1. A1 and B2 both have length 1, so lengths need not be different. The names are not a left-to-right numerical order.

The labels below each tape sit at the right edges of cells. A piece uses the label at its own rightmost boundary: in the example, A2 ends at the third cell's B2 label, while A1 ends at the fourth cell's double-framed B1 label. On the B tape, B1 ends at the single-framed A1 label and B2 at A2. In the lower question the thin grey divisions mark individual cells; the thick internal cuts have not yet been supplied.

Next compare the two sides of the Areas line. The numbers inside a piece add to its initial sum: A1 = 3, A2 = 2 + 3 + 3 = 8, B1 = 1 + 1 = 2, B2 = 3, exactly the first row of the Sums table. The equation A1 + B1 is drawn as two rectangles. The first is as wide as A1 and as tall as the single-framed bar, which is A1's own length bracket, reached from the single-framed A1 label at B1's right end. The second is as wide as B1 and as tall as the double-framed bar, which is B1's length bracket, reached from the double-framed B1 label at A1's right end. So the current sums 3 and 2 satisfy 3 + 2 = 1×1 + 2×2. Each piece's own length multiplies the length named by the other piece's endpoint. A sum of lengths or a perimeter would not give 5.

Now follow the crossed arrows under Sums. C exchanges A1 and B1; the other columns stay in place, so the second row is 2, 8, 3, 3. A tests A1—B2: its threshold is 1×3 + 1×2 = 5. A is illegal in the original state (3 + 3 = 6 ≠ 5), but legal after C (2 + 3 = 5); exchanging gives 3, 8, 3, 2. T then uses the newly updated totals: A2 + B2 = 8 + 2 = 10 = 3×3 + 1×1, and the last row is 3, 2, 3, 8. The inventory on the left maps to the three execution cards exactly once, and their letters give C→A→T. Apply the same coverage, single-use and chronological conventions to the lower question.

In the lower question each lettered card is a box on a line joining two named nodes, so trace each line to read its pair. Where two lines cross without a box they simply continue straight, just as the crossed exchange arrows do. This gives Q A5—B2, M A1—B2, V A1—B3, K A1—B1, X A3—B1, J A3—B2, Z A3—B3, B A3—B4, F A2—B4, W A2—B3, Y A2—B2, P A2—B1, D A2—B5, G A4—B5 and C A5—B5.

The lower two strips each have 14 cells and five names. Try full-cover partitions and place the names on them; for each candidate record its lengths, digit sums and right-end labels. For any selected card, test its equality on current sums, exchange the sums if it works, and continue with unused cards. An isolated successful equality is insufficient: a choice must extend through every card. There are 13 possible internal boundaries on each 14-cell strip. Choosing four boundaries makes five nonempty contiguous pieces; assigning the five names gives C(13, 4) × 5! = 85,800 configurations per strip. For each pair of configurations, keep every currently legal unused card as a possible next step. Reject a branch only when it cannot finish all 15 cards. This exhaustive procedure leaves one pair of partitions and one complete history. The surviving partition is:

| Segment | Cells from left | Length | Initial sum | Right-end target |
|---|---:|---:|---:|---|
| A4 | 1–3 | 3 | 17 | B3 |
| A2 | 4–5 | 2 | 5 | B2 |
| A3 | 6–7 | 2 | 1 | B1 |
| A1 | 8–11 | 4 | 1 | B1 |
| A5 | 12–14 | 3 | 11 | B5 |
| B1 | 1–2 | 2 | 5 | A3 |
| B4 | 3–6 | 4 | 5 | A1 |
| B3 | 7–9 | 3 | 7 | A5 |
| B5 | 10–12 | 3 | 11 | A5 |
| B2 | 13–14 | 2 | 1 | A3 |

At these cuts, both A2—B3 and A5—B2 initially satisfy an equality. The A2—B3 start cannot complete the whole inventory. Across both starts there are 8,368 legal thirteen-card prefixes: 7,059 start with A2—B3 (W), and 1,309 start with A5—B2 (Q). Only one of these prefixes extends to fourteen cards and then all fifteen. The comparisons near the end therefore check earlier exchange choices; taking any available card greedily is unsafe.

Use the surviving order shown below. Each row's equation is evaluated before swapping its two sums; carry the updated totals to the next row.

| Step | Letter | Pair | Equality before exchanging |
|---:|:---:|---|---|
| 1 | Q | A5—B2 | 11 + 1 = 3 × 2 + 2 × 3 = 12 |
| 2 | M | A1—B2 | 1 + 11 = 4 × 2 + 2 × 2 = 12 |
| 3 | V | A1—B3 | 11 + 7 = 4 × 3 + 3 × 2 = 18 |
| 4 | K | A1—B1 | 7 + 5 = 4 × 2 + 2 × 2 = 12 |
| 5 | X | A3—B1 | 1 + 7 = 2 × 2 + 2 × 2 = 8 |
| 6 | J | A3—B2 | 7 + 1 = 2 × 2 + 2 × 2 = 8 |
| 7 | Z | A3—B3 | 1 + 11 = 2 × 3 + 3 × 2 = 12 |
| 8 | B | A3—B4 | 11 + 5 = 2 × 4 + 4 × 2 = 16 |
| 9 | F | A2—B4 | 5 + 11 = 2 × 4 + 4 × 2 = 16 |
| 10 | W | A2—B3 | 11 + 1 = 2 × 3 + 3 × 2 = 12 |
| 11 | Y | A2—B2 | 1 + 7 = 2 × 2 + 2 × 2 = 8 |
| 12 | P | A2—B1 | 7 + 1 = 2 × 2 + 2 × 2 = 8 |
| 13 | D | A2—B5 | 1 + 11 = 2 × 3 + 3 × 2 = 12 |
| 14 | G | A4—B5 | 17 + 1 = 3 × 3 + 3 × 3 = 18 |
| 15 | C | A5—B5 | 1 + 17 = 3 × 3 + 3 × 3 = 18 |

Finally copy the letters of those cards into the bottom arrow-linked spaces, left to right. They form the finite key **QMVKXJZBFWYPDGC**. The complete set of valid equations confirms this 15-letter code.

**Answer: QMVKXJZBFWYPDGC**
