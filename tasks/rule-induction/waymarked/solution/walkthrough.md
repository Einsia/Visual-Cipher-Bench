# Waymarked — Walkthrough

Positions are given as rN cM (row N from the top, column M from the left). "Chevrons" are the little V marks on an
arrow's tail.

## Step 1 — What the page asks
**Where:** the three small numbered boards at the top and the large lettered board.
**What it gives:** on the small boards every signpost is either circled (kept) or struck through with a grey line
(not trusted). The large board has no marks; instead each signpost carries a letter. So the task is to judge the
large board's signposts the same way and read the answer from the ones that would be kept.
**Needs:** nothing.

## Step 2 — The obvious reading does not work
**Where:** board 1, column 2. From top to bottom it holds: r2c2 down arrow with one chevron (circled), r3c2 down
arrow with one chevron (struck), r4c2 up arrow with one chevron (circled).
**What it gives:** suppose you follow each arrow exactly as drawn and move as many cells as it has chevrons. Then r3c2
and r4c2 point at each other and would make a loop, and r2c2 would only lead into it. The page says the opposite for
the top two: r2c2 is kept and r3c2 is struck. The same failure appears on boards 2 and 3 (try board 2's column 6 or
board 3's rectangles). So an arrow's meaning is not fixed by the arrow alone.
**Needs:** step 1.

## Step 3 — Arrows are read like road signs, relative to the way you are walking
**Where:** board 1 again.
**What it gives:** start at r2c2. Read it as drawn: go down 1 to r3c2. You are now walking down. If r3c2's "down" means
"turn back", you go up 1 and arrive at r2c2 again, the post you started from. That explains why r2c2 is circled.
Start at r4c2: go up 1 to r3c2, now walking up; "down" means turn back, so you return to r4c2 (circled). Start at r3c2
itself: you read it as drawn (down 1) and reach r4c2 walking down. On a road sign an up arrow means "straight on", so
you keep walking down to r5c2, an empty cell. The walk is over and you never came back, so r3c2 is struck.
**Rule so far:** the starting post is read as drawn (you face up the page). Every later post is read relative to your
walking direction: up = straight on, down = turn back. The chevrons are the number of cells.
**Needs:** step 2.

## Step 4 — Confirm "up = straight on" with board 2
**Where:** board 2, column 6: r2c6 down 1 (circled), r3c6 up 3 (struck), r4c6 left 1 (struck), r5c6 up 3 (circled),
r6c6 down 1 (struck).
**What it gives:**
- From r2c6: go down 1 to r3c6, walking down. Up there means straight on, so go down 3 to r6c6, jumping over r4c6 and
  r5c6.
- At r6c6 (walking down) "down" means turn back: up 1 to r5c6. Walking up, its "up" means straight on: up 3, which
  lands on r2c6 again, so r2c6 is circled.
- From r5c6 the same loop is travelled from a different point, so r5c6 is also circled.
- From r3c6 or r6c6 you start by reading the arrow as drawn and fall off the board, so both are struck although they
  lie on that loop.

This rules out ideas such as "the post you land on turns a quarter or a half turn". It also shows that a jump goes
exactly n cells, over anything in between.
**Needs:** step 3.

## Step 5 — Left and right are turns: board 3
**Where:** board 3. Row 3 holds r3c1 left 2, r3c2 left 1 (circled), r3c5 right 1 (circled) and r3c6 right 3. Row 5
holds r5c1 left 1 and r5c2 left 2. Row 6 holds r6c3 right 2, r6c5 right 3 and r6c6 right 1.
**What it gives:**
- From r3c2: left 1 to r3c1, walking left. "Left" there means turn left, so walking left you now go down 2 to r5c1.
- Walking down, "left" means turn left again: right 1 to r5c2. Walking right, "left" means turn left: up 2 to r3c2,
  back at the start, so r3c2 is circled.
- From r3c5 the right arrows turn right each time: r3c6 -> down 3 to r6c6 -> left 1 to r6c5 -> up 3 to r3c5, so r3c5
  is circled.
- The other corners start as drawn and leave the board (struck). r6c3 goes right 2 to r6c5, turns right (down) and
  leaves the board (struck): reaching a loop is not enough.

If left and right were swapped (a mirror reading), boards 1 and 2 would still fit, but neither rectangle would
close. So only board 3 settles which way left and right turn.
**Needs:** step 4.

## Step 6 — The complete rule
A post is trusted (circled) exactly when a walk that starts on it comes back to it:
- start on the post facing up the page, so the first arrow is read as drawn;
- at every later post, up = straight on, right = turn right, down = turn back, left = turn left;
- move exactly as many cells as the post has chevrons;
- the walk ends if it lands on an empty cell or leaves the board.

It does not matter which way you are facing when you come back. Board 1's r4c2 comes back walking down, yet it is
circled. All 27 marks on the three boards agree with this rule.
**Needs:** steps 3-5.

## Step 7 — Walk every post on the large board
**Where:** the large board.
**What it gives:** each walk starts on its own post facing up. Two walks come back:
- From **P** r4c6 (up 3): up to A r1c6, walking up; its left arrow means turn left, so go left 3 to P r1c3. Walking
  left, its left arrow means turn left again (down 2) to E r3c3. Walking down, E's up arrow means straight on: down 1
  to R r4c3. Walking down, R's left arrow means turn left, which is to the east: right 3, which lands on P r4c6 again.
  Kept.
- From **C** r3c2 (down 3): down to H r6c2. Walking down, H's right arrow means turn right, which is to the west: left
  1 to A r6c1. Walking left, A's right arrow means turn right (north): up 3 to S r3c1. Walking up, S's right arrow
  means right: right 3 to E r3c4. Walking right, E's down arrow means turn back: left 2, which lands on C r3c2 again.
  Kept.
- Every other walk ends on an empty cell or off the board. For example, W r5c4 goes right 2 to U r5c6, turns left
  (up) to P r4c6 and follows the P walk all the way round. But it reaches P r4c6 walking right, so P's up arrow now
  means straight on, and the walk leaves the board. A r1c6, S r3c1 and B r4c4 also run into these walks without
  coming back to where they started.
**Needs:** step 6.

## Step 8 — Read the answer
**Where:** the two kept posts.
**What it gives:** read each kept post's walk in the order you travel it, starting at the kept post and stopping
before you would read it a second time. P r4c6, A r1c6, P r1c3, E r3c3, R r4c3 spells PAPER. C r3c2, H r6c2, A r6c1,
S r3c1, E r3c4 spells CHASE. Two kept posts give two words, and each walk visits five posts, so the answer is two
five-letter words; they make a phrase only in one order.

**PAPER CHASE** is a game of following a laid trail, which fits a page of waymarked paths.

_Notes on the page: the rings are mid-grey circles around the whole sign, and the strikes are light-grey diagonals
from lower left to upper right across the arrowhead. On the large board row 2, row 7 and column 7 are empty._

**Answer: PAPERCHASE**
