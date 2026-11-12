# Echo Vault — Walkthrough

1. Separate fixed square slot numbers from the circular rings attached to specimens. The five calibration columns are complete snapshots, not successive lists of instructions. The transfer log gives only the two words named at each step; the addresses must be inferred by comparing consecutive columns. The word inventory and ring inventory each carry ×1.

2. Compare Initial with After 1. Step 1 names REED and ARCH, whose current rings are 3 and 1. REED's ring 3 points to After 3, where REED occupies square 4; ARCH's ring 1 points to After 1, where ARCH occupies square 1. Exchange the *current* tubes at squares 4 and 1, carrying their circular rings along: ARCH(1), OVAL(2), GLOW(4), REED(3).

3. That alone does not reach After 1. The rings must then be exchanged on their own at the slots named by the original current ring values, 3 and 1: ARCH(4), OVAL(2), GLOW(1), REED(3), which is exactly After 1. Step 2 confirms it: OVAL's ring 2 points to After 2 (OVAL in square 1), ARCH's ring 4 points to After 4 (ARCH in square 2); exchange tubes 1 ⇄ 2, then rings only at slots 2 ⇄ 4. Step 3 (GLOW 1 → After 1 → square 3, OVAL 2 → After 2 → square 1) works the same way. In Step 4 both lookups return square 1, so the tube exchange is the identity and only the ring exchange at slots 3 ⇄ 2 changes anything. The repeated GLOW/OVAL pair in Steps 3 and 4 having different effects shows that the addresses depend on the current state, and the steps together distinguish selecting a completed snapshot from always consulting Final.

4. On plate 2, the left panel maps the final column GLOW, ARCH, OVAL, REED to W, A, V, E. Working the calibration backwards, their initial rings are 4, 1, 2, 3, and GLOW[4]=W, ARCH[1]=A, OVAL[2]=V, REED[3]=E: each letter is taken at the specimen's initial ring. The right panel connects the final ring of OVAL (1) to a snapshot; the drawn tower ARCH(4), OVAL(2), GLOW(1), REED(3) matches only After 1. Its bracket joins slots 1 and 4, a span of three slot intervals, matching GLOW's final ring 3. Apply that connection pattern to plate 3. The word above each bracket precedes the word below it, with a positive gap selected by the other final ring. The three visible “Final” roles must not be confused: observation time, observation distance and output ordering use final information, but letter indices use initial rings.

5. Introduce nine position permutations and nine ring permutations. Each of the eight named transfer pairs imposes two updates. Snapshot queries can point forward, so a forward simulation with a guessed start is not enough. The observation-time selectors are WINDPIPE (three observations), ADJACENT (two), and AIRWAVES, TUNNELED and RUMBLING (one each), so the eight constraints are spread over five different snapshots and tie the whole history together. Relative positions must fit into eight slots without overlap.

6. Search the coupled constraints. The unique initial column, top to bottom, is OVERTONE(5), DAYLIGHT(7), TUNNELED(4), RUMBLING(8), AIRWAVES(1), DRUMBEAT(2), WINDPIPE(6), ADJACENT(3). For example, transfer 1 reads snapshots 8 and 4 and returns slots 3 and 7; after those tubes exchange, its ring-only exchange is at slots 8 and 4. The full checked history (slots 1 to 8; each transfer first exchanges the tubes at the two returned slots, then exchanges only the rings at the two slots named by the original current rings):

| Transfer | First word: ring → snapshot → slot | Second word: ring → snapshot → slot | Tubes | Rings |
|---:|---|---|---|---|
| 1 | RUMBLING 8 → After 8 → 3 | TUNNELED 4 → After 4 → 7 | 3 ⇄ 7 | 8 ⇄ 4 |
| 2 | OVERTONE 5 → After 5 → 4 | RUMBLING 3 → After 3 → 2 | 4 ⇄ 2 | 5 ⇄ 3 |
| 3 | AIRWAVES 6 → After 6 → 1 | OVERTONE 5 → After 5 → 4 | 1 ⇄ 4 | 6 ⇄ 5 |
| 4 | ADJACENT 8 → After 8 → 6 | DRUMBEAT 6 → After 6 → 8 | 6 ⇄ 8 | 8 ⇄ 6 |
| 5 | RUMBLING 3 → After 3 → 2 | WINDPIPE 1 → After 1 → 3 | 2 ⇄ 3 | 3 ⇄ 1 |
| 6 | DAYLIGHT 3 → After 3 → 1 | AIRWAVES 2 → After 2 → 5 | 1 ⇄ 5 | 3 ⇄ 2 |
| 7 | RUMBLING 1 → After 1 → 4 | AIRWAVES 2 → After 2 → 5 | 4 ⇄ 5 | 1 ⇄ 2 |
| 8 | TUNNELED 4 → After 4 → 7 | AIRWAVES 7 → After 7 → 1 | 7 ⇄ 1 | 4 ⇄ 7 |

- Initial: OVERTONE(5), DAYLIGHT(7), TUNNELED(4), RUMBLING(8), AIRWAVES(1), DRUMBEAT(2), WINDPIPE(6), ADJACENT(3)
- After 1: OVERTONE(5), DAYLIGHT(7), WINDPIPE(6), RUMBLING(3), AIRWAVES(1), DRUMBEAT(2), TUNNELED(4), ADJACENT(8)
- After 2: OVERTONE(5), RUMBLING(3), WINDPIPE(1), DAYLIGHT(7), AIRWAVES(6), DRUMBEAT(2), TUNNELED(4), ADJACENT(8)
- After 3: DAYLIGHT(7), RUMBLING(3), WINDPIPE(1), OVERTONE(5), AIRWAVES(2), DRUMBEAT(6), TUNNELED(4), ADJACENT(8)
- After 4: DAYLIGHT(7), RUMBLING(3), WINDPIPE(1), OVERTONE(5), AIRWAVES(2), ADJACENT(6), TUNNELED(4), DRUMBEAT(8)
- After 5: DAYLIGHT(3), WINDPIPE(1), RUMBLING(7), OVERTONE(5), AIRWAVES(2), ADJACENT(6), TUNNELED(4), DRUMBEAT(8)
- After 6: AIRWAVES(2), WINDPIPE(7), RUMBLING(1), OVERTONE(5), DAYLIGHT(3), ADJACENT(6), TUNNELED(4), DRUMBEAT(8)
- After 7: AIRWAVES(7), WINDPIPE(2), RUMBLING(1), DAYLIGHT(3), OVERTONE(5), ADJACENT(6), TUNNELED(4), DRUMBEAT(8)
- After 8: TUNNELED(4), WINDPIPE(2), RUMBLING(1), DAYLIGHT(7), OVERTONE(5), ADJACENT(6), AIRWAVES(3), DRUMBEAT(8)


7. The final column is TUNNELED(4), WINDPIPE(2), RUMBLING(1), DAYLIGHT(7), OVERTONE(5), ADJACENT(6), AIRWAVES(3), DRUMBEAT(8). Reading the observations left to right, top to bottom, their selected times are 2, 3, 2, 4, 2, 6, 6, 1, not the visible order of the diagrams. Verify the eight gaps: 1, 5, 3, 2, 5, 3, 1, 3. For example, in After 2 OVERTONE is in slot 1 and RUMBLING in slot 2 (gap 1 = RUMBLING’s final ring); in After 3 RUMBLING is in slot 2 and TUNNELED in slot 7 (gap 5 = OVERTONE’s final ring); in After 4 AIRWAVES is in slot 5 and TUNNELED in slot 7 (gap 2 = WINDPIPE’s final ring); in After 6 RUMBLING is in slot 3 and OVERTONE in slot 4 (gap 1); in After 1 WINDPIPE is in slot 3 and DRUMBEAT in slot 6 (gap 3 = AIRWAVES’s final ring).

8. Take the initial rings of those final words: 4, 6, 8, 7, 5, 3, 1, 2. The indexed letters are N I G H T J A R, giving **NIGHTJAR**. The word is a check on the extraction, not an extra constraint used to choose a history.

**Answer: NIGHTJAR**
