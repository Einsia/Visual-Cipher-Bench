# PNG-only reference solver

Runtime is `solve.py` plus this directory. It reads only the supplied PNGs and generic recognition/linguistic resources.

`pixels.py` reads the example's empty silhouette and derives its two word lengths and the indices of the shared cell. `example_rules.py` compares eight ordinary local transformations against those observations using the full dictionary. Only first-sound exchange survives, with BEE/CONE inferred rather than read or stored. This is a bounded mechanism check, not a claim that finite examples uniquely specify arbitrary rules.

The bank parser recognizes pictograms at twelve page regions, checks the printed noncrossing instruction, and recovers pairing-circle centres from pixels. There are no source-specific direction labels or intended source pairs in the vocabulary. `spatial_rule_vocabulary.json` contains only the isolated instruction sentence, with no picture order or instance geometry.

`geometry.py` derives the main silhouette and candidate endpoints from intact vertical boundaries and the drawn horizontal evidence. All undrawn horizontal boundaries remain unknown. It also tests straight-segment intersection using the observed circle coordinates.

`engine.py` searches the full picture-name domains and phonetic dictionary, all across/down placements, missing endpoints, reciprocal pairings, crossings and noncrossing connections. Both searches enumerate all 132 noncrossing perfect matchings inferred from the circle coordinates as disjoint search blocks. This does not preselect the intended matching. `pair_first` uses exact-cover bitsets and a partial-English-answer test. `word_first` independently enumerates the full eight-letter English inventory, then filters explicit candidate lists by used sources/slots, cell equality and geometric compatibility. Caching geometric conflicts changes speed, not candidate domains.

The solver requires a unique answer, unique restored boundaries, unique source directions and unique matching. Spellings of internal homophones may vary. Neither candidate words nor the answer are selected from a target-specific shortlist.
