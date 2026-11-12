# Notebook Society — Walkthrough

1. Read the three columns in the upper block. Vertical links under Pairs associate A with B, C with D and E with F. The first Queue cell is 4,7; the fourth and seventh Record cells are grey, and their letters E and F are boxed in Pairs. The middle and lower blocks repeat the same selection convention. The pointer is at the left edge of the Queue, and the output rows have empty queues: each arrow represents a whole run.

2. Compare the two completed runs before using the lower input. Both start with AB/CD/EF and ACEEBCFB. Their queues contain the same four requests in reverse orders. The upper result has the original matching but Record ACECEBFB; the middle result has matching AE/BF/CD and Record ACAFBCEB. This rejects an order-independent substitution or four independent edits. Returning to the original matching in one run does not mean the matching stayed fixed during it.

3. The boxed names show which characters participate; the links supply their partners, and the two numbered positions delimit a span in the Record. Test the same operation on every request in both examples. Natural possibilities to compare include exchanging selected names or their partners, reversing or rotating the span, and leaving pending addresses fixed or carrying them with the span. Recompute the entire run for each hypothesis: an unprinted intermediate state is not an extra clue. The composition that fits both complete observations exchanges the selected names in the matching; reverses the inclusive Record interval; and exchanges the two old partners inside that interval. The reversal also carries every pending address in that interval to its reflected position. The labels above Record remain fixed. These rules are a joint hypothesis verified against BOTH printed endpoints, not something visible in any isolated intermediate picture.

4. Check the hypothesis and its near alternatives on the upper and middle blocks. The first run's Records become ACEECBFB, ACEBCEFB, ACECBEFB, ACECEBFB. Its matchings become AB/CD/EF, AE/BF/CD, AE/BF/CD, AB/CD/EF. The reversed run's Records become ACBEECFB, ACBEFCEB, ACFABCEB, ACAFBCEB, ending AE/BF/CD. This matches every printed output. Keeping Queue addresses fixed instead gives ACFBECCB and ACBEEFCB; reflecting only interval endpoints gives the wrong upper Record ACEECBFB. Freezing the matching fails the middle block. Neither completed run by itself settles all these choices. Compare both final Records and both final sets of pairs, not just one agreeing row. The joint fit fixes the prediction for the bottom input; it does not establish a rule for every possible future input.

5. Now start fresh at the bottom separator. Read the pairs AN, DI, ES, RT; Record RRETIETA; and Queue 5,6; 1,2; 1,6; 7,8; 1,4; 1,7. Carry matching, Record and pending addresses forward together:

| Step | Current request | Selected / old partners | Pairs after | Record after | Remaining Queue |
|---|---|---|---|---|---|
| 1 | 5,6 | IE / DS | AN / DE / IS / RT | RRETEITA | 1,2; 1,5; 7,8; 1,4; 1,7 |
| 2 | 1,2 | RR / TT | AN / DE / IS / RT | RRETEITA | 2,5; 7,8; 2,4; 2,7 |
| 3 | 2,5 | RE / TD | AN / DR / ET / IS | REDERITA | 7,8; 5,3; 5,7 |
| 4 | 7,8 | TA / EN | AE / DR / IS / NT | REDERIAT | 5,3; 5,8 |
| 5 | 3,5 | DR / RD | AE / DR / IS / NT | REDERIAT | 3,8 |
| 6 | 3,8 | DT / RN | AE / DN / IS / RT | RETAINED | empty |

6. Do not drop the apparently idle requests. After the second request the Record remains RRETEITA, but future 1,5 becomes 2,5. After the fifth request the Record remains REDERIAT, but pending 5,8 becomes 3,8. Both effects matter to the final result. Only after that last interval is processed is the Queue empty.

7. The eight question-mark cells at Final record ask for the entire Record in the same left-to-right order as the examples. They read **RETAINED**. A plausible word sharing seven letters would not be enough: the final cell must also be calculated from the joint rule fit. No extra indexing, pair reading or thematic synonym is needed.

**Answer: RETAINED**
