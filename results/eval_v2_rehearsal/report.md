# Evaluation run of eval_plan_v2 (rehearsal on calib)

Plan: `eval_plan_v2`. Scorer: `gpttrace_v8s_1b_typography_off` (nakas/gpttrace-v8s-1b at revision `ac748e32ca8c`). Seed `20261119`. Intervals are 95% Clopper Pearson.

**This is a rehearsal.** Half of the groups of the calib split stand in for test. It checks the harness and is not a result.

What these corpora can and cannot show:

* **The texts of eval_v1 have been seen.** Their results were published, so the claims of this run rest on the texts added for eval_plan_v2.
* **The 300 Claude essays are in fitting only.** They were scored before the plan was frozen.
* **Attacked texts are DIPPER paraphrases and AI rewrites of AI essays, from GEDE.** Commercial humanizers and light human edits are not covered.
* **Native human essays come from BAWE (GEDE):** students at UK universities whose first language is English. Nonnative essays are mostly those of ELLIPSE, written in US schools. The two groups also differ in age and level, so a gap between them is not due to the first language alone.
* **The writers of the Ghostbuster human essays are unknown.** They come from IvyPanda and are counted in neither writer group.
* **Generators fine tuned on student essays are few:** one model of DACTYL. The rate on them rests on few texts.

## All texts

Fitted on 2330 human and 1991 AI texts, so P(AI) assumes that mix. Measured on 2323 human and 2020 AI texts. Threshold of M1 `7.867`, tau `0.500`.

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

* **True positive rate:** 1907/2020 = 94.4% (93.3% to 95.4%)
* **Realized false positive rate (nominal 1.0%):** 22/2323 = 0.9% (0.6% to 1.4%)

Human texts by source. A claim of 1% or lower needs 300 texts.

| Source | Flagged | Enough texts for the claim |
|---|---|---|
| ellipse | 0/1563 = 0.0% (0.0% to 0.2%) | yes |
| gede | 0/86 = 0.0% (0.0% to 4.2%) | no |
| ghostbuster | 9/248 = 3.6% (1.7% to 6.8%) | no |
| liang | 13/201 = 6.5% (3.5% to 10.8%) | no |
| textsight | 0/225 = 0.0% (0.0% to 1.6%) | no |

Human texts by writer group. A claim of 1% or lower needs 300 texts.

| Writer group | Flagged | Enough texts for the claim |
|---|---|---|
| native | 2/150 = 1.3% (0.2% to 4.7%) | no |
| nonnative | 1/1671 = 0.1% (0.0% to 0.3%) | yes |
| unknown | 19/502 = 3.8% (2.3% to 5.8%) | yes |

Human texts by length in words. A claim of 1% or lower needs 300 texts.

| Length in words | Flagged | Enough texts for the claim |
|---|---|---|
| under 100 | 3/39 = 7.7% (1.6% to 20.9%) | no |
| 100 to 149 | 4/141 = 2.8% (0.8% to 7.1%) | no |
| 150 to 249 | 2/388 = 0.5% (0.1% to 1.8%) | yes |
| 250 to 499 | 10/1121 = 0.9% (0.4% to 1.6%) | yes |
| 500 or more | 3/634 = 0.5% (0.1% to 1.4%) | yes |

AI texts by source.

| Source | Flagged |
|---|---|
| claude_essays | 166/166 = 100.0% (97.8% to 100.0%) |
| dactyl | 302/398 = 75.9% (71.4% to 80.0%) |
| gede | 179/179 = 100.0% (98.0% to 100.0%) |
| ghostbuster | 151/153 = 98.7% (95.4% to 99.8%) |
| liang | 173/175 = 98.9% (95.9% to 99.9%) |
| meld | 726/735 = 98.8% (97.7% to 99.4%) |
| qwen_essays | 194/198 = 98.0% (94.9% to 99.4%) |
| textsight | 16/16 = 100.0% (79.4% to 100.0%) |

AI texts by generator.

| Generator | Flagged |
|---|---|
| DeepSeek-V3 | 35/35 = 100.0% (90.0% to 100.0%) |
| ShantanuT01/fine-tuned-Llama-3.2-1B-Instruct-apollo-mini-student_essays-testing | 2/18 = 11.1% (1.4% to 34.7%) |
| claude (2023) | 30/32 = 93.8% (79.2% to 99.2%) |
| claude-3-5-haiku-20241022 | 27/34 = 79.4% (62.1% to 91.3%) |
| claude-3-5-sonnet-20241022 | 29/37 = 78.4% (61.8% to 90.2%) |
| claude-haiku | 197/197 = 100.0% (98.1% to 100.0%) |
| claude-haiku-4-5 | 4/4 = 100.0% (39.8% to 100.0%) |
| claude-haiku-5-5 | 55/55 = 100.0% (93.5% to 100.0%) |
| claude-opus-5 | 2/2 = 100.0% (15.8% to 100.0%) |
| claude-opus-5-5 | 52/52 = 100.0% (93.2% to 100.0%) |
| claude-sonnet-5-5 | 59/59 = 100.0% (93.9% to 100.0%) |
| gemini-1.5-flash | 31/35 = 88.6% (73.3% to 96.8%) |
| gemini-1.5-pro | 30/33 = 90.9% (75.7% to 98.1%) |
| gemini-3-flash | 185/186 = 99.5% (97.0% to 100.0%) |
| gpt-3 | 87/87 = 100.0% (95.8% to 100.0%) |
| gpt-3 (prompt engineered) | 86/88 = 97.7% (92.0% to 99.7%) |
| gpt-3.5-turbo (2023) | 121/121 = 100.0% (97.0% to 100.0%) |
| gpt-4.1 | 3/3 = 100.0% (29.2% to 100.0%) |
| gpt-4o-2024-11-20 | 29/30 = 96.7% (82.8% to 99.9%) |
| gpt-4o-mini | 28/28 = 100.0% (87.7% to 100.0%) |
| gpt-4o-mini-2024-07-18 | 89/89 = 100.0% (95.9% to 100.0%) |
| gpt-5.4-mini | 171/179 = 95.5% (91.4% to 98.1%) |
| gpt-oss-120b | 4/4 = 100.0% (39.8% to 100.0%) |
| llama-3.2-90b | 22/36 = 61.1% (43.5% to 76.9%) |
| llama-3.3-70b | 20/32 = 62.5% (43.7% to 78.9%) |
| meta-llama/Llama-3.2-1B-Instruct | 1/16 = 6.2% (0.2% to 30.2%) |
| meta-llama/Llama-3.3-70B-Instruct | 90/90 = 100.0% (96.0% to 100.0%) |
| mistral-large-latest | 26/35 = 74.3% (56.7% to 87.5%) |
| mistral-small-latest | 22/29 = 75.9% (56.5% to 89.7%) |
| qwen-3.6-plus | 173/173 = 100.0% (97.9% to 100.0%) |
| qwen-3.8-27b | 3/3 = 100.0% (29.2% to 100.0%) |
| qwen2.5-1.5b-instruct | 194/198 = 98.0% (94.9% to 99.4%) |

AI texts by length in words.

| Length in words | Flagged |
|---|---|
| under 100 | 23/28 = 82.1% (63.1% to 93.9%) |
| 100 to 149 | 128/131 = 97.7% (93.5% to 99.5%) |
| 150 to 249 | 244/252 = 96.8% (93.8% to 98.6%) |
| 250 to 499 | 1197/1284 = 93.2% (91.7% to 94.5%) |
| 500 or more | 315/325 = 96.9% (94.4% to 98.5%) |

AI texts by generator family. Verdicts count texts of 150 words or more.

| Generator family | Flagged | Labelled Likely human |
|---|---|---|
| claude | 455/472 = 96.4% (94.3% to 97.9%) | 13/471 = 2.8% (1.5% to 4.7%) |
| deepseek | 35/35 = 100.0% (90.0% to 100.0%) | 0/35 = 0.0% (0.0% to 10.0%) |
| gemini | 246/254 = 96.9% (93.9% to 98.6%) | 5/254 = 2.0% (0.6% to 4.5%) |
| gpt | 618/629 = 98.3% (96.9% to 99.1%) | 4/486 = 0.8% (0.2% to 2.1%) |
| llama | 135/192 = 70.3% (63.3% to 76.7%) | 55/192 = 28.6% (22.4% to 35.6%) |
| mistral | 48/64 = 75.0% (62.6% to 85.0%) | 11/63 = 17.5% (9.1% to 29.1%) |
| qwen | 370/374 = 98.9% (97.3% to 99.7%) | 0/360 = 0.0% (0.0% to 1.0%) |

AI texts by kind of essay. Verdicts count texts of 150 words or more.

| Kind of essay | Flagged | Labelled Likely human |
|---|---|---|
| argument | 114/114 = 100.0% (96.8% to 100.0%) | 0/111 = 0.0% (0.0% to 3.3%) |
| explanatory | 115/115 = 100.0% (96.8% to 100.0%) | 0/112 = 0.0% (0.0% to 3.2%) |
| personal | 131/135 = 97.0% (92.6% to 99.2%) | 0/127 = 0.0% (0.0% to 2.9%) |

AI texts by voice. Verdicts count texts of 150 words or more.

| Voice | Flagged | Labelled Likely human |
|---|---|---|
| grade | 126/127 = 99.2% (95.7% to 100.0%) | 0/125 = 0.0% (0.0% to 2.9%) |
| learner | 255/322 = 79.2% (74.3% to 83.5%) | 53/313 = 16.9% (12.9% to 21.6%) |
| plain | 281/313 = 89.8% (85.9% to 92.9%) | 30/307 = 9.8% (6.7% to 13.7%) |

### M2: calibration of P(AI)

* **ECE (15 equal mass bins):** 0.0106. Target: at most 0.03. Met: yes.
* **Brier score:** 0.0254

![Reliability diagram](reliability.svg)

### M3: nonnative release gate

* Nonnative human texts flagged at the M1 threshold: 1/1671 = 0.1% (0.0% to 0.3%)
* Native human texts flagged at the M1 threshold: 2/150 = 1.3% (0.2% to 4.7%)
* Upper bound of the nonnative rate at most 2.0%: yes
* Rule of §2, ratio of the rates is 0.04, at most 1.5: yes. Gate: passed.
* Rule proposed in §10, upper bounds (0.3% against 1.5 times 4.7%): yes. Gate: passed.
* **Gate under the rule adopted at the tag (section_2): passed.**

### M4: attacked texts

True positive rate at the M1 threshold, against the unattacked AI texts of the same source. The drop is in absolute points, with Newcombe's interval from the two Clopper Pearson intervals.

| Attack | Unattacked | Attacked | Drop | Verdicts, enough words |
|---|---|---|---|---|
| gede/dipper | 179/179 = 100.0% (98.0% to 100.0%) | 30/31 = 96.8% (83.3% to 99.9%) | 3.2% (-0.5% to 16.7%) | 29 Likely AI, 1 Likely human, 1 Can't tell, 0 no verdict |
| gede/rewrite | 179/179 = 100.0% (98.0% to 100.0%) | 69/69 = 100.0% (94.8% to 100.0%) | 0.0% (-2.0% to 5.2%) | 69 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict |

### Verdict rules and rates

| Length band of the conformal layer | Human texts in fitting | AI texts in fitting | Can label as AI | Can label as human |
|---|---|---|---|---|
| 150 to 249 | 287 | 252 | yes | yes |
| 250 to 499 | 1209 | 1252 | yes | yes |
| 500 or more | 706 | 325 | yes | yes |

| Texts | Class | n | Likely AI | Likely human | Can't tell | No verdict | Wrong label | Own class ruled out |
|---|---|---|---|---|---|---|---|---|
| all lengths | human | 2323 | 7 | 2094 | 42 | 180 | 7/2323 = 0.3% (0.1% to 0.6%) | 20/2143 = 0.9% (0.6% to 1.4%) |
| all lengths | ai | 2020 | 1741 | 88 | 32 | 159 | 88/2020 = 4.4% (3.5% to 5.3%) | 114/1861 = 6.1% (5.1% to 7.3%) |
| 150 words or more | human | 2143 | 7 | 2094 | 42 | 0 | 7/2143 = 0.3% (0.1% to 0.7%) | 20/2143 = 0.9% (0.6% to 1.4%) |
| 150 words or more | ai | 1861 | 1741 | 88 | 32 | 0 | 88/1861 = 4.7% (3.8% to 5.8%) | 114/1861 = 6.1% (5.1% to 7.3%) |
| 150 to 249 | human | 388 | 1 | 365 | 22 | 0 | 1/388 = 0.3% (0.0% to 1.4%) | 1/388 = 0.3% (0.0% to 1.4%) |
| 150 to 249 | ai | 252 | 240 | 6 | 6 | 0 | 6/252 = 2.4% (0.9% to 5.1%) | 6/252 = 2.4% (0.9% to 5.1%) |
| 250 to 499 | human | 1121 | 5 | 1103 | 13 | 0 | 5/1121 = 0.4% (0.1% to 1.0%) | 16/1121 = 1.4% (0.8% to 2.3%) |
| 250 to 499 | ai | 1284 | 1192 | 78 | 14 | 0 | 78/1284 = 6.1% (4.8% to 7.5%) | 92/1284 = 7.2% (5.8% to 8.7%) |
| 500 or more | human | 634 | 1 | 626 | 7 | 0 | 1/634 = 0.2% (0.0% to 0.9%) | 3/634 = 0.5% (0.1% to 1.4%) |
| 500 or more | ai | 325 | 309 | 4 | 12 | 0 | 4/325 = 1.2% (0.3% to 3.1%) | 16/325 = 4.9% (2.8% to 7.9%) |

### Human texts that an AI edited

* **gede/improve-human:** flagged at the M1 threshold 42/50 = 84.0% (70.9% to 92.8%). Verdicts with enough words: 38 Likely AI, 5 Likely human, 7 Can't tell, 0 no verdict.
* **gede/rewrite-human:** flagged at the M1 threshold 49/50 = 98.0% (89.4% to 99.9%). Verdicts with enough words: 48 Likely AI, 1 Likely human, 1 Can't tell, 0 no verdict.
* **liang/chatgpt (simplify):** flagged at the M1 threshold 32/51 = 62.7% (48.1% to 75.9%). Verdicts with enough words: 6 Likely AI, 0 Likely human, 3 Can't tell, 0 no verdict.
* **liang/gpt-4 (polish):** flagged at the M1 threshold 36/39 = 92.3% (79.1% to 98.4%). Verdicts with enough words: 0 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.

## Student essays only (`--kind student_essay`)

Fitted on 2174 human and 1057 AI texts, so P(AI) assumes that mix. Measured on 2023 human and 1130 AI texts. Threshold of M1 `6.993`, tau `0.500`.

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

* **True positive rate:** 1037/1130 = 91.8% (90.0% to 93.3%)
* **Realized false positive rate (nominal 1.0%):** 24/2023 = 1.2% (0.8% to 1.8%)

Human texts by source. A claim of 1% or lower needs 300 texts.

| Source | Flagged | Enough texts for the claim |
|---|---|---|
| ellipse | 0/1563 = 0.0% (0.0% to 0.2%) | yes |
| gede | 0/86 = 0.0% (0.0% to 4.2%) | no |
| ghostbuster | 18/248 = 7.3% (4.4% to 11.2%) | no |
| liang | 6/126 = 4.8% (1.8% to 10.1%) | no |

Human texts by writer group. A claim of 1% or lower needs 300 texts.

| Writer group | Flagged | Enough texts for the claim |
|---|---|---|
| native | 3/150 = 2.0% (0.4% to 5.7%) | no |
| nonnative | 3/1625 = 0.2% (0.0% to 0.5%) | yes |
| unknown | 18/248 = 7.3% (4.4% to 11.2%) | no |

Human texts by length in words. A claim of 1% or lower needs 300 texts.

| Length in words | Flagged | Enough texts for the claim |
|---|---|---|
| under 100 | 1/30 = 3.3% (0.1% to 17.2%) | no |
| 100 to 149 | 2/77 = 2.6% (0.3% to 9.1%) | no |
| 150 to 249 | 0/240 = 0.0% (0.0% to 1.5%) | no |
| 250 to 499 | 13/1049 = 1.2% (0.7% to 2.1%) | yes |
| 500 or more | 8/627 = 1.3% (0.6% to 2.5%) | yes |

AI texts by source.

| Source | Flagged |
|---|---|
| claude_essays | 166/166 = 100.0% (97.8% to 100.0%) |
| dactyl | 310/398 = 77.9% (73.5% to 81.9%) |
| gede | 179/179 = 100.0% (98.0% to 100.0%) |
| ghostbuster | 151/153 = 98.7% (95.4% to 99.8%) |
| liang | 36/36 = 100.0% (90.3% to 100.0%) |
| qwen_essays | 195/198 = 98.5% (95.6% to 99.7%) |

AI texts by generator.

| Generator | Flagged |
|---|---|
| DeepSeek-V3 | 35/35 = 100.0% (90.0% to 100.0%) |
| ShantanuT01/fine-tuned-Llama-3.2-1B-Instruct-apollo-mini-student_essays-testing | 3/18 = 16.7% (3.6% to 41.4%) |
| claude (2023) | 30/32 = 93.8% (79.2% to 99.2%) |
| claude-3-5-haiku-20241022 | 28/34 = 82.4% (65.5% to 93.2%) |
| claude-3-5-sonnet-20241022 | 31/37 = 83.8% (68.0% to 93.8%) |
| claude-haiku-5-5 | 55/55 = 100.0% (93.5% to 100.0%) |
| claude-opus-5-5 | 52/52 = 100.0% (93.2% to 100.0%) |
| claude-sonnet-5-5 | 59/59 = 100.0% (93.9% to 100.0%) |
| gemini-1.5-flash | 31/35 = 88.6% (73.3% to 96.8%) |
| gemini-1.5-pro | 31/33 = 93.9% (79.8% to 99.3%) |
| gpt-3 | 18/18 = 100.0% (81.5% to 100.0%) |
| gpt-3 (prompt engineered) | 18/18 = 100.0% (81.5% to 100.0%) |
| gpt-3.5-turbo (2023) | 121/121 = 100.0% (97.0% to 100.0%) |
| gpt-4o-2024-11-20 | 29/30 = 96.7% (82.8% to 99.9%) |
| gpt-4o-mini | 28/28 = 100.0% (87.7% to 100.0%) |
| gpt-4o-mini-2024-07-18 | 89/89 = 100.0% (95.9% to 100.0%) |
| llama-3.2-90b | 22/36 = 61.1% (43.5% to 76.9%) |
| llama-3.3-70b | 20/32 = 62.5% (43.7% to 78.9%) |
| meta-llama/Llama-3.2-1B-Instruct | 1/16 = 6.2% (0.2% to 30.2%) |
| meta-llama/Llama-3.3-70B-Instruct | 90/90 = 100.0% (96.0% to 100.0%) |
| mistral-large-latest | 28/35 = 80.0% (63.1% to 91.6%) |
| mistral-small-latest | 23/29 = 79.3% (60.3% to 92.0%) |
| qwen2.5-1.5b-instruct | 195/198 = 98.5% (95.6% to 99.7%) |

AI texts by length in words.

| Length in words | Flagged |
|---|---|
| under 100 | 7/10 = 70.0% (34.8% to 93.3%) |
| 100 to 149 | 8/10 = 80.0% (44.4% to 97.5%) |
| 150 to 249 | 140/146 = 95.9% (91.3% to 98.5%) |
| 250 to 499 | 758/838 = 90.5% (88.3% to 92.4%) |
| 500 or more | 124/126 = 98.4% (94.4% to 99.8%) |

AI texts by generator family. Verdicts count texts of 150 words or more.

| Generator family | Flagged | Labelled Likely human |
|---|---|---|
| claude | 255/269 = 94.8% (91.4% to 97.1%) | 11/268 = 4.1% (2.1% to 7.2%) |
| deepseek | 35/35 = 100.0% (90.0% to 100.0%) | 0/35 = 0.0% (0.0% to 10.0%) |
| gemini | 62/68 = 91.2% (81.8% to 96.7%) | 2/68 = 2.9% (0.4% to 10.2%) |
| gpt | 303/304 = 99.7% (98.2% to 100.0%) | 1/300 = 0.3% (0.0% to 1.8%) |
| llama | 136/192 = 70.8% (63.9% to 77.2%) | 49/192 = 25.5% (19.5% to 32.3%) |
| mistral | 51/64 = 79.7% (67.8% to 88.7%) | 8/63 = 12.7% (5.6% to 23.5%) |
| qwen | 195/198 = 98.5% (95.6% to 99.7%) | 0/184 = 0.0% (0.0% to 2.0%) |

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
| learner | 263/322 = 81.7% (77.0% to 85.7%) | 42/313 = 13.4% (9.8% to 17.7%) |
| plain | 282/313 = 90.1% (86.2% to 93.2%) | 27/307 = 8.8% (5.9% to 12.5%) |

### M2: calibration of P(AI)

* **ECE (15 equal mass bins):** 0.0122. Target: at most 0.03. Met: yes.
* **Brier score:** 0.0298

![Reliability diagram](reliability_student_essay.svg)

### M3: nonnative release gate

* Nonnative human texts flagged at the M1 threshold: 3/1625 = 0.2% (0.0% to 0.5%)
* Native human texts flagged at the M1 threshold: 3/150 = 2.0% (0.4% to 5.7%)
* Upper bound of the nonnative rate at most 2.0%: yes
* Rule of §2, ratio of the rates is 0.09, at most 1.5: yes. Gate: passed.
* Rule proposed in §10, upper bounds (0.5% against 1.5 times 5.7%): yes. Gate: passed.
* **Gate under the rule adopted at the tag (section_2): passed.**

### M4: attacked texts

True positive rate at the M1 threshold, against the unattacked AI texts of the same source. The drop is in absolute points, with Newcombe's interval from the two Clopper Pearson intervals.

| Attack | Unattacked | Attacked | Drop | Verdicts, enough words |
|---|---|---|---|---|
| gede/dipper | 179/179 = 100.0% (98.0% to 100.0%) | 30/31 = 96.8% (83.3% to 99.9%) | 3.2% (-0.5% to 16.7%) | 29 Likely AI, 1 Likely human, 1 Can't tell, 0 no verdict |
| gede/rewrite | 179/179 = 100.0% (98.0% to 100.0%) | 69/69 = 100.0% (94.8% to 100.0%) | 0.0% (-2.0% to 5.2%) | 69 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict |

### Verdict rules and rates

| Length band of the conformal layer | Human texts in fitting | AI texts in fitting | Can label as AI | Can label as human |
|---|---|---|---|---|
| 150 to 249 | 223 | 147 | yes | yes |
| 250 to 499 | 1191 | 786 | yes | yes |
| 500 or more | 706 | 109 | yes | yes |

| Texts | Class | n | Likely AI | Likely human | Can't tell | No verdict | Wrong label | Own class ruled out |
|---|---|---|---|---|---|---|---|---|
| all lengths | human | 2023 | 7 | 1878 | 31 | 107 | 7/2023 = 0.3% (0.1% to 0.7%) | 20/1916 = 1.0% (0.6% to 1.6%) |
| all lengths | ai | 1130 | 1007 | 71 | 32 | 20 | 71/1130 = 6.3% (4.9% to 7.9%) | 75/1110 = 6.8% (5.4% to 8.4%) |
| 150 words or more | human | 1916 | 7 | 1878 | 31 | 0 | 7/1916 = 0.4% (0.1% to 0.8%) | 20/1916 = 1.0% (0.6% to 1.6%) |
| 150 words or more | ai | 1110 | 1007 | 71 | 32 | 0 | 71/1110 = 6.4% (5.0% to 8.0%) | 75/1110 = 6.8% (5.4% to 8.4%) |
| 150 to 249 | human | 240 | 0 | 231 | 9 | 0 | 0/240 = 0.0% (0.0% to 1.5%) | 0/240 = 0.0% (0.0% to 1.5%) |
| 150 to 249 | ai | 146 | 136 | 2 | 8 | 0 | 2/146 = 1.4% (0.2% to 4.9%) | 2/146 = 1.4% (0.2% to 4.9%) |
| 250 to 499 | human | 1049 | 7 | 1028 | 14 | 0 | 7/1049 = 0.7% (0.3% to 1.4%) | 17/1049 = 1.6% (0.9% to 2.6%) |
| 250 to 499 | ai | 838 | 751 | 67 | 20 | 0 | 67/838 = 8.0% (6.2% to 10.0%) | 67/838 = 8.0% (6.2% to 10.0%) |
| 500 or more | human | 627 | 0 | 619 | 8 | 0 | 0/627 = 0.0% (0.0% to 0.6%) | 3/627 = 0.5% (0.1% to 1.4%) |
| 500 or more | ai | 126 | 120 | 2 | 4 | 0 | 2/126 = 1.6% (0.2% to 5.6%) | 6/126 = 4.8% (1.8% to 10.1%) |

### Human texts that an AI edited

* **gede/improve-human:** flagged at the M1 threshold 45/50 = 90.0% (78.2% to 96.7%). Verdicts with enough words: 41 Likely AI, 4 Likely human, 5 Can't tell, 0 no verdict.
* **gede/rewrite-human:** flagged at the M1 threshold 49/50 = 98.0% (89.4% to 99.9%). Verdicts with enough words: 49 Likely AI, 1 Likely human, 0 Can't tell, 0 no verdict.
* **liang/chatgpt (simplify):** flagged at the M1 threshold 41/51 = 80.4% (66.9% to 90.2%). Verdicts with enough words: 6 Likely AI, 0 Likely human, 3 Can't tell, 0 no verdict.
* **liang/gpt-4 (polish):** flagged at the M1 threshold 38/39 = 97.4% (86.5% to 99.9%). Verdicts with enough words: 0 Likely AI, 0 Likely human, 0 Can't tell, 0 no verdict.

## Inputs

* calib_manifest: SHA 256 `4959ab6e0c633231a2b0ef723b62e19ca3f85b1787cad351c49cbb0d7a5f08c1`
* test_manifest: SHA 256 `651f05bfb034022f50b01af3e299c90fcdb1d220c2d2e39f11dafe80c9fcd0cb`
* scores: SHA 256 `fd39306bccf6b53c9c4bf56eff4e37b8f60b1b0314a58e208be7b032a5dc1066`
