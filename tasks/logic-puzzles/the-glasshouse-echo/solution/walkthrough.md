# The Glasshouse Echo — Walkthrough

1. On the Nursery trial, grey top halves are fixed pot numbers and lower halves are contents. Four individual seed tags supply one of each identity. Two shaded seeds point to the already placed tags; the other two fill the remaining holes. The first-impressions tray is a separate given state.

2. Follow the left circular probe 04: it reads tag 01 from pot 04. Its long connector enters the content of an impression tray. The square probe 02 reads tag 04 from pot 02, and that connector enters the tray's grey header 04. Therefore the first payload is placed at the pot named by the looked-up square value. The right branch independently reads payload 03 and resolves pot 01. The crossed old impressions show replacement, not accumulation.

3. The separate Then diagram exchanges tags at resolved pots 04 and 01. It starts with 02 04 03 01 and ends with 01 04 03 02. This distinguishes exchanging the resolved pots from exchanging the printed square sources, and distinguishes reading before exchange from reading afterwards. No intermediate Value box or Copy/Swap-via column is supplied; the routing endpoints carry those roles.

4. Read the four graft cards across the trial shelf. Rounds 01, 03 and 04 are checked, satisfying Count=3. Round 02 is unchecked and both of its snapshots match round 01. The intermediate impression snapshots contain duplicates, so uniqueness cannot be imposed on the impressions during execution. Later cards overwrite old values. The final full-bed equality restores the first tags, and the output arrow formats the impressions as 02 04 03 01.

5. On Night cycle, use the same circuit grammar with twelve identities. There are no initially placed tags. Copy the separate first-impressions bed exactly, including its shuffled order. Each card has two vertical branches: circle contents become payloads, square contents become destinations. The opposing arrows below indicate the later exchange. Process any chosen cards in shelf order, respecting Count=10. The last-tags bed gives only pot 06 = 08 and pot 09 = 07. Its other values remain unknown.

6. The lower equation is between complete indexed beds. Require last impressions to equal first tags at every position, not just as a set. The long return line identifies the original unknown bed. Jointly search the initial permutation and the ten-card subset; each tentative choice determines a complete forward run. A complete reverse method enumerates terminal permutations, undoes consistent indirect exchanges, and binds initial entries only at their last surviving writes. Skip overwritten earlier values. Untouched pots retain their first impressions. All these conditions come from the picture.

7. Exhaustive search leaves first tags `09 01 10 03 02 05 04 07 12 11 08 06` and selected rounds 01, 04, 05, 06, 07, 11, 12, 14, 16, 18. Replaying those ten rounds gives:

| Round | Read values | Resolved pots | Tags after | Impressions after |
|---|---|---|---|---|
| 01 | 01 03 | 05 04 | 09 01 10 02 03 05 04 07 12 11 08 06 | 01 12 08 03 01 06 09 10 02 07 05 03 |
| 04 | 12 01 | 01 02 | 01 09 10 02 03 05 04 07 12 11 08 06 | 12 01 08 03 01 06 09 10 02 07 05 03 |
| 05 | 01 09 | 07 01 | 04 09 10 02 03 05 01 07 12 11 08 06 | 09 01 08 03 01 06 01 10 02 07 05 03 |
| 06 | 04 01 | 07 02 | 04 01 10 02 03 05 09 07 12 11 08 06 | 09 01 08 03 01 06 04 10 02 07 05 03 |
| 07 | 11 10 | 10 09 | 04 01 10 02 03 05 09 07 11 12 08 06 | 09 01 08 03 01 06 04 10 10 11 05 03 |
| 11 | 06 05 | 03 11 | 04 01 08 02 03 05 09 07 11 12 10 06 | 09 01 06 03 01 06 04 10 10 11 05 03 |
| 12 | 08 07 | 12 08 | 04 01 08 02 03 05 09 06 11 12 10 07 | 09 01 06 03 01 06 04 07 10 11 05 08 |
| 14 | 06 12 | 12 09 | 04 01 08 02 03 05 09 06 07 12 10 11 | 09 01 06 03 01 06 04 07 12 11 05 06 |
| 16 | 02 08 | 05 11 | 04 01 08 02 10 05 09 06 07 12 03 11 | 09 01 06 03 02 06 04 07 12 11 08 06 |
| 18 | 05 10 | 06 03 | 04 01 05 02 10 08 09 06 07 12 03 11 | 09 01 10 03 02 05 04 07 12 11 08 06 |

8. The last tags `04 01 05 02 10 08 09 06 07 12 03 11` have the two required entries. Last impressions `09 01 10 03 02 05 04 07 12 11 08 06` reproduce first tags exactly. Read the impressions by increasing grey pot index, using two digits per field. Submit `090110030205040712110806`. The selected round numbers and last tags are working, not the submitted object.

**Answer: 090110030205040712110806**
