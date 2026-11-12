# Loose Threads — Walkthrough

Read the two pages in their printed order. Each long row contains thirteen outlined shapes; each short result or candidate contains five. Circles, squares and diamonds are abbreviated O, S and D below.

1. Look at the three long strings on the first page. Each crossed pair contains equal neighbors. The lower rows have five shapes rather than thirteen, so the arrow must include repeated changes; simply erasing the marked pair is insufficient. The outputs have no equal neighbors.

2. Compare the first two long rows. Only their ninth shape differs, but four output positions differ. Try a propagation rule associated with the erased shape. Exchanging the two other types throughout the suffix does not reproduce the printed outputs; neither does ordinary pair cancellation.

3. A rule that fits is to start the exchange on immediately to the right of each erased pair, then toggle it whenever the erased shape occurs in that current suffix. Such a shape itself is unchanged. Nothing left of the pair changes. After the scan, erase the newly created equal pair and apply the rule again. The word “current” matters: later switches depend on shapes already altered by earlier deletions. This is a hypothesis checked against all observations, not an instruction printed by the arrow.

4. Starting at the top crossed circles, the intermediate strings are OSDOOSODSDODS → OSDDODSDOSD → OSSDSDSOD → OOSDSDO → DSDSO. The last string is the visible endpoint. On the second example the same operation gives SDODO, agreeing with its different endpoint. On the third, starting with squares instead, it gives OSDSO. This matches the circled candidate 50; the filled 5 0 blanks tell you to copy the label digits unchanged.

5. Apply the same operation to each page-2 row. At each step only one equal pair is available. Stop once none remains, and compare the entire surviving order, not just the counts or leading shapes.

Row 1: OSDOOSODOSOSO → OSDDODODOSO → OSSDODSOS → OODOSOS → SOSOD. Its matching label is 16.

Row 2: ODOSDDODSODOD → ODOSSDSODSD → ODOOSODSO → ODDODSO → OSDSO. Its matching label is 91.

Row 3: SOSOSDDODODOS → SOSOSSDODSO → SOSOODOSO → SOSSOSO → SODSO. Its matching label is 61.

Row 4: SDSDSDOOSOSOS → SDSDSDDOSOD → SDSDSSOSD → SDSDDSD → SDSOD. Its matching label is 63.

Row 5: DOSDDODSDODSD → DOSSDSDSDSD → DOOSDSOSD → DDSDOSD → ODOSD. Its matching label is 87.

6. Read the selected labels in the page’s top-to-bottom order and copy each pair left to right into the five pairs of blank strokes: 16 91 61 63 87. The answer is **1691616387**. The labels are identifiers, so do not add, sort or convert them.

**Answer: 1691616387**
