# Window Dressing — Walkthrough

The eight answer blanks read **CTYVEKZS**.

Start with the first page. The legend associates dashed outlines with View A and solid outlines with View B. In the separated example, follow each horizontal arrow from the dashed position to the solid position. The longest move is labelled 1, the middle-length move 2, and the shortest 3. The filled answer is H A T, so the letters are read in decreasing horizontal displacement, rather than left-to-right position or arrow-lane height.

The small diagram below the windows shows how to recover a letter: align the two upright strokes from View A with the short horizontal stroke from View B, producing H. The lower two rows establish a further point needed on page two. H and T occupy overlapping open frames; their black strokes combine, and then the grey strips hide some of that combined ink. A black stroke within a frame can therefore come from another letter. Grey means hidden; exposed white means no letter contributes black at that location.

On the second page each window has its own eight open frames, marked by small tabs: dashed tabs below View A and solid tabs below View B. Unlike the example, no arrows connect them, so which View A frame became which View B frame has to be worked out from the letters themselves. Measured from the left edge of the delivered page, the tab centres are:

| Tab, left to right | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| View A | 400 | 452 | 504 | 556 | 608 | 660 | 712 | 764 |
| View B | 798 | 842 | 886 | 930 | 974 | 1018 | 1062 | 1106 |

The dimensions are in native pixels; only their relative lengths matter.

Now reconstruct the letter shapes in each window. Use the heavy uppercase style illustrated on page one and centre each candidate on its tab. The main windows share a vertical scale: the straight cap and baseline strokes run from about y450 to y790 in View A and y1070 to y1410 in View B; curved letters slightly overshoot those lines. Reject any candidate that would put black into an exposed white region. Do not reject strokes hidden by grey, and do not assume that all black within one frame belongs to that frame. The remaining candidates must jointly cover all exposed black in the window.

Neither window settles its letters alone. In View A, reading tabs left to right, three scenes fit exactly: T V C H Y K S E, T V C T Y K S E and T V C Z Y K S E. In View B, two scenes fit: Z V I S K C Y E and Z V T S K C Y E. The same eight letters must appear in both views, unchanged, merely moved. Only **T V C Z Y K S E** in View A and **Z V T S K C Y E** in View B contain the same letters, so these are the two scenes. The search does not assume the letters are distinct and does not need an English-word guess or an anagram step.

Because the eight letters happen to be different, each View A frame now has exactly one partner in View B:

| View A tab | A centre | Letter | B centre | Horizontal move |
|---|---:|:---:|---:|---:|
| First | 400 | T | 886 | 486 |
| Second | 452 | V | 842 | 390 |
| Third | 504 | C | 1018 | 514 |
| Fourth | 556 | Z | 798 | 242 |
| Fifth | 608 | Y | 1062 | 454 |
| Sixth | 660 | K | 974 | 314 |
| Seventh | 712 | S | 930 | 218 |
| Eighth | 764 | E | 1106 | 342 |

No individual frame needs to display its entire letter. The evidence is the consistency of all shapes with both visible unions. Swapping any two letters between their View B positions would put black onto exposed white or leave exposed black uncovered.

Finally, sort the horizontal moves from largest to smallest:

514, 486, 454, 390, 342, 314, 242, 218.

These select the third, first, fifth, second, eighth, sixth, fourth and seventh View A tabs. Their letters fill the eight blanks as **C T Y V E K Z S**. Reversing the order would contradict the numbered HAT example; reading by either screen position would also contradict that example.

**Answer: CTYVEKZS**
