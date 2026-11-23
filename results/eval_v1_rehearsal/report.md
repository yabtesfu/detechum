# Evaluation run (rehearsal on calib)

Plan: `eval_plan_v1`. Scorer: `gpttrace_v8s_1b_typography_off` (nakas/gpttrace-v8s-1b at revision `ac748e32ca8c`). Seed `20261119`. Intervals are 95% Clopper Pearson.

**This is a rehearsal.** Half of the groups of the calib split stand in for test. It checks the harness and is not a result.

## What this run covers

| Part of the plan | Status |
|---|---|
| M1, true positive rate at 1% false positive rate | computed |
| M2, calibration of the document probability | computed |
| M2, calibration of a sentence probability | not computed: the command gives no sentence probability |
| M3, nonnative release gate | passed |
| M4, paraphrase and humanizer attacks | not run: the corpora hold no attacked text |
| Verdict rules and rates | computed |
| Revision mode metrics (§3) | not run: revision mode does not exist |
| RAID submission (§5) | not run |

## Data

Fitted on 1298 human and 925 AI texts, so P(AI) assumes that mix. Measured on 2643 human and 961 AI texts.

| Source and class | Fitting | Measuring |
|---|---|---|
| ellipse/human | 937 | 2300 |
| liang/ai | 173 | 175 |
| liang/human | 197 | 196 |
| meld/ai | 735 | 773 |
| textsight/ai | 17 | 13 |
| textsight/human | 164 | 147 |

What these corpora can and cannot show:

* **The human and the AI texts are of different kinds.** Most human texts are school essays by English learners (ELLIPSE). Most AI texts are answers of 2026 chat models in eight other domains (MELD-eval). The false positive rate on essays and the true positive rate on chat model text are each valid for their kind of text. Any number that mixes the classes (AUROC, ECE, P(AI)) also reflects the difference in kind, which makes the classes easier to separate than authorship alone would.
* **The native human texts are pilot essays.** On test there are none, because the pilots may be used for fitting only. This rehearsal draws on calib, so here the ratio of M3 rests on those few essays.
* **Nonnative means two things here:** school essays by English learners in the United States, and passages of research papers whose authors work in countries where English is not the main language. The second is the label of the TextSight benchmark and is an inference from the affiliation.
* **No AI text is a student essay** except the 2023 GPT 3 essays of the pilots, which are in fitting only.
* **The scorer's author reports results on MELD-eval and on the TextSight benchmark.** Neither is listed as training data, but both may have guided the choice of the released model.
* **Human texts taken from RAID are left out of every rate above the last section.** The scorer was trained on RAID, so its scores on them say nothing about unseen human text.

## M1: true positive rate at a 1% false positive rate

The threshold `8.072` on the raw score flags 1.0% of the human texts used for fitting. It is applied unchanged below.

* **True positive rate:** 948/961 = 98.6% (97.7% to 99.3%)
* **Realized false positive rate (nominal 1.0%):** 6/2643 = 0.2% (0.1% to 0.5%)

Human texts by writer group. A stratum supports a claim of 1% or lower only with at least 300 texts.

| Writer group | Flagged | Enough texts for the claim |
|---|---|---|
| native | 1/80 = 1.2% (0.0% to 6.8%) | no |
| nonnative | 1/2400 = 0.0% (0.0% to 0.2%) | yes |
| unknown | 4/163 = 2.5% (0.7% to 6.2%) | no |

Human texts by length in words. A stratum supports a claim of 1% or lower only with at least 300 texts.

| Length in words | Flagged | Enough texts for the claim |
|---|---|---|
| under 100 | 2/29 = 6.9% (0.8% to 22.8%) | no |
| 100 to 149 | 2/124 = 1.6% (0.2% to 5.7%) | no |
| 150 to 249 | 0/400 = 0.0% (0.0% to 0.9%) | yes |
| 250 to 499 | 1/1323 = 0.1% (0.0% to 0.4%) | yes |
| 500 or more | 1/767 = 0.1% (0.0% to 0.7%) | yes |

Human texts by domain. A stratum supports a claim of 1% or lower only with at least 300 texts.

| Domain | Flagged | Enough texts for the claim |
|---|---|---|
| academic | 4/120 = 3.3% (0.9% to 8.3%) | no |
| encyclopedic | 0/30 = 0.0% (0.0% to 11.6%) | no |
| literature | 0/65 = 0.0% (0.0% to 5.5%) | no |
| student_essay | 2/2428 = 0.1% (0.0% to 0.3%) | yes |

Human texts by source. A stratum supports a claim of 1% or lower only with at least 300 texts.

| Source | Flagged | Enough texts for the claim |
|---|---|---|
| ellipse | 0/2300 = 0.0% (0.0% to 0.2%) | yes |
| liang | 6/196 = 3.1% (1.1% to 6.5%) | no |
| textsight | 0/147 = 0.0% (0.0% to 2.5%) | no |

AI texts by generator.

| Generator | Flagged |
|---|---|
| claude-haiku | 190/190 = 100.0% (98.1% to 100.0%) |
| claude-haiku-4-5 | 4/4 = 100.0% (39.8% to 100.0%) |
| claude-opus-5 | 3/3 = 100.0% (29.2% to 100.0%) |
| gemini-3-flash | 209/209 = 100.0% (98.3% to 100.0%) |
| gpt-3 | 86/87 = 98.9% (93.8% to 100.0%) |
| gpt-3 (prompt engineered) | 85/88 = 96.6% (90.4% to 99.3%) |
| gpt-4.1 | 2/2 = 100.0% (15.8% to 100.0%) |
| gpt-5.4-mini | 188/197 = 95.4% (91.5% to 97.9%) |
| gpt-oss-120b | 2/2 = 100.0% (15.8% to 100.0%) |
| qwen-3.6-plus | 177/177 = 100.0% (97.9% to 100.0%) |
| qwen-3.8-27b | 2/2 = 100.0% (15.8% to 100.0%) |

AI texts by length in words.

| Length in words | Flagged |
|---|---|
| under 100 | 13/14 = 92.9% (66.1% to 99.8%) |
| 100 to 149 | 131/134 = 97.8% (93.6% to 99.5%) |
| 150 to 249 | 111/111 = 100.0% (96.7% to 100.0%) |
| 250 to 499 | 485/486 = 99.8% (98.9% to 100.0%) |
| 500 or more | 208/216 = 96.3% (92.8% to 98.4%) |

AI texts by domain.

| Domain | Flagged |
|---|---|
| abstracts | 121/121 = 100.0% (97.0% to 100.0%) |
| academic | 148/152 = 97.4% (93.4% to 99.3%) |
| books | 93/100 = 93.0% (86.1% to 97.1%) |
| encyclopedic | 6/6 = 100.0% (54.1% to 100.0%) |
| news | 91/91 = 100.0% (96.0% to 100.0%) |
| poetry | 88/88 = 100.0% (95.9% to 100.0%) |
| recipes | 91/91 = 100.0% (96.0% to 100.0%) |
| reddit | 130/131 = 99.2% (95.8% to 100.0%) |
| reviews | 57/57 = 100.0% (93.7% to 100.0%) |
| student_essay | 30/30 = 100.0% (88.4% to 100.0%) |
| wiki | 93/94 = 98.9% (94.2% to 100.0%) |

## Secondary metrics

* AUROC: 0.9998
* At a nominal false positive rate of 0.1% (threshold `9.395`): true positive rate 928/961 = 96.6% (95.2% to 97.6%), realized false positive rate 1/2643 = 0.0% (0.0% to 0.2%)
* At a nominal false positive rate of 5.0% (threshold `4.723`): true positive rate 959/961 = 99.8% (99.3% to 100.0%), realized false positive rate 89/2643 = 3.4% (2.7% to 4.1%)
* Latency: not measured.

## M2: calibration of P(AI)

* **ECE (15 equal mass bins):** 0.0036. Target: at most 0.03. Met: yes.
* **Brier score:** 0.0048

![Reliability diagram](reliability.svg)

| Bin | n | Mean predicted P(AI) | Observed share of AI | 95% interval |
|---|---|---|---|---|
| 1 | 241 | 0.000 | 0.000 | 0.000 to 0.015 |
| 2 | 241 | 0.000 | 0.000 | 0.000 to 0.015 |
| 3 | 241 | 0.000 | 0.000 | 0.000 to 0.015 |
| 4 | 241 | 0.000 | 0.000 | 0.000 to 0.015 |
| 5 | 240 | 0.000 | 0.000 | 0.000 to 0.015 |
| 6 | 240 | 0.000 | 0.000 | 0.000 to 0.015 |
| 7 | 240 | 0.000 | 0.000 | 0.000 to 0.015 |
| 8 | 240 | 0.000 | 0.000 | 0.000 to 0.015 |
| 9 | 240 | 0.000 | 0.000 | 0.000 to 0.015 |
| 10 | 240 | 0.000 | 0.000 | 0.000 to 0.015 |
| 11 | 240 | 0.077 | 0.042 | 0.020 to 0.075 |
| 12 | 240 | 0.952 | 0.967 | 0.935 to 0.986 |
| 13 | 240 | 1.000 | 1.000 | 0.985 to 1.000 |
| 14 | 240 | 1.000 | 1.000 | 0.985 to 1.000 |
| 15 | 240 | 1.000 | 0.996 | 0.977 to 1.000 |

Per stratum. The target of 0.05 applies to strata with at least 300 texts. A stratum with one class only measures how close P(AI) is to 0 or 1 for that class.

| Dimension | Stratum | n | AI texts | ECE | Brier | Meets target |
|---|---|---|---|---|---|---|
| length | under 100 | 43 | 14 | 0.0172 | 0.0303 | n/a |
| length | 100 to 149 | 258 | 134 | 0.0416 | 0.0192 | n/a |
| length | 150 to 249 | 511 | 111 | 0.0095 | 0.0049 | yes |
| length | 250 to 499 | 1809 | 486 | 0.0008 | 0.0011 | yes |
| length | 500 or more | 983 | 216 | 0.0059 | 0.0069 | yes |
| domain | abstracts | 121 | 121 | 0.0000 | 0.0000 | n/a |
| domain | academic | 272 | 152 | 0.0354 | 0.0316 | n/a |
| domain | books | 100 | 100 | 0.0655 | 0.0482 | n/a |
| domain | encyclopedic | 36 | 6 | 0.0035 | 0.0004 | n/a |
| domain | literature | 65 | 0 | 0.0137 | 0.0036 | n/a |
| domain | news | 91 | 91 | 0.0000 | 0.0000 | n/a |
| domain | poetry | 88 | 88 | 0.0090 | 0.0027 | n/a |
| domain | recipes | 91 | 91 | 0.0064 | 0.0016 | n/a |
| domain | reddit | 131 | 131 | 0.0041 | 0.0022 | n/a |
| domain | reviews | 57 | 57 | 0.0000 | 0.0000 | n/a |
| domain | student_essay | 2458 | 30 | 0.0023 | 0.0009 | yes |
| domain | wiki | 94 | 94 | 0.0158 | 0.0079 | n/a |
| source | ellipse | 2300 | 0 | 0.0005 | 0.0001 | yes |
| source | liang | 371 | 175 | 0.0371 | 0.0287 | yes |
| source | meld | 773 | 773 | 0.0129 | 0.0081 | yes |
| source | textsight | 160 | 13 | 0.0071 | 0.0017 | n/a |
| writer_group | native | 80 | 0 | 0.0177 | 0.0120 | n/a |
| writer_group | nonnative | 2400 | 0 | 0.0019 | 0.0006 | yes |
| writer_group | unknown | 163 | 0 | 0.0922 | 0.0395 | n/a |
| generator | claude-haiku | 190 | 190 | 0.0000 | 0.0000 | n/a |
| generator | claude-haiku-4-5 | 4 | 4 | 0.0000 | 0.0000 | n/a |
| generator | claude-opus-5 | 3 | 3 | 0.0000 | 0.0000 | n/a |
| generator | gemini-3-flash | 209 | 209 | 0.0078 | 0.0020 | n/a |
| generator | gpt-3 | 87 | 87 | 0.0093 | 0.0037 | n/a |
| generator | gpt-3 (prompt engineered) | 88 | 88 | 0.0465 | 0.0231 | n/a |
| generator | gpt-4.1 | 2 | 2 | 0.0000 | 0.0000 | n/a |
| generator | gpt-5.4-mini | 197 | 197 | 0.0422 | 0.0296 | n/a |
| generator | gpt-oss-120b | 2 | 2 | 0.0000 | 0.0000 | n/a |
| generator | qwen-3.6-plus | 177 | 177 | 0.0000 | 0.0000 | n/a |
| generator | qwen-3.8-27b | 2 | 2 | 0.0625 | 0.0078 | n/a |

## M3: nonnative release gate

* Nonnative human texts flagged at the M1 threshold: 1/2400 = 0.0% (0.0% to 0.2%)
* Native human texts flagged at the M1 threshold: 1/80 = 1.2% (0.0% to 6.8%)
* Upper bound of the nonnative rate at most 2.0%: yes
* Ratio of the nonnative to the native rate is 0.03, at most 1.5: yes
* **Gate: passed.**

## Verdict rules and rates

A label needs 150 words, the whole 90.0% interval on one side of tau (`0.500`), and a conformal prediction set that holds that class alone.

| Length band of the conformal layer | Human texts in fitting | AI texts in fitting | Can label as AI | Can label as human |
|---|---|---|---|---|
| 150 to 249 | 254 | 122 | yes | yes |
| 250 to 499 | 581 | 460 | yes | yes |
| 500 or more | 313 | 199 | yes | yes |

| Texts | Class | n | Likely AI | Likely human | Can't tell | No verdict | Wrong label | Own class ruled out |
|---|---|---|---|---|---|---|---|---|
| all lengths | human | 2643 | 1 | 2471 | 18 | 153 | 1/2643 = 0.0% (0.0% to 0.2%) | 7/2490 = 0.3% (0.1% to 0.6%) |
| all lengths | ai | 961 | 770 | 3 | 40 | 148 | 3/961 = 0.3% (0.1% to 0.9%) | 43/813 = 5.3% (3.9% to 7.1%) |
| 150 words or more | human | 2490 | 1 | 2471 | 18 | 0 | 1/2490 = 0.0% (0.0% to 0.2%) | 7/2490 = 0.3% (0.1% to 0.6%) |
| 150 words or more | ai | 813 | 770 | 3 | 40 | 0 | 3/813 = 0.4% (0.1% to 1.1%) | 43/813 = 5.3% (3.9% to 7.1%) |
| 150 to 249 | human | 400 | 0 | 390 | 10 | 0 | 0/400 = 0.0% (0.0% to 0.9%) | 0/400 = 0.0% (0.0% to 0.9%) |
| 150 to 249 | ai | 111 | 106 | 0 | 5 | 0 | 0/111 = 0.0% (0.0% to 3.3%) | 5/111 = 4.5% (1.5% to 10.2%) |
| 250 to 499 | human | 1323 | 0 | 1320 | 3 | 0 | 0/1323 = 0.0% (0.0% to 0.3%) | 1/1323 = 0.1% (0.0% to 0.4%) |
| 250 to 499 | ai | 486 | 459 | 0 | 27 | 0 | 0/486 = 0.0% (0.0% to 0.8%) | 27/486 = 5.6% (3.7% to 8.0%) |
| 500 or more | human | 767 | 1 | 761 | 5 | 0 | 1/767 = 0.1% (0.0% to 0.7%) | 6/767 = 0.8% (0.3% to 1.7%) |
| 500 or more | ai | 216 | 205 | 3 | 8 | 0 | 3/216 = 1.4% (0.3% to 4.0%) | 11/216 = 5.1% (2.6% to 8.9%) |

The wrong label for a human text is "Likely AI written or AI edited", the false accusation. For an AI text it is "Likely human written". The targets for ruling out the own class are 1.0% for human and 5.0% for AI texts.

## Reported on their own

* **Human texts taken from RAID, on which the scorer was trained:** flagged at the M1 threshold 0/302 = 0.0% (0.0% to 1.2%). Of the 273 with enough words: 0 Likely AI, 273 Likely human, 0 Can't tell, 0 no verdict.
* **Human texts that an AI edited:** flagged at the M1 threshold 62/77 = 80.5% (69.9% to 88.7%). Of the 5 with enough words: 3 Likely AI, 2 Likely human, 0 Can't tell, 0 no verdict.

## Inputs

* calib_manifest: SHA 256 `45a59e2b45633c23a589cdcbb1a8a5ff41314712931b8dc801abe65732ce59d7`
* test_manifest: SHA 256 `bd3820e2738af1e18fc544f7f3ea96450fd416594f3376821fbbe3b3fcdee98f`
* scores: SHA 256 `36ddef54326a1c2b294f713f2bbdeed01b8dd41e1334b5976deb017a756b7bc9`
