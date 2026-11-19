# Nonnative test of the top 1 token rate (explanation_pilot_v1)

Data: Liang et al. 2023 repository at commit `1d05ed8242d4694a0ed7b73a79c52be8864470f9`. Language model: `Qwen/Qwen2.5-1.5B` at revision `8faed761d45a263340a0528343f099c05c9a4323`, bfloat16, first 512 tokens of each text.
Python 3.14.9, torch 2.15.0, transformers 5.23.0, arm64.

The top 1 token rate is the share of tokens that were the language model's single most likely next token.

* Outcome under the rule fixed before the run: **undecided**
* Threshold, the rate exceeded by 1% of native essays: 0.534
* Median rate of native essays: 0.421
* Probability that a TOEFL essay has a higher rate than a native essay of the same length: 0.793 (0.5 means no difference)
* AUROC of the rate alone, AI groups against all human groups: 0.871

| Group | Role | n | Median rate | Quartiles | Above the threshold (95% interval) |
|---|---|---|---|---|---|
| TOEFL_real_91 | human_nonnative | 91 | 0.440 | 0.405 to 0.486 | 4/91 = 4.4% (1.2 to 10.9) |
| HewlettStudentEssay_real_88 | human_native | 88 | 0.409 | 0.372 to 0.448 | 1/88 = 1.1% (0.0 to 6.2) |
| CollegeEssay_real_70 | human_native | 70 | 0.423 | 0.401 to 0.450 | 0/70 = 0.0% (0.0 to 5.1) |
| CS224N_real_145 | human_unknown | 145 | 0.488 | 0.455 to 0.515 | 22/145 = 15.2% (9.8 to 22.1) |
| TOEFL_gpt4polished_91 | ai_edited | 91 | 0.455 | 0.405 to 0.481 | 5/91 = 5.5% (1.8 to 12.4) |
| HewlettStudentEssay_GPTsimplify_88 | ai_edited | 88 | 0.467 | 0.440 to 0.496 | 5/88 = 5.7% (1.9 to 12.8) |
| CollegeEssay_gpt3_31 | ai | 31 | 0.623 | 0.599 to 0.652 | 30/31 = 96.8% (83.3 to 99.9) |
| CollegeEssay_gpt3PromptEng_31 | ai | 31 | 0.457 | 0.432 to 0.487 | 3/31 = 9.7% (2.0 to 25.8) |
| CS224N_gpt3_145 | ai | 145 | 0.602 | 0.569 to 0.635 | 127/145 = 87.6% (81.1 to 92.5) |
| CS224N_gpt3PromptEng_145 | ai | 145 | 0.518 | 0.481 to 0.556 | 57/145 = 39.3% (31.3 to 47.8) |
| control/Hewlett_truncated_to_TOEFL_lengths | human_native_length_matched | 91 | 0.376 | 0.346 to 0.418 | 1/91 = 1.1% (0.0 to 6.0) |
