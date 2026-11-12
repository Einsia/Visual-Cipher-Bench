# Front Desk — Walkthrough

1. On page 1, squares stay over the rack positions while circles are inside word cards. The inventories say ×1, so both the card names and the badges are used exactly once.

2. Follow the Step 2 example. ROPE currently carries 1, so its address comes from where ROPE is in After 1: slot 1. IRON currently carries 4, so look for IRON in After 4: slot 2. Exchange the current cards in slots 1 and 2. The Then row confirms that FELT and ROPE moved with their badges.

3. On page 2, the Then 2 / Swap badges query row gives ROPE=1 and IRON=4 again, but now the arrows go straight to square slots 1 and 4. Only their badges move: FELT receives 4 and IRON receives 3. The After 2 row confirms this. The square 4 exchanging with itself in Step 1 shows that coincident targets leave the state unchanged.

4. Page 3 supplies eight named pairs. Make nine racks, Initial and After 1 through After 8. Each pair imposes the same two-stage update. Some references point forward, so these are simultaneous constraints over the whole history; do not invent a default order for the initial cards or badges.

5. Read each observation panel the way the small panel at the bottom of page 2 is read. There, STEM's final badge 1 selects After 1, ROPE's final badge 2 is the separation, and the bracket runs from ROPE in slot 1 to STEM in slot 3: two slots apart, with the left-hand word on the left. On page 3, the word after "After" and its final badge select the completed rack to inspect, and the word after "Separation" and its final badge give the distance in slots. When the two words sit at the ends of a bracket, the left-hand word is on the left in that rack. For example, the top-left panel says that after the step numbered by DOORKNOB's final badge, TRINKETS is CUPBOARD's final badge slots right of PASSWORD. The two panels marked Either order stack their words instead: they fix only the distance, not which word is on the left. The panels give the equations without revealing any value.

6. Propagate the position constraints (six with a direction, two without) alongside the eight exchanges. A compact reproducible way is to enumerate final-badge values allowed by the same-time distance graphs, and solve each remaining coupled-history branch. This uses every condition on the pages; it does not assume a dictionary word. The uniqueness check excludes all alternative histories. The surviving initial rack is:

KEYBOARD(5), DOORWAYS(4), BATHROOM(6), TRINKETS(7), CUPBOARD(3), SUITCASE(1), PASSWORD(8), DOORKNOB(2)

The resulting completed racks are:

- After 1: TRINKETS(7), DOORWAYS(4), BATHROOM(6), KEYBOARD(2), CUPBOARD(3), SUITCASE(1), PASSWORD(8), DOORKNOB(5)
- After 2: TRINKETS(7), KEYBOARD(4), BATHROOM(6), DOORWAYS(2), CUPBOARD(3), SUITCASE(1), PASSWORD(8), DOORKNOB(5)
- After 3: SUITCASE(3), KEYBOARD(4), BATHROOM(6), DOORWAYS(2), CUPBOARD(1), TRINKETS(7), PASSWORD(8), DOORKNOB(5)
- After 4: CUPBOARD(5), KEYBOARD(4), BATHROOM(6), DOORWAYS(2), SUITCASE(3), TRINKETS(7), PASSWORD(8), DOORKNOB(1)
- After 5: DOORKNOB(7), KEYBOARD(4), BATHROOM(6), DOORWAYS(2), SUITCASE(3), TRINKETS(1), PASSWORD(8), CUPBOARD(5)
- After 6: BATHROOM(8), KEYBOARD(4), DOORKNOB(7), DOORWAYS(2), SUITCASE(3), TRINKETS(1), PASSWORD(6), CUPBOARD(5)
- After 7: PASSWORD(1), KEYBOARD(4), DOORKNOB(7), DOORWAYS(2), SUITCASE(3), TRINKETS(6), BATHROOM(8), CUPBOARD(5)
- After 8: PASSWORD(1), DOORKNOB(7), KEYBOARD(4), DOORWAYS(8), SUITCASE(3), TRINKETS(6), BATHROOM(2), CUPBOARD(5)

7. Check the eight panels against the resulting times and distances. The final badges give DOORKNOB 7, BATHROOM 2, CUPBOARD 5, PASSWORD 1 and DOORWAYS 8. Left column, top to bottom:

- After 7, TRINKETS is 5 slots right of PASSWORD.
- After 2, PASSWORD is 2 slots right of CUPBOARD.
- After 2, DOORKNOB is 5 slots right of BATHROOM.
- After 7, CUPBOARD is 2 slots right of TRINKETS.

Right column, top to bottom:

- After 2, BATHROOM and TRINKETS are 2 slots apart (either order; BATHROOM is in slot 3, TRINKETS in slot 1).
- After 2, DOORWAYS and CUPBOARD are 1 slot apart (either order; DOORWAYS is in slot 4, CUPBOARD in slot 5).
- After 2, PASSWORD is 5 slots right of KEYBOARD.
- After 8, CUPBOARD is 7 slots right of PASSWORD.

8. The Initial badges diagram on page 2 shows the extraction. Each line starts at a badge of the initial rack, by slot, and ends at a slot of the final rack; that badge says which letter to take from the word now in that slot. In the example, the badges 4, 3, 2, 1 of initial slots 1–4 run to final slots 2, 1, 4, 3, so STEM gives its 3rd letter, IRON its 4th, FELT its 1st and ROPE its 2nd: E, N, F, O. On page 3 the lines into final slots 1–8 start at initial slots 7, 8, 1, 2, 6, 4, 3, 5, whose initial badges are 8, 2, 5, 4, 1, 7, 6, 3. Read the final rack from left to right:

- PASSWORD[8] = D
- DOORKNOB[2] = O
- KEYBOARD[5] = O
- DOORWAYS[4] = R
- SUITCASE[1] = S
- TRINKETS[7] = T
- BATHROOM[6] = O
- CUPBOARD[3] = P

The eight final blanks read **DOORSTOP**.

**Answer: DOORSTOP**
