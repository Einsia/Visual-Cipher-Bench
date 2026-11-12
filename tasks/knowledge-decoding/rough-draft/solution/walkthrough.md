# Rough Draft — Walkthrough

The speaker icon marks the left panel, whose edits work on sound; Aa marks the right panel, whose edits work on spelling. Each edit is a node on a line: an arrow leaving the node downward into a box removes that box's contents, and an arrow rising into the node from a box inserts it. When an edit both removes and inserts, the inserted part takes the removed part's place ("Replace in place"). The five edits are not connected to each other: every edit is used exactly once, each output becomes the input of another edit, and the chain must return to the word marked ?.

The worked example at the top, STONE → ONE, removes the contents of two adjacent empty letter cells. Only ST works, so two adjacent cells stand for one consecutive block of two letters, and on the Aa rows letters are written letters, not letter names. The H cell on the right is printed; every other letter cell is blank and must be deduced.

## Placing the picture cards

The three picture cards at the top must go into the four empty receivers in the sound panel. Every card is used, a card may be used more than once, and cards may not be turned or resized, so each card must fit inside the receiver it is placed in. The ray (fish) card is wide and short, the grain card is narrow and tall, and the ball-of-string card is smaller than both.

- The two tall, narrow receivers (the removal in the middle edit and the removal in the ? edit) are too narrow for the ray card: each holds the grain or the string.
- The two wide, short receivers (the insertion in the top edit and the insertion in the middle edit) are too short for the grain card: each holds the ray or the string.

Since there are four receivers and three cards, one card repeats. Size alone does not settle the assignment; the word chain does.

## The loop

The loop is WHITE WINE → WHY → WRY → RAY → Y → WHITE WINE.

1. The ? edit removes the ball of string, named TWINE. WHITE WINE /W AY T W AY N/ minus TWINE /T W AY N/ leaves /W AY/, spelled WHY. The deletion straddles the WHITE|WINE word boundary.
2. The upper Aa edit removes H and puts one letter in its place. From WHY, inserting R gives WRY.
3. In the middle sound edit, the narrow receiver holds the ear of grain, named RYE, and the wide receiver holds the ray fish, RAY. WRY sounds the same as RYE, /R AY/, and is replaced in place with RAY /R EY/.
4. The lower Aa edit removes a two-letter block: from RAY delete RA in spelling, giving Y.
5. The top sound edit inserts the ball of string again. The letter Y is pronounced /W AY/; adding TWINE /T W AY N/ gives /W AY T W AY N/, i.e. WHITE WINE, returning to the start.

So the string card is used twice and the grain and ray cards once each, every card fits its receiver, and the missing letters are R and RA. No other assignment of cards, order of edits or choice of missing letters closes the chain; reading every edit as spelling alone has no solution.

Answer: **WHITEWINE** (the starting word that goes in the question mark, with the space removed).

**Answer: WHITEWINE**
