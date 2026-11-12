# Some Assembly Required — Walkthrough

Coordinates are pixel positions on the delivered 1700 x 2193 page. Title "Some Assembly Required" and a one-line italic lede at the top;
house at upper left (no letters, no marks); worked example at upper right (an unruled cut-out, an arrow, and the folded
wedge); four nets below: net 1 (upper left), net 2 (upper right), net 3 (lower left) and net 4 (lower right), separated
by "+" signs; answer area at the bottom centre: a 4 x 2 grid of touching 70 px cells in grey hairlines (like the house
wall grid), each cell empty except a short black foot bar where an underlined letter would stand.
The short bar under each letter is its foot; the letter's own shape, read together with its foot, gives its turn on the
paper. The nets carry no lines at all inside their outlines: every fold, and every boundary between unit faces, has to be
recovered from the outline. Letters sit inside their faces but not necessarily at the face centre, so they mark which
face they belong to, not where its centre is. The unit edge is 70 px (a square is 70 x 70, a slope rectangle 70 x 99).

## Step 1 — Conventions from the worked example (needs: nothing)
- **See:** an unruled cut-out with G and F side by side, a slanted strip carrying Y, and two blank corners; arrow; the
  folded wedge with F upright on its white front and G on its light-grey top.
- **Conclude:** G and F are neighbours on the flat paper, yet on the block they lie on perpendicular faces, so a fold
  can sit where no line is drawn. Solid black = cut (the outline); everything inside the outline is paper that may fold
  or stay flat. The paper is folded printed side out; letters ride on their faces; the bar is the letter's foot. Squares
  are cube faces, the 1 x 1.41 rectangles are wedge slopes, half-square right triangles are wedge ends (blank). A branch
  that passes through a triangle from a leg to its long side is turned 45 degrees on paper and folds back square.
- **Excluded:** folding letters inside would hide every letter and contradicts the example block.

## Step 2 — The house (needs: nothing; parallel to steps 1 and 3)
- **See:** a 4 x 2 x 2 block of cubes with a gable roof (4 strips per slope, ridge along the long side), hidden
  edges as short dashes, and a lean-to annex at the right end, set back one cell, flush with the back wall.
- **Conclude:** 16 cubes + 8 roof wedges + annex cube + lean-to wedge, volume 21.5, no symmetry. The blanks (two
  rows of 4) have the shape of a 4 x 2 wall; the house has exactly two: the drawn front and the hidden back.

## Step 3 — Divide the nets into faces (needs: step 1)
- **See:** four outlines made of 70 px steps along the page axes and along 45-degree directions. Each letter lies
  inside one face.
- **Conclude:** the house grid and the example fix the allowed face shapes: unit squares, 70 x 99 slope rectangles and
  half-square triangles. Starting from the outline corners, tile each outline with these shapes, square-on along the
  axes and turned 45 degrees along the slanted branches, so that each letter falls inside one face and neighbouring
  faces meet along whole unit edges. Each outline has exactly one such division: net 1 has 20 faces, net 2 has 23, net 3
  has 26 and net 4 has 18 (net 3 has the most faces turned 45 degrees on the paper). A division that left a face hanging
  on by only half of an edge is not a net of unit faces. Record every face, its letter and the letter's turn.
- **Excluded:** placing faces by letter positions alone: the letters are off centre, and snapping faces to them
  misplaces the face grid so the paper no longer closes.

## Step 4 — Fold (needs: steps 1, 3)
- **See:** no crease marks; every edge shared by two faces may stay flat or fold by 45, 90 or 135 degrees either way.
- **Conclude:** require each net to close into one solid with printed side outward, fitting the house's unit grid.
  Each net has exactly one such folding. Their volumes in page order are 5, 5.5, 7 and 4 unit cubes (total 21.5, the
  house). Wedge slopes: 2 + 3 + 2 + 2 = 9 = 8 roof wedges + lean-to.
- **Excluded:** other fold choices leave the paper open or overlapping; an inside-out folding of nets 2, 3 or 4 is a
  mirror image that fits nowhere in the house.

## Step 5 — Fit the blocks into the house (needs: steps 2, 4)
- **Reason:** net 4 is the only block containing the lean-to, so it holds the annex. Number the house columns 1 to 4
  from left to right as drawn (column 4 at the annex end). The pieces then fit in exactly one way:
  - net 1: all of column 1 (four cubes and both roof wedges);
  - net 2: all of column 2 plus the back roof wedge of column 3;
  - net 3: all four cubes of column 3, the two front cubes of column 4 and the front roof wedges of columns 3 and 4;
  - net 4: the two back cubes of column 4, its back roof wedge, the annex cube and the lean-to.
- **Conclude:** one occupied-volume packing. Net 1's block is a plain 1 x 2 x 2 column with a gable cap and has a
  twofold symmetry (it can be turned end for end), so the letters give two assemblies. Geometry alone cannot finish the
  house; the letters have to.

## Step 6 — Which assembly puts an upright 4 x 2 wall on the house? (needs: steps 3, 4, 5)
- **See (front):** the drawn front wall never has more than 2 of its 8 letters upright, in either assembly.
- **See (back):** the hidden back wall is made of the back faces of columns 1 to 4, one column from each net. From
  net 4 come **O** (about (1260, 1676), lower right of the net) on the upper storey and **L** (about (1260, 1606)) on the lower;
  from net 3 **V** (about (187, 1431), top left of the net) and **O** (about (703, 1451)); from net 2 **E** (about (1246,
  1154)) and **A** (about (1176, 1154)); from net 1 **R** (about (484, 1076)) and **D** (about (554, 1076)). In one of the
  two assemblies all eight feet point down.
- **Conclude:** the only upright 4 x 2 wall in either assembly is the back wall, with net 1's column turned so that R
  and D face outward the right way up. In the other assembly the back wall reads OVEPLOAH with only 6 letters upright.
  The end walls, annex faces and roof slopes are not 4 x 2 walls.
- **Excluded:** the drawn front wall (never more than 2 of 8 upright), the other assembly's back wall.

## Step 7 — Read (needs: step 6)
- Stand behind the house (the annex end is now on the left) and read row by row: top **O V E R**, bottom
  **L O A D**.
- Other orders (LOADOVER, column-wise OLVOEARD, mirrored REVO / DAOL) are not words; no other wall of either assembly
  reads as a word.

**Answer: OVERLOAD** (the only 4 x 2 wall with all letters upright over all assemblies, read from outside: top row
then bottom row).

**Answer: OVERLOAD**
