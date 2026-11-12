# Lasting Impressions — Walkthrough

1. Start with the first page. Each of the five small groups has a 5×5 input grid, a string of diamonds and circles, a right-pointing arrow, and an output grid. Read the string from left to right and start again from the displayed input in each group. The top two groups have the same input, but diamond–circle and circle–diamond give different outputs: the cell in row 2, column 2 is black only on the left. The order of the operations therefore matters.

2. Follow the dark details inside the border columns. In the top-left group, the isolated detail at row 3, column 2 ends up at row 3, column 4, while the detail at row 4, column 4 has a counterpart at row 2, column 2. This suggests a half-turn for the combined movement, which is what a left/right reflection followed by a top/bottom reflection gives. Pure reflection does not explain the new black cells: compare the three lower groups, which share one input. Diamond–diamond–circle, circle–circle–diamond and circle–diamond–circle all fill both side columns and add a black centre cell, so repeating a symbol does not simply cancel it. The title suggests that an operation also leaves a lasting mark.

3. Test fixed reflections together with fixed black or white writes at destination cells. A later operation can hide an earlier mark, so a single completed group cannot reveal every write. Keep the same two operations throughout both pages. The observations support diamond as a left/right reflection and circle as a top/bottom reflection, with persistent changes to selected cells. A useful way to keep the alternatives straight is to give each destination cell a small table: what does this operation do when the arriving cell is white, and what does it do when it is black? Compare complete outputs, including white cells, with every group on the first page.

4. The bottom of the first page shows a single H-shaped grid with a downward arrow to H. It is not an operation example; it establishes how to read the outputs on page two: each missing grid should be a capital letter, written on its short answer line. These capital shapes provide further evidence about the same operations. The five completed groups do not pin down every write on their own, so when each missing output is considered separately, several of them can still be made into more than one capital letter.

5. Do not choose those letters independently. The top-left, top-right and second-row-left groups all use circle–diamond–circle. Their combined geometric action is a left/right reflection; their combined colour behaviour must also agree wherever the incoming bit agrees. For example, the top-right and second-row-left inputs both have a white cell at row 2, column 1. That cell feeds row 2, column 5 in both outputs. Choosing A for the top-right output and S for the second-row-left output would require this same white input to become both black and white. Thus a tempting reading such as MASSAGES fails the shared operation. Comparing all such shared-cell constraints across the eight targets and the five completed groups leaves M E / S S / A G / E S.

6. Check the result with one complete pair of operations. Number rows from top to bottom and columns from left to right, starting at 1. For a diamond, mirror the grid left to right, then make row 1, columns 1 and 5, row 3, columns 1 and 3 black, and make row 2, columns 2, 3 and 4 and row 4, column 3 white. For a circle, mirror top to bottom, then make all four corner cells black and make row 2, column 3 and row 4, column 3 white. Apply these in the printed order, restarting from each displayed input. This pair reproduces all five completed transformations and produces the following missing grids. Here `1` means black and `0` means white:

   | Position | Output rows | Letter |
   |---|---|---|
   | Top left | 10001 / 11011 / 10101 / 10001 / 10001 | M |
   | Top right | 11111 / 10000 / 11110 / 10000 / 11111 | E |
   | Second row left | 11111 / 10000 / 11111 / 00001 / 11111 | S |
   | Second row right | 11111 / 10000 / 11111 / 00001 / 11111 | S |
   | Third row left | 11111 / 10001 / 11111 / 10001 / 10001 | A |
   | Third row right | 11111 / 10000 / 10111 / 10001 / 11111 | G |
   | Bottom left | 11111 / 10000 / 11110 / 10000 / 11111 | E |
   | Bottom right | 11111 / 10000 / 11111 / 00001 / 11111 | S |

The hidden writes need not be uniquely determined in cells where later writes conceal them. Likewise, a longer middle bar still reads as E. What is fixed by the shared operations and recognizable capital outputs is the letter sequence. Read across each row, then down the page: **MESSAGES**.

**Answer: MESSAGES**
