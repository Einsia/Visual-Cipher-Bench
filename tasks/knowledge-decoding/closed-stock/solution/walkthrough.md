# Closed Stock — Walkthrough

First look at the answer structure: seal numbers repeat across the cards, but the SEAL REGISTER has only one line per number, so the same number must share one entry. RETURN has as many empty circles as there are numbers, and the arrows run along the three rows and come back from the outside to 01; the requirement that the chain close must be inferred from this visible return line. The top and bottom use the same arrow notation, hinting that the same kind of link is used throughout. The relation to try is that the English name of a pictured object combines with a missing word to form a familiar word; this hypothesis must still be checked against every crossing link.

1. **Guess from several lines at once, not from one picture.** On page I, 03 sits before the horn, and on page II, 03 sits before the box as well. SHOE gives SHOEHORN and SHOEBOX; but POST also gives POSTHORN and POSTBOX. This shows that two local lines alone cannot guarantee a solution.

2. **Look for the blank with the most crossings.** 10 links at once to the insect, to 04 (which pairs with fish), to the axe, and to 08; the horn's name also links to 10. Trying HORN and STONE gives HORNSTONE, STONEFLY, STONE AXE, STONEFISH and STONEWARE. So 10=STONE, 04=FISH and 08=WARE are well worth keeping.

3. **Confirm names using the other page.** The metal can→08→01 on page II can now be read as TINWARE, WAREHOUSE. Calling the can a CAN at first glance is not misidentifying the object, but you must not force every word link to use the first synonym that comes to mind. 08=WARE is also supported by STONEWARE on page I. 01=HOUSE in turn supports HOUSEFLY, HOUSECOAT and WHEELHOUSE.

4. **Keep propagating across pages.** 12→01 gives BOATHOUSE and 12→hook gives BOAT HOOK, so 12=BOAT. 01→11 and 11→12 give HOUSECAT, CATBOAT, so 11=CAT. 11→13 and 13→coat give CATTAIL, TAILCOAT, so 13=TAIL. 14→box and 14→13 can be HORSEBOX, HORSETAIL, so 14=HORSE. Do not mistake TAIL's position in the picture for the end of an arrow; arrows can point either left or right.

5. **Treat the pictures at the ends as words with several names too.** The ribbon bow can be called BOW. BOW→09→15, plus 15→bag and 14→15, can be BOWSTRING, STRING BEAN, BEANBAG, HORSEBEAN. So 09=STRING and 15=BEAN. 06→15 and 06→axe supply POLE BEAN and POLEAXE, giving 06=POLE.

6. **Leave the unsettled entries open for now.** 02 comes before WHEEL and, together with 14, links to 05; MILLWHEEL / MILLRACE / HORSERACE fit well, but WATERWHEEL is also a real word. 07 has only one direct picture clue, "07→bag", and AIRBAG, MAILBAG, WORKBAG and WINDBAG are all worth considering. The competition between POST and SHOE for 03 should also be left to the overall picture to decide.

7. **The final RETURN is an extra constraint.** It is not a matter of following arrows already drawn on the cards. Using the same word-joining relation, the 15 numbered words must be rearranged into a new directed closed loop. Once HOUSEBOAT, BOATRACE, RACEHORSE, HORSESHOE, SHOESTRING, STRING BEAN, BEANPOLE, POLECAT, CATFISH, FISHTAIL are chained together, TAILWIND, WINDMILL, MILLSTONE, STONEWARE, WAREHOUSE close the loop exactly. The other local guesses cannot achieve full coverage.

8. **Output the numbers.** Starting at 01, fill the 15 circles following the arrows at the bottom. Each number is used only once, and 01 is not written again on returning to it. The result is:

```
01 12 05 14 03 09 15 06 11 04 13 07 02 10 08
```

With the spaces removed, the answer is `011205140309150611041307021008`.

The less common HORNSTONE, HORSEBEAN, MILLRACE and TAILRACE are not something the reader is expected to guess independently first; they are cross-confirmed by several more familiar combinations.

**Answer: 011205140309150611041307021008**
