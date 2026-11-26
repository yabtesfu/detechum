# Evaluation run of eval_plan_v2 (rehearsal on calib)

Plan: `eval_plan_v2`. Scorer: `gpttrace+desklib_logistic_rehearsal` (nakas/gpttrace-v8s-1b at revision `ac748e32ca8c`). Seed `20261119`. Intervals are 95% Clopper Pearson.

**This is a rehearsal.** Half of the groups of the calib split stand in for test. It checks the harness and is not a result.

What these corpora can and cannot show:

* **The texts of eval_v1 have been seen.** Their results were published, so the claims of this run rest on the texts added for eval_plan_v2.
* **The 300 Claude essays are in fitting only.** They were scored before the plan was frozen.
* **Attacked texts are DIPPER paraphrases and AI rewrites of AI essays, from GEDE.** Commercial humanizers and light human edits are not covered.
* **Native human essays come from BAWE (GEDE):** students at UK universities whose first language is English. Nonnative essays are mostly those of ELLIPSE, written in US schools. The two groups also differ in age and level, so a gap between them is not due to the first language alone.
* **The writers of the Ghostbuster human essays are unknown.** They come from IvyPanda and are counted in neither writer group.
* **Generators fine tuned on student essays are few:** one model of DACTYL. The rate on them rests on few texts.

## All texts

Fitted on 2330 human and 1991 AI texts, so P(AI) assumes that mix. Measured on 2323 human and 2020 AI texts. Threshold of M1 `0.579`, tau `0.717`.

| Source and class | Fitting | Measuring |
|---|---|---|
| claude_essays/ai | 134 | 166 |
| dactyl/ai | 344 | 398 |
| ellipse/human | 1674 | 1563 |
| gede/ai | 202 | 179 |
| gede/human | 111 | 86 |
| ghostbuster/ai | 130 | 153 |
| ghostbuster/human | 267 | 248 |
| liang/ai | 173 | 175 |
| liang/human | 192 | 201 |
| meld/ai | 773 | 735 |
| qwen_essays/ai | 221 | 198 |
| textsight/ai | 14 | 16 |
| textsight/human | 86 | 225 |

### M1: true positive rate at a 1% false positive rate

* **True positive rate:** 1840/2020 = 91.1% (89.8% to 92.3%)
* **Realized false positive rate (nominal 1.0%):** 16/2323 = 0.7% (0.4% to 1.1%)

Human texts by source. A claim of 1% or lower needs 300 texts.

| Source | Flagged | Enough texts for the claim |
|---|---|---|
| ellipse | 1/1563 = 0.1% (0.0% to 0.4%) | yes |
| gede | 0/86 = 0.0% (0.0% to 4.2%) | no |
| ghostbuster | 1/248 = 0.4% (0.0% to 2.2%) | no |
| liang | 14/201 = 7.0% (3.9% to 11.4%) | no |
| textsight | 0/225 = 0.0% (0.0% to 1.6%) | no |

Human texts by writer group. A claim of 1% or lower needs 300 texts.

| Writer group | Flagged | Enough texts for the claim |
|---|---|---|
| native | 1/150 = 0.7% (0.0% to 3.7%) | no |
| nonnative | 6/1671 = 0.4% (0.1% to 0.8%) | yes |
| unknown | 9/502 = 1.8% (0.8% to 3.4%) | yes |

Human texts by length in words. A claim of 1% or lower needs 300 texts.

| Length in words | Flagged | Enough texts for the claim |
|---|---|---|
| under 100 | 4/39 = 10.3% (2.9% to 24.2%) | no |
| 100 to 149 | 5/141 = 3.5% (1.2% to 8.1%) | no |
| 150 to 249 | 5/388 = 1.3% (0.4% to 3.0%) | yes |
| 250 to 499 | 1/1121 = 0.1% (0.0% to 0.5%) | yes |
| 500 or more | 1/634 = 0.2% (0.0% to 0.9%) | yes |

AI texts by source.

| Source | Flagged |
|---|---|
| claude_essays | 165/166 = 99.4% (96.7% to 100.0%) |
| dactyl | 323/398 = 81.2% (77.0% to 84.9%) |
| gede | 179/179 = 100.0% (98.0% to 100.0%) |
| ghostbuster | 152/153 = 99.3% (96.4% to 100.0%) |
| liang | 172/175 = 98.3% (95.1% to 99.6%) |
| meld | 639/735 = 86.9% (84.3% to 89.3%) |
| qwen_essays | 196/198 = 99.0% (96.4% to 99.9%) |
| textsight | 14/16 = 87.5% (61.7% to 98.4%) |

AI texts by generator.

| Generator | Flagged |
|---|---|
| DeepSeek-V3 | 35/35 = 100.0% (90.0% to 100.0%) |
| ShantanuT01/fine-tuned-Llama-3.2-1B-Instruct-apollo-mini-student_essays-testing | 7/18 = 38.9% (17.3% to 64.3%) |
| claude (2023) | 31/32 = 96.9% (83.8% to 99.9%) |
| claude-3-5-haiku-20241022 | 29/34 = 85.3% (68.9% to 95.0%) |
| claude-3-5-sonnet-20241022 | 31/37 = 83.8% (68.0% to 93.8%) |
| claude-haiku | 191/197 = 97.0% (93.5% to 98.9%) |
| claude-haiku-4-5 | 4/4 = 100.0% (39.8% to 100.0%) |
| claude-haiku-5-5 | 55/55 = 100.0% (93.5% to 100.0%) |
| claude-opus-5 | 2/2 = 100.0% (15.8% to 100.0%) |
| claude-opus-5-5 | 52/52 = 100.0% (93.2% to 100.0%) |
| claude-sonnet-5-5 | 58/59 = 98.3% (90.9% to 100.0%) |
| gemini-1.5-flash | 34/35 = 97.1% (85.1% to 99.9%) |
| gemini-1.5-pro | 30/33 = 90.9% (75.7% to 98.1%) |
| gemini-3-flash | 158/186 = 84.9% (79.0% to 89.8%) |
| gpt-3 | 87/87 = 100.0% (95.8% to 100.0%) |
| gpt-3 (prompt engineered) | 85/88 = 96.6% (90.4% to 99.3%) |
| gpt-3.5-turbo (2023) | 121/121 = 100.0% (97.0% to 100.0%) |
| gpt-4.1 | 3/3 = 100.0% (29.2% to 100.0%) |
| gpt-4o-2024-11-20 | 29/30 = 96.7% (82.8% to 99.9%) |
| gpt-4o-mini | 28/28 = 100.0% (87.7% to 100.0%) |
| gpt-4o-mini-2024-07-18 | 89/89 = 100.0% (95.9% to 100.0%) |
| gpt-5.4-mini | 128/179 = 71.5% (64.3% to 78.0%) |
| gpt-oss-120b | 4/4 = 100.0% (39.8% to 100.0%) |
| llama-3.2-90b | 23/36 = 63.9% (46.2% to 79.2%) |
| llama-3.3-70b | 21/32 = 65.6% (46.8% to 81.4%) |
| meta-llama/Llama-3.2-1B-Instruct | 4/16 = 25.0% (7.3% to 52.4%) |
| meta-llama/Llama-3.3-70B-Instruct | 90/90 = 100.0% (96.0% to 100.0%) |
| mistral-large-latest | 29/35 = 82.9% (66.4% to 93.4%) |
| mistral-small-latest | 23/29 = 79.3% (60.3% to 92.0%) |
| qwen-3.6-plus | 162/173 = 93.6% (88.9% to 96.8%) |
| qwen-3.8-27b | 1/3 = 33.3% (0.8% to 90.6%) |
| qwen2.5-1.5b-instruct | 196/198 = 99.0% (96.4% to 99.9%) |

AI texts by length in words.

| Length in words | Flagged |
|---|---|
| under 100 | 25/28 = 89.3% (71.8% to 97.7%) |
| 100 to 149 | 127/131 = 96.9% (92.4% to 99.2%) |
| 150 to 249 | 211/252 = 83.7% (78.6% to 88.1%) |
| 250 to 499 | 1170/1284 = 91.1% (89.4% to 92.6%) |
| 500 or more | 307/325 = 94.5% (91.4% to 96.7%) |

AI texts by generator family. Verdicts count texts of 150 words or more.

| Generator family | Flagged | Labelled Likely human |
|---|---|---|
| claude | 453/472 = 96.0% (93.8% to 97.6%) | 10/471 = 2.1% (1.0% to 3.9%) |
| deepseek | 35/35 = 100.0% (90.0% to 100.0%) | 0/35 = 0.0% (0.0% to 10.0%) |
| gemini | 222/254 = 87.4% (82.7% to 91.2%) | 13/254 = 5.1% (2.8% to 8.6%) |
| gpt | 574/629 = 91.3% (88.8% to 93.3%) | 25/486 = 5.1% (3.4% to 7.5%) |
| llama | 145/192 = 75.5% (68.8% to 81.4%) | 42/192 = 21.9% (16.2% to 28.4%) |
| mistral | 52/64 = 81.2% (69.5% to 89.9%) | 7/63 = 11.1% (4.6% to 21.6%) |
| qwen | 359/374 = 96.0% (93.5% to 97.7%) | 5/360 = 1.4% (0.5% to 3.2%) |

AI texts by kind of essay. Verdicts count texts of 150 words or more.

| Kind of essay | Flagged | Labelled Likely human |
|---|---|---|
| argument | 114/114 = 100.0% (96.8% to 100.0%) | 0/111 = 0.0% (0.0% to 3.3%) |
| explanatory | 115/115 = 100.0% (96.8% to 100.0%) | 0/112 = 0.0% (0.0% to 3.2%) |
| personal | 132/135 = 97.8% (93.6% to 99.5%) | 0/127 = 0.0% (0.0% to 2.9%) |

AI texts by voice. Verdicts count texts of 150 words or more.

| Voice | Flagged | Labelled Likely human |
|---|---|---|
| grade | 126/127 = 99.2% (95.7% to 100.0%) | 0/125 = 0.0% (0.0% to 2.9%) |
| learner | 268/322 = 83.2% (78.7% to 87.1%) | 40/313 = 12.8% (9.3% to 17.0%) |
| plain | 290/313 = 92.7% (89.2% to 95.3%) | 19/307 = 6.2% (3.8% to 9.5%) |

### M2: calibration of P(AI)

* **ECE (15 equal mass bins):** 0.0120. Target: at most 0.03. Met: yes.
* **Brier score:** 0.0286

![Reliability diagram](reliability.svg)

### M3: nonnative release gate

* Nonnative human texts flagged at the M1 threshold: 6/1671 = 0.4% (0.1% to 0.8%)
* Native human texts flagged at the M1 threshold: 1/150 = 0.7% (0.0% to 3.7%)
* Upper bound of the nonnative rate at most 2.0%: yes
* Rule of §2, ratio of the rates is 0.54, at most 1.5: yes. Gate: passed.
* Rule proposed in §10, upper bounds (0.8% against 1.5 times 3.7%): yes. Gate: passed.
* **Gate under the rule adopted at the tag (section_2): passed.**

### M4: attacked texts

True positive rate at the M1 threshold, against the unattacked AI texts of the same source. The drop is in absolute points, with Newcombe's interval from the two Clopper Pearson intervals.

| Attack | Unattacked | Attacked | Drop | Verdicts, enough words |
|---|---|---|---|---|
| gede/dipper | 179/179 = 100.0% (98.0% to 100.0%) | 30/31 = 96.8% (83.3% to 99.9%) | 3.2% (-0.5% to 16.7%) | 30 Likely AI, 1 Likely human, 0 Can't tell, 0 no verdict |
| gede/rewrite | 179/179 = 100.0% (98.0% to 100.0%) | 69/69 = 100.0% (94.8% to 100.0%) | 0.0% (-2.0% to 5.2%) | 69 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict |

### Verdict rules and rates

| Length band of the conformal layer | Human texts in fitting | AI texts in fitting | Can label as AI | Can label as human |
|---|---|---|---|---|
| 150 to 249 | 287 | 252 | yes | yes |
| 250 to 499 | 1209 | 1252 | yes | yes |
| 500 or more | 706 | 325 | yes | yes |

| Texts | Class | n | Likely AI | Likely human | Can't tell | No verdict | Wrong label | Own class ruled out |
|---|---|---|---|---|---|---|---|---|
| all lengths | human | 2323 | 3 | 2115 | 25 | 180 | 3/2323 = 0.1% (0.0% to 0.4%) | 10/2143 = 0.5% (0.2% to 0.9%) |
| all lengths | ai | 2020 | 1676 | 102 | 83 | 159 | 102/2020 = 5.0% (4.1% to 6.1%) | 125/1861 = 6.7% (5.6% to 8.0%) |
| 150 words or more | human | 2143 | 3 | 2115 | 25 | 0 | 3/2143 = 0.1% (0.0% to 0.4%) | 10/2143 = 0.5% (0.2% to 0.9%) |
| 150 words or more | ai | 1861 | 1676 | 102 | 83 | 0 | 102/1861 = 5.5% (4.5% to 6.6%) | 125/1861 = 6.7% (5.6% to 8.0%) |
| 150 to 249 | human | 388 | 1 | 369 | 18 | 0 | 1/388 = 0.3% (0.0% to 1.4%) | 1/388 = 0.3% (0.0% to 1.4%) |
| 150 to 249 | ai | 252 | 199 | 10 | 43 | 0 | 10/252 = 4.0% (1.9% to 7.2%) | 10/252 = 4.0% (1.9% to 7.2%) |
| 250 to 499 | human | 1121 | 1 | 1115 | 5 | 0 | 1/1121 = 0.1% (0.0% to 0.5%) | 6/1121 = 0.5% (0.2% to 1.2%) |
| 250 to 499 | ai | 1284 | 1170 | 82 | 32 | 0 | 82/1284 = 6.4% (5.1% to 7.9%) | 97/1284 = 7.6% (6.2% to 9.1%) |
| 500 or more | human | 634 | 1 | 631 | 2 | 0 | 1/634 = 0.2% (0.0% to 0.9%) | 3/634 = 0.5% (0.1% to 1.4%) |
| 500 or more | ai | 325 | 307 | 10 | 8 | 0 | 10/325 = 3.1% (1.5% to 5.6%) | 18/325 = 5.5% (3.3% to 8.6%) |

### Human texts that an AI edited

* **gede/improve-human:** flagged at the M1 threshold 45/50 = 90.0% (78.2% to 96.7%). Verdicts with enough words: 45 Likely AI, 4 Likely human, 1 Can't tell, 0 no verdict.
* **gede/rewrite-human:** flagged at the M1 threshold 50/50 = 100.0% (92.9% to 100.0%). Verdicts with enough words: 50 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.
* **liang/chatgpt (simplify):** flagged at the M1 threshold 49/51 = 96.1% (86.5% to 99.5%). Verdicts with enough words: 9 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.
* **liang/gpt-4 (polish):** flagged at the M1 threshold 38/39 = 97.4% (86.5% to 99.9%). Verdicts with enough words: 0 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.

## Student essays only (`--kind student_essay`)

Fitted on 2174 human and 1057 AI texts, so P(AI) assumes that mix. Measured on 2023 human and 1130 AI texts. Threshold of M1 `-0.131`, tau `0.500`.

| Source and class | Fitting | Measuring |
|---|---|---|
| claude_essays/ai | 134 | 166 |
| dactyl/ai | 344 | 398 |
| ellipse/human | 1674 | 1563 |
| gede/ai | 202 | 179 |
| gede/human | 111 | 86 |
| ghostbuster/ai | 130 | 153 |
| ghostbuster/human | 267 | 248 |
| liang/ai | 26 | 36 |
| liang/human | 122 | 126 |
| qwen_essays/ai | 221 | 198 |

### M1: true positive rate at a 1% false positive rate

* **True positive rate:** 1063/1130 = 94.1% (92.5% to 95.4%)
* **Realized false positive rate (nominal 1.0%):** 19/2023 = 0.9% (0.6% to 1.5%)

Human texts by source. A claim of 1% or lower needs 300 texts.

| Source | Flagged | Enough texts for the claim |
|---|---|---|
| ellipse | 2/1563 = 0.1% (0.0% to 0.5%) | yes |
| gede | 2/86 = 2.3% (0.3% to 8.1%) | no |
| ghostbuster | 4/248 = 1.6% (0.4% to 4.1%) | no |
| liang | 11/126 = 8.7% (4.4% to 15.1%) | no |

Human texts by writer group. A claim of 1% or lower needs 300 texts.

| Writer group | Flagged | Enough texts for the claim |
|---|---|---|
| native | 4/150 = 2.7% (0.7% to 6.7%) | no |
| nonnative | 11/1625 = 0.7% (0.3% to 1.2%) | yes |
| unknown | 4/248 = 1.6% (0.4% to 4.1%) | no |

Human texts by length in words. A claim of 1% or lower needs 300 texts.

| Length in words | Flagged | Enough texts for the claim |
|---|---|---|
| under 100 | 4/30 = 13.3% (3.8% to 30.7%) | no |
| 100 to 149 | 6/77 = 7.8% (2.9% to 16.2%) | no |
| 150 to 249 | 1/240 = 0.4% (0.0% to 2.3%) | no |
| 250 to 499 | 5/1049 = 0.5% (0.2% to 1.1%) | yes |
| 500 or more | 3/627 = 0.5% (0.1% to 1.4%) | yes |

AI texts by source.

| Source | Flagged |
|---|---|
| claude_essays | 166/166 = 100.0% (97.8% to 100.0%) |
| dactyl | 332/398 = 83.4% (79.4% to 86.9%) |
| gede | 179/179 = 100.0% (98.0% to 100.0%) |
| ghostbuster | 153/153 = 100.0% (97.6% to 100.0%) |
| liang | 36/36 = 100.0% (90.3% to 100.0%) |
| qwen_essays | 197/198 = 99.5% (97.2% to 100.0%) |

AI texts by generator.

| Generator | Flagged |
|---|---|
| DeepSeek-V3 | 35/35 = 100.0% (90.0% to 100.0%) |
| ShantanuT01/fine-tuned-Llama-3.2-1B-Instruct-apollo-mini-student_essays-testing | 7/18 = 38.9% (17.3% to 64.3%) |
| claude (2023) | 32/32 = 100.0% (89.1% to 100.0%) |
| claude-3-5-haiku-20241022 | 29/34 = 85.3% (68.9% to 95.0%) |
| claude-3-5-sonnet-20241022 | 32/37 = 86.5% (71.2% to 95.5%) |
| claude-haiku-5-5 | 55/55 = 100.0% (93.5% to 100.0%) |
| claude-opus-5-5 | 52/52 = 100.0% (93.2% to 100.0%) |
| claude-sonnet-5-5 | 59/59 = 100.0% (93.9% to 100.0%) |
| gemini-1.5-flash | 34/35 = 97.1% (85.1% to 99.9%) |
| gemini-1.5-pro | 31/33 = 93.9% (79.8% to 99.3%) |
| gpt-3 | 18/18 = 100.0% (81.5% to 100.0%) |
| gpt-3 (prompt engineered) | 18/18 = 100.0% (81.5% to 100.0%) |
| gpt-3.5-turbo (2023) | 121/121 = 100.0% (97.0% to 100.0%) |
| gpt-4o-2024-11-20 | 30/30 = 100.0% (88.4% to 100.0%) |
| gpt-4o-mini | 28/28 = 100.0% (87.7% to 100.0%) |
| gpt-4o-mini-2024-07-18 | 89/89 = 100.0% (95.9% to 100.0%) |
| llama-3.2-90b | 23/36 = 63.9% (46.2% to 79.2%) |
| llama-3.3-70b | 22/32 = 68.8% (50.0% to 83.9%) |
| meta-llama/Llama-3.2-1B-Instruct | 6/16 = 37.5% (15.2% to 64.6%) |
| meta-llama/Llama-3.3-70B-Instruct | 90/90 = 100.0% (96.0% to 100.0%) |
| mistral-large-latest | 31/35 = 88.6% (73.3% to 96.8%) |
| mistral-small-latest | 24/29 = 82.8% (64.2% to 94.2%) |
| qwen2.5-1.5b-instruct | 197/198 = 99.5% (97.2% to 100.0%) |

AI texts by length in words.

| Length in words | Flagged |
|---|---|
| under 100 | 9/10 = 90.0% (55.5% to 99.7%) |
| 100 to 149 | 8/10 = 80.0% (44.4% to 97.5%) |
| 150 to 249 | 140/146 = 95.9% (91.3% to 98.5%) |
| 250 to 499 | 780/838 = 93.1% (91.1% to 94.7%) |
| 500 or more | 126/126 = 100.0% (97.1% to 100.0%) |

AI texts by generator family. Verdicts count texts of 150 words or more.

| Generator family | Flagged | Labelled Likely human |
|---|---|---|
| claude | 259/269 = 96.3% (93.3% to 98.2%) | 7/268 = 2.6% (1.1% to 5.3%) |
| deepseek | 35/35 = 100.0% (90.0% to 100.0%) | 0/35 = 0.0% (0.0% to 10.0%) |
| gemini | 65/68 = 95.6% (87.6% to 99.1%) | 1/68 = 1.5% (0.0% to 7.9%) |
| gpt | 304/304 = 100.0% (98.8% to 100.0%) | 0/300 = 0.0% (0.0% to 1.2%) |
| llama | 148/192 = 77.1% (70.5% to 82.8%) | 42/192 = 21.9% (16.2% to 28.4%) |
| mistral | 55/64 = 85.9% (75.0% to 93.4%) | 7/63 = 11.1% (4.6% to 21.6%) |
| qwen | 197/198 = 99.5% (97.2% to 100.0%) | 0/184 = 0.0% (0.0% to 2.0%) |

AI texts by kind of essay. Verdicts count texts of 150 words or more.

| Kind of essay | Flagged | Labelled Likely human |
|---|---|---|
| argument | 114/114 = 100.0% (96.8% to 100.0%) | 0/111 = 0.0% (0.0% to 3.3%) |
| explanatory | 115/115 = 100.0% (96.8% to 100.0%) | 0/112 = 0.0% (0.0% to 3.2%) |
| personal | 134/135 = 99.3% (95.9% to 100.0%) | 0/127 = 0.0% (0.0% to 2.9%) |

AI texts by voice. Verdicts count texts of 150 words or more.

| Voice | Flagged | Labelled Likely human |
|---|---|---|
| grade | 126/127 = 99.2% (95.7% to 100.0%) | 0/125 = 0.0% (0.0% to 2.9%) |
| learner | 277/322 = 86.0% (81.8% to 89.6%) | 38/313 = 12.1% (8.7% to 16.3%) |
| plain | 292/313 = 93.3% (89.9% to 95.8%) | 19/307 = 6.2% (3.8% to 9.5%) |

### M2: calibration of P(AI)

* **ECE (15 equal mass bins):** 0.0126. Target: at most 0.03. Met: yes.
* **Brier score:** 0.0234

![Reliability diagram](reliability_student_essay.svg)

### M3: nonnative release gate

* Nonnative human texts flagged at the M1 threshold: 11/1625 = 0.7% (0.3% to 1.2%)
* Native human texts flagged at the M1 threshold: 4/150 = 2.7% (0.7% to 6.7%)
* Upper bound of the nonnative rate at most 2.0%: yes
* Rule of §2, ratio of the rates is 0.25, at most 1.5: yes. Gate: passed.
* Rule proposed in §10, upper bounds (1.2% against 1.5 times 6.7%): yes. Gate: passed.
* **Gate under the rule adopted at the tag (section_2): passed.**

### M4: attacked texts

True positive rate at the M1 threshold, against the unattacked AI texts of the same source. The drop is in absolute points, with Newcombe's interval from the two Clopper Pearson intervals.

| Attack | Unattacked | Attacked | Drop | Verdicts, enough words |
|---|---|---|---|---|
| gede/dipper | 179/179 = 100.0% (98.0% to 100.0%) | 30/31 = 96.8% (83.3% to 99.9%) | 3.2% (-0.5% to 16.7%) | 30 Likely AI, 1 Likely human, 0 Can't tell, 0 no verdict |
| gede/rewrite | 179/179 = 100.0% (98.0% to 100.0%) | 69/69 = 100.0% (94.8% to 100.0%) | 0.0% (-2.0% to 5.2%) | 69 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict |

### Verdict rules and rates

| Length band of the conformal layer | Human texts in fitting | AI texts in fitting | Can label as AI | Can label as human |
|---|---|---|---|---|
| 150 to 249 | 223 | 147 | yes | yes |
| 250 to 499 | 1191 | 786 | yes | yes |
| 500 or more | 706 | 109 | yes | yes |

| Texts | Class | n | Likely AI | Likely human | Can't tell | No verdict | Wrong label | Own class ruled out |
|---|---|---|---|---|---|---|---|---|
| all lengths | human | 2023 | 0 | 1904 | 12 | 107 | 0/2023 = 0.0% (0.0% to 0.2%) | 12/1916 = 0.6% (0.3% to 1.1%) |
| all lengths | ai | 1130 | 1017 | 57 | 36 | 20 | 57/1130 = 5.0% (3.8% to 6.5%) | 72/1110 = 6.5% (5.1% to 8.1%) |
| 150 words or more | human | 1916 | 0 | 1904 | 12 | 0 | 0/1916 = 0.0% (0.0% to 0.2%) | 12/1916 = 0.6% (0.3% to 1.1%) |
| 150 words or more | ai | 1110 | 1017 | 57 | 36 | 0 | 57/1110 = 5.1% (3.9% to 6.6%) | 72/1110 = 6.5% (5.1% to 8.1%) |
| 150 to 249 | human | 240 | 0 | 237 | 3 | 0 | 0/240 = 0.0% (0.0% to 1.5%) | 3/240 = 1.2% (0.3% to 3.6%) |
| 150 to 249 | ai | 146 | 137 | 3 | 6 | 0 | 3/146 = 2.1% (0.4% to 5.9%) | 3/146 = 2.1% (0.4% to 5.9%) |
| 250 to 499 | human | 1049 | 0 | 1043 | 6 | 0 | 0/1049 = 0.0% (0.0% to 0.4%) | 6/1049 = 0.6% (0.2% to 1.2%) |
| 250 to 499 | ai | 838 | 758 | 54 | 26 | 0 | 54/838 = 6.4% (4.9% to 8.3%) | 65/838 = 7.8% (6.0% to 9.8%) |
| 500 or more | human | 627 | 0 | 624 | 3 | 0 | 0/627 = 0.0% (0.0% to 0.6%) | 3/627 = 0.5% (0.1% to 1.4%) |
| 500 or more | ai | 126 | 122 | 0 | 4 | 0 | 0/126 = 0.0% (0.0% to 2.9%) | 4/126 = 3.2% (0.9% to 7.9%) |

### Human texts that an AI edited

* **gede/improve-human:** flagged at the M1 threshold 45/50 = 90.0% (78.2% to 96.7%). Verdicts with enough words: 43 Likely AI, 3 Likely human, 4 Can't tell, 0 no verdict.
* **gede/rewrite-human:** flagged at the M1 threshold 50/50 = 100.0% (92.9% to 100.0%). Verdicts with enough words: 50 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.
* **liang/chatgpt (simplify):** flagged at the M1 threshold 51/51 = 100.0% (93.0% to 100.0%). Verdicts with enough words: 9 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.
* **liang/gpt-4 (polish):** flagged at the M1 threshold 38/39 = 97.4% (86.5% to 99.9%). Verdicts with enough words: 0 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.

## Inputs

* calib_manifest: SHA 256 `4959ab6e0c633231a2b0ef723b62e19ca3f85b1787cad351c49cbb0d7a5f08c1`
* test_manifest: SHA 256 `651f05bfb034022f50b01af3e299c90fcdb1d220c2d2e39f11dafe80c9fcd0cb`
* scores: SHA 256 `c9547007b3dbc8e0aa971f7093a739183b5d7293926cfba501f2002a83eef55f`
