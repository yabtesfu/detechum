# Sentence attribution pilot (attribution_pilot_v1)

Scorer: `gpttrace_v8s_1b_typography_off`. 50 native human essays (first 250 words at most), each with one GPT 3 sentence planted at a random position. Seed `20261118`. Intervals are 95% Clopper Pearson.

**Result under the reading fixed before the run: the method locates the planted sentence.**

| Measure | Observed | Chance |
|---|---|---|
| Planted sentence ranked first | 27/50 = 54.0% (39.3 to 68.2) | 6.9% |
| Planted sentence in the top 3 | 30/50 = 60.0% (45.2 to 73.6) | 20.8% |
| Planted sentence raises the score by 1 or more | 11/50 = 22.0% (11.5 to 36.0) | |
| Human first sentence ranked first, when the planted sentence is elsewhere | 9/48 = 18.8% (8.9 to 32.6) | 6.9% |

* Median contribution of the planted sentence: 0.33
* Median change of the document score from planting: 0.33
* Median contribution of a human first sentence: 0.12
