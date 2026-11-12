# Word of Mouth — Walkthrough

Each large letter ring and each small dial has a top notch. Count the ten positions clockwise from that notch, beginning with zero. On the starting ring this gives every letter a fixed value: A, E, I, L, N, O, R, S, T, U are 0 through 9. In the first row the three filled holes select positions 2, 1, 2. The starting ring reads I, E, I there; the right tray says IEI and the ring is unchanged. Thus a plain dial reads its current position and appends that letter. The arrows establish left-to-right processing. Each new row starts with the same letter ring and an empty tray.

The first row also calibrates the small numbered circles on the right-hand ring. Circles 1 and 3 hang off the slot holding I and circle 2 off the slot holding E: circle k marks the slot of the final ring that holds the k-th recorded letter. In the second and third rows the final ring's letters and the tray are blank, so each of those rows only tells us, for each record position, which slot of the (unknown) final ring holds that letter. Reading the circles, the second row's seven record letters sit at final slots 7, 5, 6, 0, 6, 6, 5, and the third row's at 4, 0, 4, 3, 5, 3, 7.

The square frames must change that action. The second row's positions are 3, 1, [3], [8], [5], 5, [5], where brackets represent the visible square frames. A simple explanation fits it: rotate the ring clockwise one position before each boxed read, without changing letter identities. That gives the record LEIRIIE on the final ring RSTUAEILNO, and those letters sit exactly at slots 7, 5, 6, 0, 6, 6, 5. Keep that as a candidate, rather than assuming this row has established the whole rule.

The third row rules that candidate out. Its positions are 9, 5, [4], [8], [5], 3, [7]. The candidate would produce the record UOLRIAL on the ring RSTUAEILNO, putting the first letter U at slot 3, but circle 1 sits at slot 4; the later circles fail as well. Nor does any fixed turn per box help on its own: circles 1 and 3 share a slot, so the third recorded letter must end up equal to the first, and circles 4 and 6 likewise. The final ring need not be a rotation of the starting ring, and earlier recorded letters may change. Both letter identities and positions therefore need attention. The small input symbols, the two kinds of dial and the fixed letter values suggest testing a shared local operation, rather than unrelated rules for individual rows.

Try exchanging the old record-end letter with the newly selected letter, everywhere in both the ring and the tray. Use the old end's value as a turn amount before selecting the new letter. The combination that fits both complete observations is:

- A plain dial reads the current ring at its marked position and appends that letter.
- A boxed dial first turns the ring clockwise by the value of the last recorded letter. It reads and appends the selected letter, then exchanges the old last letter and the new selected letter throughout both the ring and the entire record, including the newly appended letter.

These are hypotheses to check against all the visible endpoints. The second row's four boxed turns are 1, 1, 1, 1; its exchanges cancel in the final ring but affect the repeated characters in the record, which still ends as LEIRIIE on RSTUAEILNO. The third row's boxed turns are 5, 5, 5, 0. Half-turns and the zero turn cannot establish direction by themselves; the second row supplies that distinction. Together the two rows distinguish clockwise turning, the feedback letter, the timing of the read, and the exchange's scope.

For a direct check, the third row produces the successive records U, UO, OUO, TUTO, TUTAO, TUTAOA, TUTIOIA. Before its last box, the old end is A, whose value is zero. The ring stays in place for that read, then A and I exchange everywhere. The final ring is URSITOEALN, and the letters of TUTIOIA sit at its slots 4, 0, 4, 3, 5, 3, 7, exactly where circles 1 to 7 point. Omitting that exchange or restricting all exchanges to newly written letters fails the combined observations.

Now read the bottom row: 4, 3, [8], 9, [0], 7, [7], [9]. Apply the same operation, retaining the updated ring and record after every dial.

| Dial | Turn before reading | Letter read | Record after the action |
|---|---:|---|---|
| 4 | — | N | N |
| 3 | — | L | NL |
| [8] | L = 3 | O | NOL |
| 9 | — | R | NOLR |
| [0] | R = 6 | E | NOLER |
| 7 | — | T | NOLERT |
| [7] | T = 8 | A | NOLERAT |
| [9] | T = 8 | N | TOLERANT |

The final exchange changes the first letter as well as the later occurrence of N. The elbow arrow leads to the question mark in the record tray, so read the whole final record from left to right: **TOLERANT**. No final-ring reading or additional extraction is requested.

The examples support this common local composition and distinguish its ordinary alternatives. Finite observations cannot exclude arbitrary lookup rules made only to imitate those observations; that is not the sense of uniqueness used here.

**Answer: TOLERANT**
