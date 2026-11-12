# Core Memory — Walkthrough

The answer is **FVSZXEKY**.

Start on the calibration sheet. The dashed and solid marks denote the two readings of a sleeve. In the three-letter example, the middle sleeve moves farthest, the lower one next and the upper one least. The corresponding rank digits produce ORE. This gives decreasing displacement, not page position or lane order.

On the field record, follow the four supplied traces (A sleeves 1, 4, 5 and 8). The other four A centers have no supplied correspondence. Do not pair them by vertical order: jointly infer their destinations and letters from the two complete ink fields. All 24 remaining bijections have nonempty local glyph domains; only one covers the entire two-view image. The table below records the result of that inference, not eight given arrows. The rack is drawn sideways relative to its uppercase glyphs; mentally turning the diagram clockwise makes the glyphs upright. The sleeve overlay on the first sheet shows why a black stroke inside one sleeve may belong to its neighbor.

| Sleeve (bottom to top in A) | A height coordinate | B height coordinate | Upward travel | Glyph | Rank |
|---|---:|---:|---:|---|---:|
| 1 | 1394 | 714 | 680 | V | 2 |
| 2 | 1342 | 542 | 800 | F | 1 |
| 3 | 1306 | 966 | 340 | X | 5 |
| 4 | 1266 | 818 | 448 | Z | 4 |
| 5 | 1126 | 1010 | 116 | Y | 8 |
| 6 | 1090 | 610 | 480 | S | 3 |
| 7 | 1010 | 878 | 132 | K | 7 |
| 8 | 958 | 754 | 204 | E | 6 |

Now treat the scans as two masked unions. A possible letter must fit both of its translated locations without touching any exposed white. Gray regions carry no negative information. After the matching has been recovered, these are the remaining local glyph domains: [["B", "E", "F", "V"], ["F", "I", "J"], ["I", "L", "T", "X", "Y"], ["L", "Z"], ["I", "Y"], ["I", "S", "T", "Y"], ["E", "F", "I", "K", "L", "T"], ["E", "F", "L"]]. Choosing independently from those sets is insufficient: the chosen letters together must reproduce every exposed black region.

Testing that complete spatial consistency leaves VFXZYSKE, bottom to top in A. For example, changing the last E to F would leave 1,508 visible pixels of A unexplained, although B would look unchanged. Conversely, changing the second F to E would leave A unchanged but damage B. These complementary tests require both views and shared-stroke attribution.

Sort the travels [800, 680, 480, 448, 340, 204, 132, 116] in decreasing order. This selects [2, 1, 6, 4, 3, 8, 7, 5], and therefore **FVSZXEKY**. Enter one character per horizontal blank, from the top of the record column downward.


The four unsupplied routes belong to A sleeves 2, 3, 6 and 7. Their inferred paired B canonical centers are 1268, 844, 1200 and 932. The B5 dogleg is a continuous leader; displacement uses its endpoints, not routed length.

**Answer: FVSZXEKY**
