# Phase 1: Trained detectors, paraphrase attacks, watermarking, and nonnative writer bias

Detechum research notes. Every number below was copied from the primary source named in the citation. Where I could not read the primary source, or where a number is my own arithmetic on released data, I say so explicitly. **UNVERIFIED** marks anything I could not confirm from the primary text.

## 0. Sources and versions actually read

| Paper | Version read | How accessed |
|---|---|---|
| Verma et al., Ghostbuster (NAACL 2024) | arXiv 2305.15047**v3** (5 Apr 2024), full PDF | arxiv.org PDF, text extracted locally |
| Solaiman et al. 2019, Release Strategies | arXiv 1908.09203 (Nov 2019 report), full PDF | arxiv.org PDF |
| Guo et al. 2023, HC3 | arXiv 2301.07597, ar5iv HTML rendering (version number not shown on the page) | ar5iv.labs.arxiv.org |
| Dugan et al. 2024, RAID (ACL 2024) | arXiv 2405.07940**v2** (10 Jun 2024), full PDF | arxiv.org PDF |
| Krishna et al. 2023, DIPPER (NeurIPS 2023) | arXiv 2303.13408**v2** (18 Oct 2023), full PDF | arxiv.org PDF |
| Kirchenbauer et al. 2023, A Watermark for LLMs (ICML 2023) | arXiv 2301.10226**v4** (1 May 2024), full PDF | arxiv.org PDF |
| Kirchenbauer et al. 2023, On the Reliability of Watermarks | arXiv 2306.04634, ar5iv HTML rendering (version not shown) | ar5iv.labs.arxiv.org |
| Dathathri et al. 2024, SynthID Text (Nature 634) | Full text from PubMed Central (PMC11499265) + Supplementary Information PDF | pmc.ncbi.nlm.nih.gov; static content.springer.com |
| Liang et al. 2023, GPT detectors biased (Patterns 4(7):100779) | arXiv 2304.02819**v3** (10 Jul 2023), full PDF; plus the authors' released score files on GitHub | arxiv.org PDF; github.com/Weixin Liang/ChatGPT Detector Bias |
| Jiang, Hao, Fauss & Li 2024 (Computers & Education 217, 105070) | **Not read.** Paywalled (ScienceDirect returned HTTP 403). Only metadata (Crossref) and secondary descriptions | see §5.3 |
| Al Ali, Helcl & Libovický 2026, Czech replication (arXiv 2602.05769) | arXiv HTML v1, full | arxiv.org/html |
| Park, Jeong & Kim 2026, Style as a Confound (arXiv 2608.26710) | arXiv HTML v1 (27 Aug 2026), full | arxiv.org/html |
| Zu, Fauss & Li 2025 (AIME Con) | Full PDF (used only as a secondary description of Jiang et al. 2024) | aclanthology.org |

Note on Ghostbuster section numbers: in arXiv v3 the nonnative experiment is **Section 7.3**, while other passages of the same paper say "Section 9" (an internal inconsistency in the paper). I cite 7.3, Table 3 and Appendix B / Table 6.

---

## 1. Ghostbuster (Verma, Fleisig, Tomlin & Klein, NAACL 2024)

Source: [arXiv 2305.15047](https://arxiv.org/abs/2305.15047) (v3).

### Signal
* Each document goes through "a series of language models that are weaker than the target model": "a unigram fertility model, a Kneser Ney trigram model, and two early GPT 3 models (ada and davinci, without instruction tuning)" to get per token probabilities ([Verma et al. 2024, §4.1](https://arxiv.org/abs/2305.15047)).
* A structured search combines these probability vectors with 13 vector and scalar operations (add, sub, mul, div, >, <; max, min, avg, avg top25, len, L2, var) ([Verma et al. 2024, Table 1](https://arxiv.org/abs/2305.15047)). The search runs to depth 3, which gives "2534 available features to select from" ([Verma et al. 2024, App. C](https://arxiv.org/abs/2305.15047)). Forward feature selection then picks the features to use. One example feature is `var(unigram_probs > ada_probs - davinci_probs)` ([§4.2](https://arxiv.org/abs/2305.15047)).
* The classifier is "a logistic regression classifier trained with L2 regularization and setting C = 1". It takes the selected features plus seven handcrafted features (word length, largest token probabilities) ([§4.3, App. D](https://arxiv.org/abs/2305.15047)).
* Ghostbuster "does not require access to token probabilities from the target model", so it can be used on black box models ([Abstract](https://arxiv.org/abs/2305.15047)).

### Compute cost
* **Model calls per text:** two GPT 3 API scoring passes (ada and davinci), plus two local n gram models trained on Brown Corpus counts ([§4.1, App. C](https://arxiv.org/abs/2305.15047)). The paper does not give parameter counts for ada or davinci. **Not from the paper, UNVERIFIED here:** OpenAI has since retired the original GPT 3 base models, so reproducing Ghostbuster exactly may require substitute scoring models. The ablation shows that a version without davinci "nearly matched the performance of our full model" ([Table 4 caption](https://arxiv.org/abs/2305.15047)).
* **Training data:** for each domain, "1,000 human authored documents and the 1,000 ChatGPT generated documents that used the same prompt were split into train, validation, and test sets" ([Table 5 caption](https://arxiv.org/abs/2305.15047)). The three domains are student essays (IvyPanda), news (Reuters 50 to 50) and creative writing (r/WritingPrompts). All training data was generated with `gpt-3.5-turbo` ([§3](https://arxiv.org/abs/2305.15047)).
* **Inference classifier:** logistic regression, so it is cheap once the probabilities are computed.

### Headline numbers (metric: F1, unless noted)
The paper reports **F1 and accuracy only. It does not report AUROC or TPR at a fixed FPR**, so a TPR@1%FPR figure is "not reported in the paper".

| Setting | Ghostbuster | GPTZero | DetectGPT | RoBERTa (roberta large baseline) | Perplexity only | Source |
|---|---|---|---|---|---|---|
| In domain, all domains | 99.0 | 93.1 | 57.4 | 98.1 | 81.5 | [Table 2](https://arxiv.org/abs/2305.15047) |
| Out of domain News | 97.9 | 91.5 | 56.6 | 88.3 | 71.9 | [Table 2](https://arxiv.org/abs/2305.15047) |
| Out of domain Creative Writing | 95.3 | 93.1 | 48.2 | 95.7 | 49.0 | [Table 2](https://arxiv.org/abs/2305.15047) |
| Out of domain Student Essays | 97.7 | 83.9 | 67.3 | 71.4 | 93.4 | [Table 2](https://arxiv.org/abs/2305.15047) |
| Prompt variants | 99.5 | 96.1 | 70.8 | 97.4 | 85.3 | [Table 3](https://arxiv.org/abs/2305.15047) |
| Claude generated text (unseen model) | 92.2 | 75.6 | 64.2 | 87.8 | 84.1 | [Table 3](https://arxiv.org/abs/2305.15047) |

* "Ghostbuster achieved 97.0 F1 averaged across all [out of domain] conditions, outperforming DetectGPT by 39.6 F1 and GPTZero by 7.5 F1" ([§6.2](https://arxiv.org/abs/2305.15047)).
* DetectGPT and GPTZero were given oracle thresholding in the domain, prompt and model experiments ([§5, Table 3 caption](https://arxiv.org/abs/2305.15047)), which favours those baselines.
* Human baseline: average accuracy 59% for six annotators. Among the 17 web participants who made at least 25 guesses it was "58.1 ± 11.1%" ([§5](https://arxiv.org/abs/2305.15047)).
* Length: "Ghostbuster may be unreliable for documents with ≤ 100 tokens, and its performance levels off with ≥ 500 tokens" ([Figure 4 caption](https://arxiv.org/abs/2305.15047)).

### Paraphrase robustness (as reported)
* Ghostbuster was tested with local perturbations, plus sentence level and paragraph level paraphrase using `tuner007/pegasus_paraphrase`. The results are plotted only, with no numeric table ([§7.2, Figure 3](https://arxiv.org/abs/2305.15047)). The text says: "Most global edits did not significantly affect model performance … However, repeated calls to a paraphrasing model will lead to worse results" ([§7.2](https://arxiv.org/abs/2305.15047)).
* Commercial evader Undetectable.ai, on 100 AI essays per domain: "recall degraded from 99% to 62%" ([§7.2, App. C](https://arxiv.org/abs/2305.15047)).
* **The paper does not test DIPPER.** It says: "we focus primarily on the setting in which entire paragraphs or documents were generated by language models, leaving adversarial prompting and paraphrasing attacks as an avenue for future work" ([§2](https://arxiv.org/abs/2305.15047)).

### Nonnative writer evaluation (explicitly reported)
Ghostbuster tested on three human only nonnative sets, with "accuracy (equivalent to precision, since there is no corresponding AI generated text)" ([Table 3 caption](https://arxiv.org/abs/2305.15047)). The datasets ([Table 6, App. B](https://arxiv.org/abs/2305.15047)):
* **Lang8:** 1,000 documents, median 77 words. Online language learner forum, "particularly from Japan".
* **TOEFL11** (Blanchard et al. 2013): 1,000 documents, median 315 words. 11 L1s, evenly split.
* **TOEFL from Liang et al. 2023:** 91 documents, median 104 words. Drawn "from a Chinese educational forum".

| Detector | Lang8 acc. | TOEFL11 acc. | TOEFL 91 (Liang) acc. |
|---|---|---|---|
| Perplexity only | 98.6 | 98.1 | 13.2 |
| DetectGPT | 98.6 | 100.0 | 63.7 |
| GPTZero | 99.2 | 100.0 | 92.3 |
| RoBERTa | 98.6 | 98.1 | 96.7 |
| **Ghostbuster** | **95.5** | **99.9** | **74.7** |

Source: [Verma et al. 2024, Table 3](https://arxiv.org/abs/2305.15047). These sets contain only human text, so the implied false positive rate is 100 minus accuracy. For Ghostbuster that gives about 4.5% (Lang8), 0.1% (TOEFL11) and 25.3% (TOEFL 91). That is my arithmetic, not a number stated in the paper. DetectGPT and GPTZero did **not** get oracle thresholding here: "we did not perform oracle thresholding on the precision only evaluation … since it would trivially result in perfect accuracy" ([§5](https://arxiv.org/abs/2305.15047)).

The authors' interpretation: "all tested models had over 95% accuracy, but experienced significant performance drops on the 91 TOEFL essays from previous work … the performance drop on the 91 TOEFL essays and on Lang8 can be largely, though not entirely, attributed to the challenge of classifying shorter documents" ([§7.3](https://arxiv.org/abs/2305.15047)).

Key point for Detechum: on the original Liang TOEFL 91 set, **Ghostbuster (74.7%) did worse than both the fine tuned RoBERTa baseline (96.7%) and GPTZero (92.3%)**. On full length TOEFL11 essays it was near perfect (99.9%) ([Table 3](https://arxiv.org/abs/2305.15047)).

Ethics statement: "we strongly discourage incorporation of Ghostbuster into any systems that automatically penalize students or other writers". The paper also lists "text written by nonnative speakers of English" as a case where incorrect predictions "may be particularly likely" ([§9](https://arxiv.org/abs/2305.15047)).

---

## 2. Fine tuned RoBERTa detectors

### 2a. OpenAI GPT 2 output detector (Solaiman et al. 2019)

Source: [arXiv 1908.09203](https://arxiv.org/abs/1908.09203), §4.3 "Detecting Synthetic Text" (printed pp. 10 to 17).

**Signal.** A sequence classifier fine tuned from RoBERTa: "basing a sequence classifier on RoBERTaBASE (125 million parameters) and RoBERTaLARGE (356 million parameters)" ([Solaiman et al. 2019, §4.3](https://arxiv.org/abs/1908.09203)). It is trained to tell GPT 2 outputs from WebText.

**Compute cost.**
* One forward pass of a 125M or 356M parameter encoder per text ([§4.3](https://arxiv.org/abs/1908.09203)).
* Training data is the released GPT 2 output dataset (outputs from 124M, 355M, 774M and 1.5B models) together with WebText ([§1, §4.3](https://arxiv.org/abs/1908.09203)). **UNVERIFIED:** the exact training set size is not stated in the section I read.
* The report notes that "training with random length sequences" improves accuracy on short inputs ([§4.3](https://arxiv.org/abs/1908.09203)).

**Headline numbers (metric: accuracy on a balanced set).**
* "Our classifier is able to detect 1.5 billion parameter GPT 2 generated text with approximately 95% accuracy" ([§4.3](https://arxiv.org/abs/1908.09203)).
* The evaluation set was "510 token test examples comprised of 5,000 samples from the WebText dataset and 5,000 samples generated by a GPT 2 model" ([Figure 1 caption, §4.3](https://arxiv.org/abs/1908.09203)).
* Accuracy depends on sampling method: "Nucleus sampling outputs proved most difficult to correctly classify, but a detector trained using nucleus sampling transfers well across other sampling methods" ([§4.3, Figure 1](https://arxiv.org/abs/1908.09203)).
* Length: accuracy is "roughly surpassing 90% accuracy at 100 RoBERTa tokens (which generally translates to 70 English words)" ([Figure 2 caption](https://arxiv.org/abs/1908.09203)).
* For comparison, the simpler TF IDF logistic regression baseline scored "88% at 124 million parameters to 74% at 1.5 billion parameters" at temperature 1 ([§4.3](https://arxiv.org/abs/1908.09203)).
* No AUROC or TPR@FPR is reported: "not reported in the paper".

**Paraphrase robustness:** not reported in the paper. The report does note that fine tuning GPT 2 on Amazon reviews drops the *zero shot* baseline's accuracy to 76% ([§4.3](https://arxiv.org/abs/1908.09203)).

**Nonnative writer bias:** not reported in the paper. See §5.1 below: this detector, served as the "OpenAI" Hugging Face Space, is one of Liang et al.'s seven detectors.

### 2b. HC3 RoBERTa detector (Guo et al. 2023)

Source: [arXiv 2301.07597](https://arxiv.org/abs/2301.07597), read via [ar5iv](https://ar5iv.labs.arxiv.org/html/2301.07597).

**Signal.** A fine tuned `roberta-base` classifier for English and `hfl/chinese-roberta-wwm-ext` for Chinese. There are two variants:
* "RoBERTa single", which takes the answer text only.
* "RoBERTa QA", which takes the question and answer joined as a text pair ([Guo et al. 2023, §5.1 to 5.2](https://arxiv.org/abs/2301.07597)).
Training used AdamW, "batch size to 32 and learning rate to 5e 5", "1 epoch for English, and 2 epochs for Chinese" ([§5.2](https://arxiv.org/abs/2301.07597)).

**Compute cost / training data.**
* One forward pass of roberta base per text. **UNVERIFIED:** the paper does not state a parameter count. The roberta base model card is commonly given as ~125M, consistent with Solaiman et al.'s "RoBERTaBASE (125 million parameters)".
* HC3 English: "24,322 questions, 58,546 human answers and 26,903 ChatGPT answers". HC3 Chinese: "12,853 questions, 22,259 human answers and 17,522 ChatGPT answers" ([§2.3](https://arxiv.org/abs/2301.07597)).
* The released checkpoint used in RAID is `Hello-SimpleAI/chatgpt-detector-roberta` ([Dugan et al. 2024, App. F.1](https://arxiv.org/abs/2405.07940)).

**Headline numbers (metric: F1 %, in distribution HC3 test splits).** These are from Table 4, RoBERTa trained on raw full.

| Test → | EN raw full | EN raw sent | EN raw mix | EN filtered full | EN filtered sent | EN filtered mix | EN avg | ZH avg |
|---|---|---|---|---|---|---|---|---|
| RoBERTa raw full | 99.82 | 81.89 | 84.67 | 99.72 | 81.00 | 84.07 | 88.53 | 89.32 |
| RoBERTa raw mix | 99.44 | 98.31 | 98.47 | 99.32 | 98.37 | 98.51 | 98.74 | 96.35 |
| GLTR Test 2 raw full | 98.26 | 71.58 | 76.15 | 98.22 | 70.19 | 75.23 | 81.61 | 61.74 |

Source: [Guo et al. 2023, Table 4](https://arxiv.org/abs/2301.07597). The QA style model on English "averages 97.48% F1 scores and surpasses single model by 5.63%" ([§5.4.5, Table 6](https://arxiv.org/abs/2301.07597)). **The paper reports no AUROC and no TPR@FPR**, only F1. A TPR@1%FPR figure is "not reported in the paper".

**Robustness as reported.** The only robustness tested is granularity (full answer, sentence, mix) and "indicating word" filtering. A raw full model tested on sentences drops to 81.89 F1 (EN) ([Table 4/5](https://arxiv.org/abs/2301.07597)). There is **no paraphrase or adversarial evaluation**: "not reported in the paper". The limitations section warns: "using special prompts such as 'Pretending you are Shakespeare…' can generate content that bypasses our detectors" ([§7](https://arxiv.org/abs/2301.07597)).

**Nonnative writer bias:** not reported in the paper.

### 2c. What RAID found for RoBERTa detectors (Dugan et al., ACL 2024)

Source: [arXiv 2405.07940](https://arxiv.org/abs/2405.07940) (v2). Detectors used:
* RoBERTa Base (GPT2) and RoBERTa Large (GPT2), which are the Solaiman et al. detector.
* RoBERTa Base (ChatGPT), which is the Guo et al. HC3 detector `Hello-SimpleAI/chatgpt-detector-roberta`.
All were used off the shelf, not retrained ([§5.1, App. F.1](https://arxiv.org/abs/2405.07940)). RAID has "over 6 million generations spanning 11 models, 8 domains, 11 adversarial attacks and 4 decoding strategies" ([Abstract](https://arxiv.org/abs/2405.07940)). Main metric: **accuracy (TPR) at FPR = 5%**, with thresholds calibrated per domain ([§5.2, App. C](https://arxiv.org/abs/2405.07940)). RAID does **not** tabulate TPR@1%FPR. Only Figure 4 plots accuracy against FPR, and it says "few detectors can operate at FPR<1%" ([Figure 4 caption](https://arxiv.org/abs/2405.07940)).

* **Naive threshold FPRs on RAID human text** ([Table 4](https://arxiv.org/abs/2405.07940)):
  * R B GPT2: 8.71% at τ=0.25, 6.59% at τ=0.5, 5.18% at τ=0.75, 3.38% at τ=0.95.
  * R L GPT2: 6.14%, 2.91%, 1.46%, 0.25% at the same thresholds.
  * **R B CGPT (HC3): 21.6%, 15.8%, 15.1%, 10.4%.**
* **Overall accuracy at FPR=5%, nonadversarial, total across generators:** R B GPT2 59.1, R L GPT2 56.7, R B CGPT 44.8 ([Table 15](https://arxiv.org/abs/2405.07940)). For comparison, Binoculars scores 79.6 and Originality 85.0 ([Table 15](https://arxiv.org/abs/2405.07940)).
* **Generator dependence:**
  * R L GPT2 gets 96.3 on GPT 2 text but 33.8 on GPT 4 text ([Table 15](https://arxiv.org/abs/2405.07940)).
  * "RoBERTa GPT2 achieves 95+% accuracy on five domains generated by GPT2, but it rarely achieves beyond 60% accuracy on text of the same domain from different models" ([§6 Finding 5, Figure 6](https://arxiv.org/abs/2405.07940)).
  * R B CGPT gets 66.1 on ChatGPT text, 17.7 on nonchat Mistral and 17.8 on nonchat MPT ([Table 15](https://arxiv.org/abs/2405.07940)).
* **Repetition penalty, open source nonchat models, sampling with penalty:** R B GPT2 26.2, R L GPT2 19.5, R B CGPT 39.3. For closed source chat models with sampling and penalty, R B CGPT falls to 1.7 ([Table 5](https://arxiv.org/abs/2405.07940)).
* **Paraphrase (RAID's paraphrase attack is DIPPER 11B, lexical 60 / order 0, applied to 100% of outputs)** ([App. E.4, Table 11](https://arxiv.org/abs/2405.07940)). Accuracy at FPR=5% before and after ([Table 16](https://arxiv.org/abs/2405.07940)):
  * RoB B GPT2: 59.1 → 68.9.
  * RoB L GPT2: 56.7 → 72.9 (+16.2) ([Table 6](https://arxiv.org/abs/2405.07940)).
  * RoB B CGPT: 44.8 → 49.2.
  * So paraphrase *raised* RoBERTa GPT2 accuracy. The authors' explanation: "GPT2, RoBERTa, T5, and BERT are contemporaneous models trained on similar data, leading us to believe that detectors benefit from adversarial attacks that inadvertently modify text to be more similar to their training data" ([§6 Finding 6](https://arxiv.org/abs/2405.07940)).
* **Other attacks that hurt RoBERTa** (accuracy at FPR=5%, [Table 16](https://arxiv.org/abs/2405.07940)):
  * Homoglyph: RoB B GPT2 7.6, RoB L GPT2 21.3, RoB B CGPT 0.0.
  * Upper/lower swap: 18.8, 19.3, 31.7.
  * Whitespace: RoB B CGPT 0.1.
  * Zero width space: RoB B CGPT 0.0.
* **Domain level FPR at a single global threshold** (R B GPT2 / R L GPT2): Poetry 15.4% / 15.4%, Recipes 7.3% / 5.1%, against a 5.0% total ([Table 8](https://arxiv.org/abs/2405.07940)).
* **Nonnative bias:** RAID did not evaluate it. Its ethics statement cites Liang et al. and says "Our results also support this and suggest that the problem of false positives remains unsolved" ([Ethics Statement](https://arxiv.org/abs/2405.07940)).

---

## 3. DIPPER paraphrase attack and retrieval defense (Krishna et al., NeurIPS 2023)

Source: [arXiv 2303.13408](https://arxiv.org/abs/2303.13408) (v2).

### The attack (signal / compute)
* DIPPER is "a 11B parameter paraphrase generation model" that can "paraphrase paragraphs, condition on surrounding context, and control lexical diversity and content reordering" ([Abstract](https://arxiv.org/abs/2303.13408)). It was initialised from "the T5 XXL 1.1 checkpoint" ([App. F.1](https://arxiv.org/abs/2303.13408)).
* Training data: the PAR3 dataset (multiple English translations of non English novels, aligned by paragraph). "Our final dataset contains 6.3M paraphrase pairs" ([§3](https://arxiv.org/abs/2303.13408)). "Training was done on 64 cloud TPUv3 chips, and took 6 to 12 hours" ([App. F.1](https://arxiv.org/abs/2303.13408)).
* Control codes L (lexical) and O (order) take values in {0, 20, 40, 60, 80, 100}. "L = 20 roughly corresponds to a 20% lexical modification" ([§3](https://arxiv.org/abs/2303.13408)). At inference the paper uses nucleus sampling with p = 0.75 ([App. F.1](https://arxiv.org/abs/2303.13408)). It paraphrases "three sentences at a time" and draws "only … each generation once" ([§4.2](https://arxiv.org/abs/2303.13408)).
* Metric: "we fix the FPR to 1% for all detection algorithms … and adjust the detection threshold accordingly while reporting detection accuracies" ([§4.1](https://arxiv.org/abs/2303.13408)). "Sim" is the share of paraphrases with P SP above the 0.76 human paraphrase average ([§4.1](https://arxiv.org/abs/2303.13408)).
* Generations are 300 tokens long, from GPT2 XL (1.5B), OPT 13B and text davinci 003 ([§4.2](https://arxiv.org/abs/2303.13408)).
* The watermark used is Kirchenbauer et al. with default γ = 0.5 and δ = 2 ([App. E](https://arxiv.org/abs/2303.13408)).

### Exact detection drops at 1% FPR: open ended generation, Wikipedia prompts ([Krishna et al. 2023, Table 1](https://arxiv.org/abs/2303.13408))

| Generator / condition | Sim | Watermark | DetectGPT | OpenAI classifier | GPTZero | RankGen |
|---|---|---|---|---|---|---|
| GPT2 1.5B, original | n/a | 100.0 | 70.3 | 21.6 | 13.9 | 13.5 |
| + DIPPER 20L | 99.2 | 97.1 | 28.7 | 19.2 | 9.1 | 15.8 |
| + DIPPER 40L | 98.4 | 85.8 | 15.4 | 17.8 | 7.3 | 18.0 |
| + DIPPER 60L | 96.9 | 68.9 | 8.7 | 13.3 | 7.1 | 19.8 |
| + DIPPER 60L, 60O | 94.3 | **57.2** | **4.6** | 14.8 | **1.2** | 28.5 |
| OPT 13B, original | n/a | 99.9 | 14.3 | 11.3 | 8.7 | 3.2 |
| + DIPPER 60L, 60O | 94.6 | 52.8 | 0.3 | 10.0 | 1.0 | 13.5 |
| GPT 3.5 davinci 003, original | n/a | n/a | 26.5* | 30.0 | 7.1 | 1.2 |
| + DIPPER 60L, 60O | 88.4 | n/a | 4.5* | **15.6** | 1.8 | 7.3 |
| Human text (FPR) | n/a | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

\*The footnote reads: "GPT3.5 DetectGPT scores computed using 200 samples at 20% FPR as it scores 0% at a 1% FPR" ([Table 1 caption](https://arxiv.org/abs/2303.13408)). Watermarking was not applied to GPT 3.5 because the API does not expose logits (the table cell is blank).

Headline sentences: "DIPPER drops detection accuracy of DetectGPT from 70.3% to 4.6% (at a constant false positive rate of 1%)" ([Abstract](https://arxiv.org/abs/2303.13408)). "paraphrasing GPT2 XL open ended generations reduces watermark detection accuracy from 100% to 57.2% … for GPT 3.5 … reduces OpenAI's text classifier accuracy from 30.0% to 15.6%" ([§4.3](https://arxiv.org/abs/2303.13408)). "Overall, we find that watermarking is the most resilient detector to paraphrasing" ([§4.3](https://arxiv.org/abs/2303.13408)).

**Long form QA (ELI5, 300 tokens), 1% FPR** ([Figure 3, the table style figure on p.6](https://arxiv.org/abs/2303.13408)):
* GPT2 1.5B: watermark 100.0 → 55.8, DetectGPT 74.9 → 7.6, OpenAI 59.2 → 32.7, at 60L,60O.
* OPT 13B: 100.0 → 51.4, 29.8 → 1.5, 33.5 → 21.6.
* GPT 3.5: DetectGPT 67.0* → 14.0* (the * means 20% FPR, 100 samples); OpenAI 40.5 → 38.1.
* GPTZero is not included in the LFQA results.

Note for Detechum: before any attack, the nonwatermark detectors were already weak on larger models. "GPTZero and RankGen … are only able to detect < 15% of nonparaphrased AI generated text" and "all detectors apart from watermarking struggle with text generated by larger models like OPT 13B and GPT 3.5, achieving detection accuracies < 50%" ([§4.3](https://arxiv.org/abs/2303.13408)). The OpenAI classifier "was taken down in July 2023 by OpenAI due to its low accuracy" ([§4.2 footnote 8](https://arxiv.org/abs/2303.13408)). This is a different model from the 2019 RoBERTa GPT 2 detector: it is "a GPT model" fine tuned on "generations from 34 LLMs" ([§2](https://arxiv.org/abs/2303.13408)).

### Retrieval defense numbers
**Mechanism.** The API provider stores every output. A query is flagged if its maximum cosine similarity to any stored output is above a threshold T. The retrievers tested are P SP and BM25, with BM25 scores normalised by unigram F1 ([§5.1](https://arxiv.org/abs/2303.13408)).

**Detection at 1% FPR, long form QA** ([Table 2](https://arxiv.org/abs/2303.13408)):

| Corpus / retriever | GPT2 XL orig / 60L / 60L,O | OPT 13B | GPT 3.5 |
|---|---|---|---|
| 3K own model gens, BM25 | 100.0 / 99.2 / 97.8 | 100.0 / 99.3 / 97.3 | 100.0 / 98.6 / 96.2 |
| 3K own model gens, SP | 100.0 / 95.6 / 87.7 | 100.0 / 94.8 / 85.3 | 100.0 / 94.2 / 85.1 |
| 9K pooled, BM25 | 100.0 / 98.3 / 95.2 | 100.0 / 98.5 / 94.4 | 100.0 / 98.5 / 96.0 |
| 43K ShareGPT + 3K, BM25 | 100.0 / 98.9 / 97.5 | 100.0 / 99.0 / 97.3 | 100.0 / 98.4 / 95.5 |
| Best nonretrieval baseline at 60L,O | 55.8 (watermark) | 51.4 (watermark) | 38.1 (OpenAI) |

* **At scale (15M generations):** "detection accuracy remains consistently high across different corpus sizes (varying from 1M generations to 15M generations) … just 1% (98.3 to 97.3) on Project Gutenberg (PG19) and 9.6% (90.0 to 80.4) on Wikipedia" ([§5.3, Figure 6a](https://arxiv.org/abs/2303.13408)). The abstract summarises this as "80% to 97% of paraphrased generations … while only classifying 1% of human written sequences as AI generated" ([Abstract](https://arxiv.org/abs/2303.13408)).
* **Query length:** "BM25 struggles to detect paraphrased text with a query length of 20 (less than 25% accuracy) … begins to plateau at 50 tokens" ([§5.3, Figure 6b](https://arxiv.org/abs/2303.13408)).
* **Cost:** "1 second per retrieval on a 15M sized corpus" on a 14 core CPU. Extrapolated to ChatGPT scale, that is "130 seconds/retrieval on a Macbook" and about "5TB space monthly" ([App. A.1](https://arxiv.org/abs/2303.13408)).
* **Limitations:** the paper lists "(1) potential privacy risk … (2) inability to use retrieval based detection on open source LLMs like LLAMA … (3) the need to implement and maintain retrieval infrastructure" ([§5.4](https://arxiv.org/abs/2303.13408)). **For Detechum:** retrieval can only be run by the LLM API provider. A third party tool cannot use it unless a provider exposes a lookup API.

**Nonnative writer bias:** not reported in the paper.

---

## 4. LLM watermarking

### 4a. Kirchenbauer et al. 2023, "A Watermark for Large Language Models" (ICML 2023)

Source: [arXiv 2301.10226](https://arxiv.org/abs/2301.10226) (v4).

**Signal.**
* Before each token, a hash of the previous token seeds a random split of the vocabulary into a "green list" (fraction γ) and a red list.
* The soft watermark "adds a constant δ to the logits of the green list tokens" ([§3](https://arxiv.org/abs/2301.10226)).
* Detection counts green tokens and runs a one proportion z test. For γ = 0.5 that is z = 2(|s|G − T/2)/√T ([§2, Eq. 2](https://arxiv.org/abs/2301.10226)). With z > 4, "the probability of a false positive is 3 × 10 to 5" ([§2](https://arxiv.org/abs/2301.10226)).

**Compute cost.**
* Detection "can be detected using an efficient open source algorithm without access to the language model API or parameters" ([Abstract](https://arxiv.org/abs/2301.10226)). It needs only the tokenizer, the hash and the key, so it makes **zero model calls**.
* Generation side cost is a logit modification during sampling.
* No training data is needed.
* Experiments used OPT 1.3B with C4 RealNewsLike prompts, T = 200 ± 5 tokens ([§4.1, §6](https://arxiv.org/abs/2301.10226)).

**Headline numbers.**

Error rates at z = 4, ~500 sequences per row, T = 200 ± 5 ([Table 2](https://arxiv.org/abs/2301.10226)):

| Sampling | δ | γ | FPR | TPR |
|---|---|---|---|---|
| Multinomial | 2.0 | 0.50 | 0.0 | 0.984 |
| Multinomial | 2.0 | 0.25 | 0.0 | 0.994 |
| Multinomial | 1.0 | 0.50 | 0.0 | 0.767 |
| 8 beams | 2.0 | 0.50 | 0.0 | 0.992 |
| 8 beams | 5.0 | 0.50 | 0.0 | 1.000 |

* Caption: "All soft watermarks at δ = 2.0 incur at most 1.6% (8/500) type II error at z = 4" ([Table 2 caption](https://arxiv.org/abs/2301.10226)).
* AUC values: δ=2.0, γ=0.5 gives AUC 0.998 (PPL 6.2, multinomial); δ=1.0, γ=0.5 gives AUC 0.985 ([Figure 4](https://arxiv.org/abs/2301.10226)).
* The paper does not tabulate TPR at exactly 1% FPR. Its operating point is z=4 (theoretical FPR 3×10⁻⁵), where empirical FPR was 0.0 in every row of Table 2.

**Robustness as reported.** The T5 Large span replacement attack, with (δ, γ) = (2.0, 0.5) and multinomial sampling, at z=4 ([Table 8](https://arxiv.org/abs/2301.10226)):
* TPR goes from 0.984 (no attack) to 0.819 at ε=0.1, 0.353 at ε=0.3, 0.094 at ε=0.5 and 0.039 at ε=0.7.
* AUC goes from 0.998 to 0.988 (ε=0.1), 0.954 (ε=0.3), 0.838 (ε=0.5) and 0.696 (ε=0.7). PPL rises from 6.3 to 13.1, 21.2, 28.4 and 33.9 ([Figure 6](https://arxiv.org/abs/2301.10226)).

The paper treats human paraphrasing as "technically outside the threat model" ([§7](https://arxiv.org/abs/2301.10226)). For DIPPER results on this watermark, see §3: 100.0 → 57.2 at 1% FPR.

**Low entropy limitation.** Low entropy text cannot be watermarked strongly. In the paper's words, "low entropy (undetectable) sequences" are the main failure case ([§5 to 6, Table 1](https://arxiv.org/abs/2301.10226)).

**Nonnative writer bias.** The watermark itself was not evaluated on nonnative text. The paper raises the issue only to motivate watermarking over post hoc detection: post hoc schemes "are susceptible to labeling human text as false positive, a concern that is especially pressing for people who produce unusual text, such as a nonnative speakers" ([§8](https://arxiv.org/abs/2301.10226)). By construction, the false positive rate on human text does not depend on writing style, because the green list is pseudo random. That is a property of the test, not an empirical nonnative evaluation.

### 4b. Kirchenbauer et al. 2023, "On the Reliability of Watermarks for Large Language Models"

Source: [arXiv 2306.04634](https://arxiv.org/abs/2306.04634) (ar5iv rendering). Setup: LLaMA 7B, plus Vicuna for the human study. LeftHash scheme with h=1, (γ, δ) = (0.25, 2.0), temperature 0.7 ([§4 Experimental Setup](https://arxiv.org/abs/2306.04634)).

* **Machine paraphrase (gpt 3.5 turbo and DIPPER 11B):**
  * "ROC AUC remains above 0.85 when T=200 tokens are available, and above 0.9 with T=600 tokens" ([§1 contributions](https://arxiv.org/abs/2306.04634)).
  * At T≈200, "the attack achieves a detection performance reduction of 0.05 to 0.15 points AUC". At 600 tokens before attack, "a loss of <0.1 points AUC" ([§4.1, Figure 3](https://arxiv.org/abs/2306.04634)).
  * Unattacked AUC is ">0.999" ([§4.1](https://arxiv.org/abs/2306.04634)).
  * GPT paraphrases shrink the text to ~300 tokens and DIPPER to ~500 from 600 ([Figure 4 caption](https://arxiv.org/abs/2306.04634)).
* **Human paraphrase:** 14 graduate student writers were incentivised to remove the watermark. "after strong human paraphrasing the watermark is detectable after observing 800 tokens on average, when setting a 1e−5 false positive rate" ([Abstract](https://arxiv.org/abs/2306.04634)). Writers who barely affected the watermark were detected "after only about 250 tokens" ([§4.3, Figure 7](https://arxiv.org/abs/2306.04634)).
* **Copy paste** (watermarked spans inside human text):
  * "When a human written passage of length 600 tokens has 150 tokens of watermarked text inserted into it, AUC for detection is above 0.95" ([§1](https://arxiv.org/abs/2306.04634)).
  * With 25% watermark remaining, AUC drops "below 0.7 for 200 tokens and below 0.85 for 600 tokens" ([§4.2](https://arxiv.org/abs/2306.04634)).
* **Comparison with other detectors (T=1000):**
  * "retrieval and watermarking are both decent detection methods, and significantly more reliable that post hoc detectors". Retrieval "equals or outperforms watermarking on the GPT and Dipper model based paraphrases" but "is bested by watermarking in this novel copy paste setting".
  * "We find DetectGPT to be catastrophically unreliable under all types of attack" ([§4.4, Figure 8](https://arxiv.org/abs/2306.04634)).
* **TPR at low FPR:** plotted only, at 0.1% FPR ([App. A.6, Figure 21](https://arxiv.org/abs/2306.04634)). No numeric table, so exact TPR@1%FPR values are not reported in the text.
* **White box caveat:** if the key leaks, an attacker with "white box access to a strong paraphrasing model like Dipper … could break the watermark" ([§4.5](https://arxiv.org/abs/2306.04634)).
* **Nonnative bias:** only cited as motivation, "impractical false positive rates that especially impact vulnerable subgroups, such as nonnative speakers (Liang et al. 2023)" ([§1](https://arxiv.org/abs/2306.04634)). Not evaluated, so "not reported in the paper".

### 4c. SynthID Text (Dathathri et al., Nature 634, 2024)

Source: [Nature, doi 10.1038/s41586 024 to 08025 to 4](https://doi.org/10.1038/s41586-024-08025-4), full text read via [PMC11499265](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/), plus the [Supplementary Information](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08025-4/MediaObjects/41586_2024_8025_MOESM1_ESM.pdf).

**Signal.**
* **Tournament sampling.** A random seed comes from a hash of the last H = 4 tokens and a key. Then m pseudorandom g functions score candidate tokens. 2^m candidates are sampled from the LLM, and a knockout tournament picks the winner layer by layer using g1…gm ([Main text, "SynthID Text's Tournament sampling approach", Fig. 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).
* **Detection** uses the mean g value, Score(x) = (1/mT) Σ Σ gℓ(xt, rt) ([Eq. 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)). Experiments use the Bayesian scoring function, "m = 30 tournament layers, a Bernoulli(0.5) g value distribution" ([Methods, SynthID Text settings](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).

**Compute cost.**
* Detection: "a scoring function only requires access to the tokenized text, the watermarking key k and the random seed generator fr; no access to the LLM is required" ([Methods, Scoring functions](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)). That is zero LLM calls and no training data, except that the Bayesian scorer is "learning from data (watermarked and unwatermarked texts)" ([Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).
* Generation latency: "Gemma 7B IT … 15.527 ms per token; this increases to 15.615 ms per token with 30 layer Tournament sampling, a latency increase of only 0.57%" ([Evaluation, "minimal computational impact"](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).

**Headline numbers.**
* Detectability is reported as **TPR @ FPR = 1%** ([Methods, Detectability metric](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)). The values are **only plotted** as curves against text length (Fig. 3a; Extended Data Figs. 1, 2, 4). The main text gives no numeric TPR@1%FPR value, so **the exact TPR@1%FPR numbers are UNVERIFIED / not stated in text**.
* The selective prediction mechanism is configured "to achieve a true positive rate of 95% and a false positive rate of 1%" on the samples it does not abstain on ([Fig. 3b caption](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).
* Live Gemini experiment, "approximately 20 million watermarked and unwatermarked responses": "the thumbs up rate for the two models differed by 0.01% … and the thumbs down rate differed by 0.02% … statistically insignificant" ([Evaluation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).
* Human side by side on 3,000 ELI5 questions with Gemma 7B IT: "no significant difference in rater preference" ([Extended Data Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).

**Paraphrase robustness as reported.**
* The SI tests random word deletion (20% or 50%) and paraphrase by Gemini Ultra on 3,000 ELI5 prompts with Gemma 2B IT and 7B IT. Results are plotted only: "editing the text weakens detectability, but the watermark can still be detected with high accuracy if the text is sufficiently long. The paraphrasing attack is quite strong, especially if we use a strong paraphrasing model like Gemini Ultra" ([SI §C.6, Fig. C3](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08025-4/MediaObjects/41586_2024_8025_MOESM1_ESM.pdf)).
* The main text says: "generative watermarks are weakened by edits to the text, such as through LLM paraphrasing" ([Limitations](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).
* **No numeric post paraphrase TPR is given in the text: UNVERIFIED.**

**Multilingual.** Compared with Binoculars on XLSum in 8 languages: "Binoculars performs poorly on Hindi, Arabic and Russian; in contrast SynthID Text detects all languages well" ([SI §C.7, Fig. C4](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08025-4/MediaObjects/41586_2024_8025_MOESM1_ESM.pdf)). The plot only is given.

**Entropy limitation.** Detection is "less effective when there is less entropy". RLHF and larger models reduce entropy ([Watermark detection section](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).

**Nonnative bias.** The paper cites it as a weakness of post hoc detectors: they "may have higher false positive rates for certain groups, such as nonnative speakers" ([Main, ref. 17](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)). It does not evaluate SynthID on nonnative human text, so "not reported in the paper".

### 4d. The key limitation for Detechum

Watermark detection only works on text from models that embedded the watermark, and only for whoever holds the key:
* SynthID's own Limitations section: "generative watermarks require coordination between actors running the LLM text generation services to apply the watermark. To detect artificial intelligence generated text produced by other actors who do not to implement watermarking, other approaches are required, such as post hoc detection. Furthermore, the rise of open source models presents a challenge" ([Dathathri et al. 2024, Limitations](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).
* Ghostbuster puts it similarly: watermarking "relies on developers incorporating watermarks into models" ([Verma et al. 2024, §2](https://arxiv.org/abs/2305.15047)).
* Retrieval (§3) has the same provider only constraint.

The practical upshot: a **negative** watermark result says nothing about whether text is human. A KGW style test needs the key and the hashing scheme. SynthID needs the key, though Google has open sourced the code ([ref. 7, github.com/google deepmind/synthid text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11499265/)).

**UNVERIFIED / not from these papers:** whether any major provider exposes a public watermark verification endpoint as of Nov 2026. Detechum should check this separately before relying on watermark detection.

---

## 5. Nonnative writer bias literature

### 5.1 Liang, Yuksekgonul, Mao, Wu & Zou 2023, "GPT detectors are biased against nonnative English writers" (Patterns 4(7):100779)

Source: [arXiv 2304.02819](https://arxiv.org/abs/2304.02819) (v3). The published version is [Patterns](https://www.cell.com/patterns/fulltext/S2666-3899(23)00130 to 7).

**Samples.**
* "91 human authored TOEFL essays obtained from a Chinese educational forum and 88 US 8 th grade essays sourced from the Hewlett Foundation's Automated Student Assessment Prize (ASAP) dataset" ([Liang et al. 2023, Results](https://arxiv.org/abs/2304.02819)).
* The TOEFL essays are "year<=2020" from toefl.zhan.com ([Materials and Methods, Data](https://arxiv.org/abs/2304.02819)).
* The authors call this a "pilot study" with "relatively small" sample sizes ([Discussion](https://arxiv.org/abs/2304.02819)).

**Detectors (7, accessed March 15, 2023):** Originality.AI, Quil.org, Sapling, OpenAI (the Hugging Face Space `openai-openai-detector.hf.space`), Crossplag, GPTZero and ZeroGPT ([Methods](https://arxiv.org/abs/2304.02819)). **Inference, not stated in the paper:** the "OpenAI" entry is the Hugging Face Space hosting OpenAI's GPT 2 output detector, i.e. the Solaiman et al. 2019 RoBERTa model in §2a. The paper does say "most of the detectors assessed in this study utilize GPT 2 as their underlying backbone model" ([Discussion](https://arxiv.org/abs/2304.02819)).

**Exact numbers stated in the paper.**
* TOEFL: "they misclassified over half of the TOEFL essays as 'AI generated' (average false positive rate: 61.22%)" ([Results](https://arxiv.org/abs/2304.02819)).
* "All seven detectors unanimously identified 18 of the 91 TOEFL essays (19.78%) as AI authored, while 89 of the 91 TOEFL essays (97.80%) are flagged as AI generated by at least one detector" ([Results](https://arxiv.org/abs/2304.02819)).
* US 8th grade: "The detectors demonstrated near perfect accuracy for US 8 th grade essays." The baseline average FPR is given as **5.19%**, which rose to 56.65% after ChatGPT "simplify word choices": "from an average of 5.19% across detectors to 56.65%" ([Results](https://arxiv.org/abs/2304.02819)).
* Mitigation: after ChatGPT "Enhance the word choices to sound more like that of a native speaker", the TOEFL average FPR went "from 61.22% to 11.77%" ([Results](https://arxiv.org/abs/2304.02819)).
* Perplexity: the unanimously flagged TOEFL essays had "significantly lower perplexity … (P value: 9.74E 05)", with perplexity measured by GPT 2 XL ([Results; Methods](https://arxiv.org/abs/2304.02819)).
* ICLR 2023 abstracts (1574 papers): authors based in nonnative English countries had lower perplexity abstracts (P = 0.035; 0.033 after controlling for review rating) ([Results](https://arxiv.org/abs/2304.02819)).
* Evasion: a self edit prompt cut detection of 31 ChatGPT college essays "from 100% to 13%" ([Results, Fig. 2a](https://arxiv.org/abs/2304.02819)).

**Per detector FPRs.** The paper shows these only as a bar chart (Fig. 1a) and does not state them numerically in the text. **I derived them myself** from the authors' released score files (`Data_and_Results/Human_Data/TOEFL_real_91/*.json` and `HewlettStudentEssay_real_88/*.json` in [the authors' GitHub repo](https://github.com/Weixin-Liang/ChatGPT-Detector-Bias)), counting score > 0.5 as "AI". This threshold **exactly reproduces the paper's stated averages (61.22% and 5.19%)**, which supports the reconstruction. It is still my computation, not a published number.

| Detector | TOEFL 91 FPR (derived) | US 8th grade (n=88) FPR (derived) |
|---|---|---|
| Originality.AI | 75.82% | 1.14% |
| Quil.org | 74.73% | 9.09% |
| Sapling | 68.13% | 4.55% |
| OpenAI (HF Space; RoBERTa GPT 2 detector, inferred) | 58.24% | 9.09% |
| Crossplag | 51.65% | 12.50% |
| GPTZero | 51.65% | 0.00% |
| ZeroGPT | 48.35% | 0.00% |
| **Mean** | **61.22%** (matches paper) | **5.19%** (matches paper) |

As a cross check, Al Ali et al. 2026 independently describe the best detector in Liang et al. as "48%" ([Al Ali et al. 2026, §5.3](https://arxiv.org/abs/2602.05769)), which matches the derived ZeroGPT value.

**Methodological caveats noted in the sources.**
* The TOEFL 91 essays are short (median 104 words) ([Verma et al. 2024, Table 6](https://arxiv.org/abs/2305.15047)).
* The native comparison group is US 8th graders, not adult or college writers. The two groups also differ in topic and genre.
* Detectors were commercial versions as of 15 March 2023.

### 5.2 Ghostbuster's reevaluation (2024)
See §1. On the same TOEFL 91 essays, accuracy was RoBERTa 96.7%, GPTZero 92.3%, Ghostbuster 74.7%, DetectGPT 63.7% and perplexity only 13.2%. On 1,000 full length TOEFL11 essays, all detectors scored ≥98.1% accuracy ([Verma et al. 2024, Table 3](https://arxiv.org/abs/2305.15047)). The authors attribute much of the TOEFL 91 drop to document length ([§7.3](https://arxiv.org/abs/2305.15047)).

Note the GPTZero discrepancy: Liang's GPTZero FPR is 51.65% (derived) in March 2023, while Ghostbuster reports 92.3% accuracy, i.e. about 7.7% implied FPR, on the same essays. The paper does not state when Ghostbuster queried GPTZero, so **a version change is possible but UNVERIFIED**.

### 5.3 Jiang, Hao, Fauss & Li 2024, GRE study (Computers & Education 217, 105070): PRIMARY NOT ACCESSED

* **Bibliographic metadata, verified via Crossref:** "Detecting ChatGPT generated essays in a large scale writing assessment: Is there a bias against nonnative English speakers?", Yang Jiang, Jiangang Hao, Michael Fauss, Chen Li. *Computers & Education*, vol. 217, article 105070, Aug 2024 ([doi 10.1016/j.compedu.2024.105070](https://doi.org/10.1016/j.compedu.2024.105070)).
* **Primary text: UNVERIFIED.** ScienceDirect returned HTTP 403, Semantic Scholar lists it as closed access, and Crossref has no abstract.
* **Secondary description by coauthors** (Zu, Fauss & Li 2025, ETS): "Using 10,000 essays generated by ChatGPT and 10,000 essays written by real test takers for 50 GRE writing items, the authors trained detectors using supervised ML with linguistic features extracted by e rater … and GPT 2 based perplexity features. Detection accuracy of the best performing detector was nearly 100% on a holdout test set, and showed no evidence of bias against nonnative English speakers" ([Zu, Fauss & Li 2025, AIME Con, p.92](https://aclanthology.org/2025.aimecon-sessions.11.pdf)).
* The lead author's conference talk transcript says "accuracy close to 100 percent" ([ETS AERA/NCME transcript](https://www.ets.org/aera-ncme-conference/transcript/yang-jiang.html)).
* **UNVERIFIED:** the exact native and nonnative FPRs, the nonnative sample sizes and the fairness metric used. None could be read from the primary source.

**How it differs methodologically from Liang** (based on the secondary description only):
1. The detectors were **custom trained on in domain data** (GRE essays, ChatGPT essays on the same 50 prompts), not off the shelf commercial tools.
2. The sample is much larger (10,000 human plus 10,000 AI essays, per the secondary source).
3. Native and nonnative writers wrote on the **same prompts in the same high stakes test**, which reduces topic and genre confounds.
4. The features are e rater linguistic features plus perplexity, not perplexity dominated public detectors.

This result shows that a detector *can* be calibrated to avoid the bias in a closed domain. It does not show that general purpose detectors are unbiased.

### 5.4 Al Ali, Helcl & Libovický 2026, "Different Time, Different Language" (EACL 2026 SRW; arXiv 2602.05769)

Source: [arXiv 2602.05769](https://arxiv.org/abs/2602.05769). The venue (EACL 2026 Student Research Workshop) is as stated on the arXiv listing and was not independently checked.

* **Language:** Czech, not English.
* **Data:**
  * NonNative: 450 essays (AKCES 3, learners who had studied Czech for at least 24 months).
  * NonNativeC1: 29 essays (proficient, C1/C2).
  * NatYouth: 450 native essays (AKCES 1, school pupils).
  * NatAdv: 29 essays (ages 16 to 18).
  Source: [Table 1, §3.3](https://arxiv.org/abs/2602.05769).
* **Perplexity finding (opposite of Liang):** "nonnative (NonNative) speakers produce texts with greater entropy than native (NatYouth) speakers do (p<10⁻¹⁴)". The authors attribute this to grammar errors, which raise entropy ([§4, Table 2](https://arxiv.org/abs/2602.05769)).
* **Detectors:** TF IDF naive Bayes, a fine tuned RobeCzech (a RoBERTa like model) and the commercial Plagramme. "none of the detectors exhibited a systematic bias against nonnative speakers of Czech" ([§5.4](https://arxiv.org/abs/2602.05769)).
* **Plagramme FPRs** (each set capped at 100 documents and 512 words) ([Table 5](https://arxiv.org/abs/2602.05769)):
  * NonNative 2.0%, NonNativeC1 0.0%, NatYouth 1.0%, NatAdv 3.5%.
  * On Liang's English sets: **TOEFL 91 23.1%** and **Hewlett (native) 0.0%**.
* Their conclusion on English: "the FPR improved from the reported 61.3% (mean) or 48% (best detector) to our observed 23.1%". There is still a nontrivial gap (ΔFPR = 23.1%), and "the correlation between text entropy and detector output was negligible" (0<ρ<0.04) ([§5.3](https://arxiv.org/abs/2602.05769)).
* The paper rounds Liang's figures as 61.3% (TOEFL) and 5.1% (native) ([§2.2](https://arxiv.org/abs/2602.05769)). The primary values are 61.22% and 5.19% ([Liang et al. 2023](https://arxiv.org/abs/2304.02819)).
* **Method differences from Liang:**
  1. A different language with richer morphology.
  2. 2025 era detectors.
  3. Native control groups matched by genre and file size.
  4. Small proficient subsets (29 each).
  5. A single commercial detector on the English retest.
* **For Detechum:** even in 2025, the best commercial detector they tested still showed a 23.1 point FPR gap on Liang's English TOEFL 91 set.

### 5.5 Park, Jeong & Kim 2026, "Style as a Confound" (arXiv 2608.26710)

Source: [arXiv 2608.26710](https://arxiv.org/abs/2608.26710) (v1, 27 Aug 2026). **UNVERIFIED:** an EMNLP 2026 acceptance was reported by a summarizer of the arXiv abstract page. The HTML I read does not state the venue.

* **Design:** "135,389 document pairs from a professional English editing service (2018 to 2025), comprising nonnative manuscripts and their native edited versions". Editors are a Wordvice service; the paper says AI rewriting is prohibited by company policy ([Abstract, §3.1](https://arxiv.org/abs/2608.26710)).
* 13 detectors, off the shelf, with a single fixed threshold of 0.5 ([App. C.0.1](https://arxiv.org/abs/2608.26710)).
* **Baseline FPR on pre ChatGPT (2018 to 2022) nonnative academic manuscripts, original → edited** ([Table 3](https://arxiv.org/abs/2608.26710)):
  * **RoBERTa (`openai-community/roberta-base-openai-detector`, i.e. Solaiman et al.): 93.1% → 93.9%.**
  * RADAR: 88.3% → 86.4%.
  * MAGE: 16.7% → 7.6%.
  * Fast DetectGPT: 25.2% → 31.6%.
  * Binoculars: 0.0% → 0.1%.
  * Log rank: 100.0% → 100.0%.
* Overall: "FPRs for human written texts varied widely, from 0.0% to 100.0%" ([Abstract](https://arxiv.org/abs/2608.26710)).
* Pre ChatGPT to post ChatGPT: "the FPR of RoBERTa increases from 92.7% to 96.4%" ([App. D.1](https://arxiv.org/abs/2608.26710)). This baseline differs slightly from Table 3's 93.1%. The two figures probably come from different subsets, but **the paper does not reconcile them (UNVERIFIED)**.
* **Method differences from Liang:**
  1. Within document paired design (same author and content, before and after native editing) instead of comparing two populations.
  2. There is **no independent native author control group**, so the study measures sensitivity to *editing style*, not a native vs nonnative FPR gap.
  3. Academic manuscripts, not test essays.
  4. A threshold fixed at 0.5 rather than calibrated. The authors warn that "different threshold choices may produce different absolute FPR estimates" ([§6](https://arxiv.org/abs/2608.26710)).

The authors frame editing style as "a key confounding variable … rather than establishing a full separation of text origin from linguistic style" ([Abstract](https://arxiv.org/abs/2608.26710)).

### 5.6 Synthesis on bias (my reading, with the evidence it rests on)

1. **Off the shelf, perplexity based or GPT 2 era detectors at default thresholds** show large nonnative FPRs on short essays. The TOEFL 91 average was 61.22% ([Liang et al. 2023](https://arxiv.org/abs/2304.02819)). The Solaiman RoBERTa detector reached 93.1% FPR on nonnative academic manuscripts at τ=0.5 ([Park et al. 2026, Table 3](https://arxiv.org/abs/2608.26710)).
2. **Length matters.** On 1,000 full length TOEFL11 essays, every detector Ghostbuster tested scored ≥98.1% accuracy ([Verma et al. 2024, Table 3](https://arxiv.org/abs/2305.15047)).
3. **In domain trained, well sampled detectors can show no measurable bias** (GRE study). This claim rests on a secondary description; the primary is UNVERIFIED ([Zu et al. 2025](https://aclanthology.org/2025.aimecon-sessions.11.pdf)).
4. **The perplexity mechanism does not transfer across languages.** In Czech, nonnative text has *higher* entropy ([Al Ali et al. 2026, Table 2](https://arxiv.org/abs/2602.05769)).
5. **The bias has not disappeared in English.** The best commercial detector Al Ali et al. tested in 2025 still showed 23.1% FPR on TOEFL 91 against 0.0% on the native set ([Al Ali et al. 2026, Table 5](https://arxiv.org/abs/2602.05769)).

---

## 6. Cross method summary for Detechum

| Method | Model calls per text at detection | Training data needed | Best low FPR number found (primary) | Under DIPPER or paraphrase | Nonnative evidence |
|---|---|---|---|---|---|
| Ghostbuster | 2 GPT 3 scoring passes (ada, davinci) + 2 local n gram models | ~1k human + 1k AI docs per domain | F1 only; no TPR@FPR reported | Not tested with DIPPER; Undetectable.ai recall 99% → 62% | TOEFL 91 acc. 74.7%; TOEFL11 99.9%; Lang8 95.5% |
| RoBERTa (Solaiman) | 1 pass, 125M or 356M encoder | GPT 2 outputs + WebText | ~95% acc. (balanced, 510 tokens); RAID acc.@5%FPR 56.7 to 59.1 | RAID DIPPER: accuracy *rose* (56.7 → 72.9 for large) | Derived 58.24% FPR on TOEFL 91 (as "OpenAI" in Liang); 93.1% FPR on nonnative manuscripts (Park et al.) |
| RoBERTa (HC3) | 1 pass, roberta base | HC3 (EN: 58,546 human / 26,903 ChatGPT answers) | F1 99.82 in dist; RAID acc.@5%FPR 44.8; naive FPR 15.8% at τ=0.5 | RAID DIPPER 44.8 → 49.2 | Not reported |
| KGW watermark | 0 (tokenizer + key) | None | TPR 0.984 at z=4, FPR 0.0 (δ=2, γ=0.5, T≈200) | DIPPER: 100.0 → 57.2 at 1% FPR (T≈300); recovers to AUC >0.9 by 600 tokens | Not evaluated (FPR is style independent by construction) |
| SynthID Text | 0 LLM calls (key + scorer) | Bayesian scorer trained on WM/non WM text | TPR@1%FPR plotted only (UNVERIFIED numerically) | "quite strong" degradation under Gemini Ultra paraphrase (plotted only) | Not evaluated |
| Retrieval (Krishna) | 1 BM25 / P SP search over provider DB | Provider's full output log | 97.8% (GPT2 XL), 97.3% (OPT), 96.2% (GPT 3.5) at 1% FPR after 60L,60O DIPPER; 80.4 to 97.3% at 15M corpus | Designed for it | Not reported |

Citations for the cells: §§1 to 4 above.

---

## 7. Could not access or verify

* **Jiang, Hao, Fauss & Li 2024** (Computers & Education 217, 105070): full text and abstract were paywalled (HTTP 403). All numbers about it come from a coauthor's secondary description and are marked UNVERIFIED. The per group FPRs and the nonnative sample size are unknown.
* **SynthID Text numeric TPR@1%FPR values** and **post paraphrase detection values**: these appear only in figures (Fig. 3, Extended Data Figs. 1 to 4, SI Fig. C3), not in text or tables.
* **Liang et al. per detector FPRs:** not stated numerically in the paper (Fig. 1a only). The table in §5.1 is my reconstruction from the authors' released data. It matches the paper's stated averages exactly but is still a derived figure.
* **Kirchenbauer "Reliability" TPR at low FPR:** plotted only (Figure 21, 0.1% FPR).
* **RAID TPR@1%FPR for RoBERTa detectors:** plotted only (Figure 4). Tables report 5% FPR.
* **Ghostbuster AUROC or TPR@FPR:** not reported in the paper (F1 and accuracy only). The paper also does not give model sizes for ada and davinci.
* **Solaiman et al. training set size:** not found in the section read.
* **HC3 paper version:** read via ar5iv, which did not show the arXiv version number.
* **Venue claims for arXiv 2602.05769 (EACL 2026 SRW) and 2608.26710 (EMNLP 2026):** taken from the arXiv listing metadata as summarized. Not independently confirmed.
