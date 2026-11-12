# Dockside Detours — Walkthrough

Start with the two tables above the ring. Each column is a complete snapshot: six numbered positions, a grey letter plaque at each position, a separate counter beside it, and one circled counter. The labels above the columns are times, not operation numbers for adjacent columns: the first table shows 0, 5, 10, and the second shows 0, 4, 10.

Compare the counters across the first interval of the upper table. They lose 1, 0, 1, 1, 2, 0 respectively, a total of five. In its second interval they lose 2, 0, 1, 2, 0, 0, again five. The lower table loses four units and then six. The letter multisets stay unchanged. These observations suggest one counter decrement per round and movement of letters among fixed counter positions. The circle supplies the current position. The clockwise arrow inside the question ring supplies the increasing, wrapping direction for the numbered positions.

The intermediate moves are deliberately absent. Test candidate moves against the whole interval, including its ending circle and every letter. For example, in the first interval the departure multiset is {1, 3, 4, 5, 5}, with the first departure at the circled position 1. Its order must produce SEESSD and finish at position 3 after five rounds. The second table provides a different multiset and different repeated letters, so the same proposed rule must also explain that table.

A rule that fits every printed snapshot is as follows. Decrease the current counter by one. Select all positions whose counters equal this new value, including the current position and including zeros. Move each selected letter forward to the next selected position, wrapping at the end. Follow the plaque that departed from the current position to its new position. From there, move forward by the number of positions whose visible letter changed in this round. That last position becomes current. Stop when the current counter is zero.

Two details need checking rather than assuming. The counters stay at their numbered positions; only the letters move. Also, count changed letter values, not moved plaques: exchanging identical letters contributes no visible change. In the first round of the upper table, positions 1, 3, 5 are selected after the decrement. Their S, E, E rotate to E, S, E, so only two positions change. The active plaque travels from 1 to 3, then the two-position hop lands at 5. After the next four rounds the printed middle column is reproduced. Counting all three selected positions would instead land at 6, a rival that fails the later observations.

One way to check the discovery systematically is to enumerate departures consistent with the observed losses. Under decrement-then-equal-selection, forward rotation leaves 3, 3, 2, and 5 possible histories for the four printed intervals before fixing the hop rule. Backward rotation has no history for three of those intervals. Comparing the hop origins and quantities across the histories leaves the changed-letter count from the carried plaque. Counting unchanged letters backwards is equivalent: on an n-position ring, going backwards n-h positions lands exactly where going forwards h positions does. Broader tests of selection before or after the decrement, equality or inequalities, inclusion of self and zeros, and other simple hop quantities leave that same process. This is evidence among natural local rules, not a claim that finitely many examples determine every imaginable function.

The shaded columns and pause bars show what 'stop' means. The upper final column still has a 3 at position 6; the lower still has a 2 at position 4. Thus stopping does not require all counters to vanish. Both stop at a circled zero. The arrows below those columns lead to numbered readouts: positions 3, 1, 2, 6 of EESSSD give SEED; positions 1, 3, 5, 4 of TEATRT give TART. This establishes terminal-position extraction.

Now read the twelve positions of the ring clockwise from the top. The letters are RAERESTTSIDM, the counters are 2, 1, 2, 2, 2, 2, 2, 2, 3, 2, 3, 0, and position 1 is circled. In its first round, decrementing position 1 selects positions 1 and 2. Swapping their R and A changes two values; the carried plaque reaches 2 and the hop reaches 4. Continue the same process:

| Round | Letters at positions 1–12 | Counters at positions 1–12 | Current position |
| ---: | --- | --- | ---: |
| 0 | RAERESTTSIDM | 2, 1, 2, 2, 2, 2, 2, 2, 3, 2, 3, 0 | 1 |
| 1 | ARERESTTSIDM | 1, 1, 2, 2, 2, 2, 2, 2, 3, 2, 3, 0 | 4 |
| 2 | RAERESTTSIDM | 1, 1, 2, 1, 2, 2, 2, 2, 3, 2, 3, 0 | 3 |
| 3 | RRAEESTTSIDM | 1, 1, 1, 1, 2, 2, 2, 2, 3, 2, 3, 0 | 7 |
| 4 | TRRAESETSIDM | 1, 1, 1, 1, 2, 2, 1, 2, 3, 2, 3, 0 | 5 |
| 5 | ETRRASETSIDM | 1, 1, 1, 1, 1, 2, 1, 2, 3, 2, 3, 0 | 11 |
| 6 | ETRRADESSTIM | 1, 1, 1, 1, 1, 2, 1, 2, 3, 2, 2, 0 | 10 |
| 7 | TETRRDASSEIM | 1, 1, 1, 1, 1, 2, 1, 2, 3, 1, 2, 0 | 7 |
| 8 | TETRRDMSSEIA | 1, 1, 1, 1, 1, 2, 0, 2, 3, 1, 2, 0 | 2 |
| 9 | TATRRDESSEIM | 1, 0, 1, 1, 1, 2, 0, 2, 3, 1, 2, 0 | 10 |
| 10 | TMTRRDASSEIE | 1, 0, 1, 1, 1, 2, 0, 2, 3, 0, 2, 0 | 3 |
| 11 | TEMRRDTSSAIE | 1, 0, 0, 1, 1, 2, 0, 2, 3, 0, 2, 0 | 11 |
| 12 | IEMTRDTSSARE | 1, 0, 0, 1, 1, 2, 0, 2, 3, 0, 1, 0 | 4 |
| 13 | IEEMRDTSSTRA | 1, 0, 0, 0, 1, 2, 0, 2, 3, 0, 1, 0 | 11 |
| 14 | IAEERDMSSTTR | 1, 0, 0, 0, 1, 2, 0, 2, 3, 0, 0, 0 | 5 |
| 15 | IRAEEDRSSMTT | 1, 0, 0, 0, 0, 2, 0, 2, 3, 0, 0, 0 | 1 |
| 16 | TIRAEDESSRMT | 0, 0, 0, 0, 0, 2, 0, 2, 3, 0, 0, 0 | 9 |
| 17 | TIRAESEDSRMT | 0, 0, 0, 0, 0, 2, 0, 2, 2, 0, 0, 0 | 8 |
| 18 | TIRAESEDSRMT | 0, 0, 0, 0, 0, 2, 0, 1, 2, 0, 0, 0 | 8 |
| 19 | TTIRASEESDRM | 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0 | 6 |
| 20 | TTIRASEESDRM | 0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 0 | 6 |
| 21 | MTTIRASESEDR | 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0 | 4 |

At round 21, the circle would be at position 4, whose counter is zero. Read the bottom indices from left to right: 7, 3, 5, 10, 6, 1, 8, 11. The corresponding letters of MTTIRASESEDR are S, T, R, E, A, M, E, D. The answer is **STREAMED**.

Every round decreases the total counter sum by exactly one, and the next state is determined by the discovered rule. Therefore the run terminates and its terminal readout is unique. The word also fits the page's water-and-journey theme, but that association is a confirmation after extraction, not a substitute for the calculation.

**Answer: STREAMED**
