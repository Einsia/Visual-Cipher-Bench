# Drydock Cipher — Walkthrough

Coordinates below refer to the delivered 2193-by-1700 PNG. The title and story are at upper left, a small sample at upper right, two large sheets across the upper middle, two further sheets at lower left and lower right, the vessel between them, and a blank 4-by-2 patch beneath it.

1. **Read the conventions.** The sample's outlined five-face sheet closes into a wedge with the printing outside. Only its top N is shown after folding. A short bar is the foot of its letter. Solid borders cut, dash-dot lines fold convexly and long dashes fold concavely. The story warns that some creases are unmarked: a join between two unit faces inside continuous paper may stay flat or may fold, and the printed lines are not a complete list of creases. The sample is not a fifth vessel piece; it fixes the unit length (about 70 px), the square/triangle/sloping-rectangle face grammar, outward printing and the foot-bar convention.

2. **Recover the target.** The vessel has a rectangular four-by-two-by-two upper hull, a V-shaped lower hull, a shallow wedge bow and an offset raised cabin. The vessel carries no unit grid: read its dashed hidden edges, its face shading (tops light grey, right-hand faces darker grey, front faces white) and its edge proportions together; the raised cabin is one cube, the upper hull is four cubes long and two high. The shape contains 17 cubes and 10 half-cubes, 22 cubic units in all. There is no highlighted reading side. The empty patch matches a two-row, four-column portion of either long side.

3. **Recover the panels.** The upper-left sheet occupies approximately (192,380) to (810,800); upper right (1385,360) to (1965,815). The lower-left sheet occupies about (190,930) to (730,1450), and the lower-right sheet (1455,940) to (2005,1440). Measure the common square edge from the sample. The four sheets contain 14, 11, 11, 12 continuous panels but 24, 24, 23, 21 unit faces (squares, right triangles and sloping rectangles). Follow the outline through concave corners and use glyph positions to split each continuous panel into unit faces; this recovers 10, 13, 12, 9 unmarked joins. Do not invent extra divisions through letters. All four sheets switch between axis-aligned and diagonal branches.

4. **Fold.** Treat every unmarked join as an unknown hinge (flat or folded) and every printed crease as given, keep the printing outside, and carry each face and foot bar through the folding. The upper-left, lower-left and lower-right sheets each close in exactly one way, with volumes 6, 5.5 and 4.5. The upper-right sheet closes in two different ways, both of volume 6, so volume alone does not choose between them. None of the four solids is a plain box: each has sloping faces and a concave notch, and each is chiral. A footprint alone is insufficient: record which direction each letter points on the folded surface.

5. **Pack.** The volumes sum to 22, the vessel's volume. Try placing the four solids, under rotations only, to fill the vessel exactly. With the first closure of the upper-right sheet no exact fill exists; with the second there is exactly one assembly. The assembly, not the letters, therefore settles the upper-right fold. Every exterior face of the vessel is covered exactly once, and all inner faces meet in pairs.

6. **Find the upright patch.** Check every 4-by-2 window on both long sides. On the visible side at most one letter in any window stands upright. On the hidden side, one window has all eight letters upright, and it draws on all four sheets: two letters each from the upper sheets, one from the lower-left sheet and three from the lower-right sheet.

7. **Read from outside, behind the vessel.** Follow the top row and then the bottom row. The recovered glyph positions provide a check on the final mapping:

| Position | Letter | Sheet | Approximate centre in PNG |
|---|---|---|---|
| Top left | C | Upper right | (1634,476) |
| Top second | R | Lower right | (1853,1190) |
| Top third | O | Lower right | (1953,1091) |
| Top right | S | Upper left | (390,501) |
| Bottom left | S | Upper right | (1788,611) |
| Bottom second | B | Lower left | (341,1298) |
| Bottom third | A | Lower right | (1656,1091) |
| Bottom right | R | Upper left | (688,699) |

This gives **CROS / SBAR**, hence **CROSSBAR**. Reading through the vessel from the front reverses each row and fails. Folding any sheet with its printing inside either admits no assembly or cannot fill a window with outward letters, so the sample's outward-printing convention is needed.

**Answer: CROSSBAR**
