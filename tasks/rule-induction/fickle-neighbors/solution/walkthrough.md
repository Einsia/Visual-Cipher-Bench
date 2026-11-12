# Fickle Neighbors — Walkthrough

Look at the framed cards rather than just the letters: each arrow remains part of its card, and a card may carry no letter. The circle indicates a square independently of the cards. The two before/after pairs use the same visual language. Coordinates below are (row, column), counted from 1 at the top-left of each board.

Start by comparing the top row of example 1. Before, it holds a blank north card, P, a blank east card and U; after, it holds a blank west card, grey U, a blank south card and grey P. The cards have moved two places along the row, and the circle moves from U at (1,4) to the empty square at (2,3), in the next row down. In both completed boards, the grey letters spell the word printed underneath. This suggests repeated arrow-guided visits, row transport, and extraction from the final grey cards. The arrow-only card at (2,4) in example 1 changes direction without being visited, so updating only the departure card cannot explain the observations. The letterless cards have no names, so follow them by position, arrow and shade.

The operation that reproduces both complete examples works as follows. The source card's current arrow is saved before any operation. Move the visitor one adjacent square in that direction, flip the departure card's shade, and cycle the whole source row right for an old-white card or left for an old-grey card. Keep the visitor at the destination coordinate. Inspect the card newly occupying the source coordinate: rotate every arrow in that source column by the same angle that makes this controller point along the saved departure direction. Then inspect the visitor cell: blank ends the episode; card continues. Final grey letters are read in an order the examples must fix. An arrow-only framed card is still a card; only a cell without a card frame is empty. No intended execution ever lacks a controller or crosses the boundary.

UP starts on U at (1,4). U points west. After row 1 shifts right, the blank east card is at the source, requiring a 180° turn in column 4. The arrow-only card below changes south→north, demonstrating a shared column operation even though it is unvisited. The visitor now reaches P at (1,3), whose south arrow was not in column 4. P departs south and shifts row 1 right. The blank north card, which started at (1,1), now occupies its source coordinate, requiring another 180° turn, this time in column 3; it ends pointing south. The circle is on an empty cell in row 2. Grey U and P read UP.

ON starts on the circled blank card at (2,2); call it the circled card. It departs north; after row 2 shifts right, incoming O points west, so turn column 2 clockwise 90° to align it north. N at (1,2) turns east→south, and the visitor follows that new south direction. N's departure and row shift bring in the arrow-only west card, so turn column 2 counterclockwise 90° to align it south. The visitor now departs O west; the blank card that started at (2,3) has arrived at (2,2) pointing south, and requires clockwise 90° in column 2. Next the visitor is on the grey circled card at (2,1). It departs north, flips back to white and shifts row 2 left. The blank card from (2,3) is now at (2,1) pointing west, and requires a clockwise 90° turn in column 1. The visitor is then on a blank at (1,1). Only O and N are grey. Their final reading gives ON.

Example 2 is especially useful: the visitor returns to the circled card, yet it is white at the end. Permanent marking therefore fails; its shade must flip back. Its return also distinguishes always shifting right from shifting left when leaving grey. The arrow-only witnesses and N show that the shared column turn affects cards other than the one just left. The two examples use different grid widths, and the same one-square move and row cycle explain both. No boundary crossing is needed.

Example 2 also constrains the reading order. In its final board grey N is at (1,3) and grey O is at (2,2), below and to the left of N. Reading rows from top to bottom would give NO, so that order is ruled out. The ordinary orders that give ON here and UP in example 1 are rows read from the bottom up, and columns read from left to right (top-down or bottom-up within each column). The lower board will supply word confirmation.

Now apply the recovered operation to the lower board. Keep the saved departure direction separate from arrow changes later in the round; otherwise the same-column controller can incorrectly change the move already chosen. The table records each current direction, incoming controller and shared turn:

| Round | Source | Card | Saved direction | Flip / row shift | Incoming arrow | Clockwise turn | Column | Visitor destination |
|---|---|---|---|---|---|---|---|---|
| 1 | (2,2) | A | S | white→grey / right | E | 90° | 2 | (3,2) |
| 2 | (3,2) | V | W | white→grey / right | S | 90° | 2 | (3,1) |
| 3 | (3,1) | S | N | white→grey / right | N | 0° | 1 | (2,1) |
| 4 | (2,1) | I | E | white→grey / right | E | 0° | 1 | (2,2) |
| 5 | (2,2) | I | E | grey→white / left | W | 180° | 2 | (2,3) |
| 6 | (2,3) | A | S | grey→white / left | E | 90° | 3 | (3,3) |
| 7 | (3,3) | N | N | white→grey / right | S | 180° | 3 | (2,3) |
| 8 | (2,3) | O | N | white→grey / right | S | 180° | 3 | (1,3) |
| 9 | (1,3) | C | W | white→grey / right | W | 0° | 3 | (1,2) |
| 10 | (1,2) | E | S | white→grey / right | E | 90° | 2 | (2,2) |
| 11 | (2,2) | R | S | white→grey / right | E | 90° | 2 | (3,2) |
| 12 | (3,2) | T | S | white→grey / right | W | 270° | 2 | (4,2) |

After round 12, the visitor is at the empty square in row 4, column 2, so stop. This location is obtained by carrying out the moves; the lower board shows only the initial state. The final grey letters are: (1,1) C; (1,3) E; (2,1) O; (2,3) R; (3,1) N; (3,2) V; (3,3) T; (3,4) S.

Read them in the orders the examples allow. Columns left to right, each top to bottom: column 1 gives CON, column 2 gives V, column 3 gives ERT, column 4 gives S, so CONVERTS. Columns read bottom to top give NOCVTRES, and rows read from the bottom up give NVTSORCE. Only CONVERTS is an ordinary English word, and its meaning also fits the changing neighbors. (Rows read from the top would give CEORNVTS, but example 2 has already excluded that order.) Submit **CONVERTS**.

The boxed question mark identifies the lower board as the new instance; it does not specify an answer length. UP and ON appear directly below their final boards. The arrow-only witness in example 1 changes S→N; the west card in example 2 is W→W overall because its intermediate turns cancel. Both witnesses remain white and unvisited.

**Answer: CONVERTS**
