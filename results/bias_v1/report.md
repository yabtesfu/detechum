# Nonnative writer false positive experiment (bias_v1)

Data: Liang et al. 2023 repository at commit `1d05ed8242d4694a0ed7b73a79c52be8864470f9`. Python 3.14.9, torch 2.15.0, transformers 5.23.0, arm64.
Flag rates are shown with 95% Clopper Pearson intervals. A text is flagged when its score is above the threshold.

## binoculars_style_qwen2.5_1.5b_pair_unvalidated

AUROC, AI groups against all human groups: 0.831

| Group | Role | Median words | Flagged at native_calibrated_1pct (-0.958) |
|---|---|---|---|
| TOEFL_real_91 | human_nonnative | 104 | 48/91 = 52.7% (42.0 to 63.3) |
| HewlettStudentEssay_real_88 | human_native | 378 | 0/88 = 0.0% (0.0 to 4.1) |
| CollegeEssay_real_70 | human_native | 632 | 1/70 = 1.4% (0.0 to 7.7) |
| CS224N_real_145 | human_unknown | 165 | 26/145 = 17.9% (12.1 to 25.2) |
| TOEFL_gpt4polished_91 | ai_edited | 89 | 24/91 = 26.4% (17.7 to 36.7) |
| HewlettStudentEssay_GPTsimplify_88 | ai_edited | 109 | 50/88 = 56.8% (45.8 to 67.3) |
| CollegeEssay_gpt3_31 | ai | 261 | 18/31 = 58.1% (39.1 to 75.5) |
| CollegeEssay_gpt3PromptEng_31 | ai | 238 | 2/31 = 6.5% (0.8 to 21.4) |
| CS224N_gpt3_145 | ai | 120 | 136/145 = 93.8% (88.5 to 97.1) |
| CS224N_gpt3PromptEng_145 | ai | 111 | 97/145 = 66.9% (58.6 to 74.5) |
| control/Hewlett_truncated_to_TOEFL_lengths | human_native_length_matched | 104 | 1/91 = 1.1% (0.0 to 6.0) |

## gpttrace_v8s_1b_typography_off

AUROC, AI groups against all human groups: 0.997

| Group | Role | Median words | Flagged at native_calibrated_1pct (7.945) | Flagged at vendor_9.3 (9.300) | Flagged at raw_0 (0.000) |
|---|---|---|---|---|---|
| TOEFL_real_91 | human_nonnative | 104 | 2/91 = 2.2% (0.3 to 7.7) | 0/91 = 0.0% (0.0 to 4.0) | 43/91 = 47.3% (36.7 to 58.0) |
| HewlettStudentEssay_real_88 | human_native | 378 | 0/88 = 0.0% (0.0 to 4.1) | 0/88 = 0.0% (0.0 to 4.1) | 0/88 = 0.0% (0.0 to 4.1) |
| CollegeEssay_real_70 | human_native | 632 | 1/70 = 1.4% (0.0 to 7.7) | 0/70 = 0.0% (0.0 to 5.1) | 20/70 = 28.6% (18.4 to 40.6) |
| CS224N_real_145 | human_unknown | 165 | 19/145 = 13.1% (8.1 to 19.7) | 2/145 = 1.4% (0.2 to 4.9) | 136/145 = 93.8% (88.5 to 97.1) |
| TOEFL_gpt4polished_91 | ai_edited | 89 | 83/91 = 91.2% (83.4 to 96.1) | 75/91 = 82.4% (73.0 to 89.6) | 91/91 = 100.0% (96.0 to 100.0) |
| HewlettStudentEssay_GPTsimplify_88 | ai_edited | 109 | 57/88 = 64.8% (53.9 to 74.7) | 40/88 = 45.5% (34.8 to 56.4) | 87/88 = 98.9% (93.8 to 100.0) |
| CollegeEssay_gpt3_31 | ai | 261 | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) |
| CollegeEssay_gpt3PromptEng_31 | ai | 238 | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) |
| CS224N_gpt3_145 | ai | 120 | 144/145 = 99.3% (96.2 to 100.0) | 140/145 = 96.6% (92.1 to 98.9) | 145/145 = 100.0% (97.5 to 100.0) |
| CS224N_gpt3PromptEng_145 | ai | 111 | 140/145 = 96.6% (92.1 to 98.9) | 129/145 = 89.0% (82.7 to 93.6) | 145/145 = 100.0% (97.5 to 100.0) |
| control/Hewlett_truncated_to_TOEFL_lengths | human_native_length_matched | 104 | 1/91 = 1.1% (0.0 to 6.0) | 0/91 = 0.0% (0.0 to 4.0) | 6/91 = 6.6% (2.5 to 13.8) |

## gpttrace_v8s_1b_typography_on

AUROC, AI groups against all human groups: 0.996

| Group | Role | Median words | Flagged at native_calibrated_1pct (8.091) | Flagged at vendor_9.3 (9.300) | Flagged at raw_0 (0.000) |
|---|---|---|---|---|---|
| TOEFL_real_91 | human_nonnative | 104 | 1/91 = 1.1% (0.0 to 6.0) | 0/91 = 0.0% (0.0 to 4.0) | 42/91 = 46.2% (35.6 to 56.9) |
| HewlettStudentEssay_real_88 | human_native | 378 | 0/88 = 0.0% (0.0 to 4.1) | 0/88 = 0.0% (0.0 to 4.1) | 0/88 = 0.0% (0.0 to 4.1) |
| CollegeEssay_real_70 | human_native | 632 | 1/70 = 1.4% (0.0 to 7.7) | 0/70 = 0.0% (0.0 to 5.1) | 23/70 = 32.9% (22.1 to 45.1) |
| CS224N_real_145 | human_unknown | 165 | 15/145 = 10.3% (5.9 to 16.5) | 3/145 = 2.1% (0.4 to 5.9) | 136/145 = 93.8% (88.5 to 97.1) |
| TOEFL_gpt4polished_91 | ai_edited | 89 | 83/91 = 91.2% (83.4 to 96.1) | 75/91 = 82.4% (73.0 to 89.6) | 91/91 = 100.0% (96.0 to 100.0) |
| HewlettStudentEssay_GPTsimplify_88 | ai_edited | 109 | 55/88 = 62.5% (51.5 to 72.6) | 40/88 = 45.5% (34.8 to 56.4) | 87/88 = 98.9% (93.8 to 100.0) |
| CollegeEssay_gpt3_31 | ai | 261 | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) |
| CollegeEssay_gpt3PromptEng_31 | ai | 238 | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) | 31/31 = 100.0% (88.8 to 100.0) |
| CS224N_gpt3_145 | ai | 120 | 143/145 = 98.6% (95.1 to 99.8) | 140/145 = 96.6% (92.1 to 98.9) | 145/145 = 100.0% (97.5 to 100.0) |
| CS224N_gpt3PromptEng_145 | ai | 111 | 140/145 = 96.6% (92.1 to 98.9) | 129/145 = 89.0% (82.7 to 93.6) | 145/145 = 100.0% (97.5 to 100.0) |
| control/Hewlett_truncated_to_TOEFL_lengths | human_native_length_matched | 104 | 1/91 = 1.1% (0.0 to 6.0) | 0/91 = 0.0% (0.0 to 4.0) | 6/91 = 6.6% (2.5 to 13.8) |
