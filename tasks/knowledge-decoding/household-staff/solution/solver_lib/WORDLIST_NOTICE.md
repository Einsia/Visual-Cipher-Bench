# Lexical data sources

`english_words.json` is derived from wordfreq 3.1.1, `top_n_list('en', 200000)`, restricted to ASCII alphabetic tokens and uppercased. This yields 183,150 forms.

Wordfreq code: Copyright Robyn Speer, Apache License 2.0; see `LICENSE-wordfreq.txt`. Data: Creative Commons Attribution-ShareAlike 4.0, https://creativecommons.org/licenses/by-sa/4.0/ . This derived word-form list is distributed under that same data license. Changes: ASCII/alphabetic filtering, uppercasing and JSON serialization; frequencies omitted.

Citation: Robyn Speer (2022), rspeer/wordfreq, Zenodo, https://doi.org/10.5281/zenodo.7199437 . Package version used: 3.1.1, https://pypi.org/project/wordfreq/3.1.1/ . The package acknowledges Google Books Ngrams, Leeds Internet Corpus, Wikipedia, ParaCrawl, OPUS/OpenSubtitles and freely available SUBTLEX lists by Marc Brysbaert and collaborators.

Princeton WordNet 3.0 material (distributed in NLTK's wordnet.zip, https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip) is governed by the included `LICENSE-WordNet.txt`.

`pronunciations.json` uses CMUdict pronunciation data (https://github.com/cmusphinx/cmudict). Copyright Carnegie Mellon University; BSD-style license. Changes: alphabetic ASCII words uppercased; stress digits removed. It contains the CMUdict entries whose spelling is in the English word list, the ordinary letter names A, B, E and I, regular -ER forms derived from known base pronunciations (remove ER, optionally restore E or undouble a consonant, append ER), and regular plurals generated uniformly for all entries, for 155,326 entries in total. Existing source pronunciations take precedence over derived forms. The derived forms are an over-approximation for phonetic letter strings, not a claim that each generated form has a standalone dictionary sense.
