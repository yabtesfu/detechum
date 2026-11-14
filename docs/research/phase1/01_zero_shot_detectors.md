# Phase 1: Zero shot detectors (GLTR, DetectGPT, Fast DetectGPT, Binoculars) and their RAID results

**Sources.** All five papers were read in full from arXiv's HTML (LaTeXML) builds, which were downloaded and converted to text so numbers could be copied exactly. These are the versions read:

| Paper | arXiv version read | Link |
|---|---|---|
| GLTR (Gehrmann, Strobelt, Rush, ACL 2019 demo) | 1906.04043**v1** (10 Jun 2019) | https://arxiv.org/abs/1906.04043 |
| DetectGPT (Mitchell et al., ICML 2023) | 2301.11305**v2** (23 Jul 2023) | https://arxiv.org/abs/2301.11305 |
| Fast DetectGPT (Bao et al., ICLR 2024) | 2310.05130**v3** (16 Dec 2024) | https://arxiv.org/abs/2310.05130 |
| Binoculars (Hans et al., ICML 2024) | 2401.12070**v3** (13 Oct 2024) | https://arxiv.org/abs/2401.12070 |
| RAID (Dugan et al., ACL 2024) | 2405.07940**v2** (10 Jun 2024) | https://arxiv.org/abs/2405.07940 |

**Conventions.**
* Numbers are copied exactly as printed. They are not rounded or recomputed.
* **UNVERIFIED** marks anything that could not be confirmed from the source text.
* **(derived)** marks statements that follow from a paper's algorithm or equations but that the paper does not state outright.
* The camera ready ACL, ICML and ICLR PDFs were **not** compared against these arXiv versions. Table and figure numbers can differ between versions.

---

## 1. GLTR (Gehrmann, Strobelt, Rush, 2019)

### Signal
* GLTR applies three per token tests using a "detection model" `p_det`. Each test is defined over `p_det(X_i | X_1:i-1)`:
  * **Test 1:** the probability of the observed word.
  * **Test 2:** the absolute rank of the observed word in the predicted distribution.
  * **Test 3:** the entropy of the predicted distribution, `-Σ_w p_det(X_i=w|X_1:i-1) log p_det(X_i=w|X_1:i-1)`.

  ([Gehrmann et al. 2019, §2](https://arxiv.org/abs/1906.04043))
* The paper states the assumption as: "most systems sample from the head of the distribution". Tests 1 and 2 check whether a word was sampled from the top of the distribution. Test 3 checks whether the context is so familiar to the detector that it is (overly) sure of its next prediction ([Gehrmann et al. 2019, §2](https://arxiv.org/abs/1906.04043)).
* **Scorer models:** the deployed tool uses "both BERT ... and GPT 2 117M" ([Gehrmann et al. 2019, §3](https://arxiv.org/abs/1906.04043)).
  * GPT 2 117M computes `p_det(X_i | X_1…i-1)` left to right.
  * For BERT, the authors "iteratively mask out each correct token" and use 30 words of context on each side ([Gehrmann et al. 2019, §3](https://arxiv.org/abs/1906.04043)).
* **Overlay buckets** (default colours): top 10 is green, top 100 yellow, top 1,000 red, and the rest purple ([Gehrmann et al. 2019, §3](https://arxiv.org/abs/1906.04043)).
* **Classifier used in the empirical validation:**
  * Test 1 feature: the average probability of each word in a document.
  * Test 2 feature: the distribution over the four rank buckets.
  * Baseline: logistic regression over bag of words.

  ([Gehrmann et al. 2019, §4](https://arxiv.org/abs/1906.04043))
* GLTR is primarily a **visual tool to assist human judges**. The paper does not define a single scalar detector score with a fixed threshold.

### Compute cost
* **GPT 2 117M backend:** one left to right forward pass yields `p_det` at every position (derived from [Gehrmann et al. 2019, §3](https://arxiv.org/abs/1906.04043)).
* **BERT backend:** one masked forward pass per token, because each token is masked in turn (derived from [Gehrmann et al. 2019, §3](https://arxiv.org/abs/1906.04043)).
* Model sizes:
  * The paper gives GPT 2 117M.
  * The paper does not state BERT's size. **UNVERIFIED**
* No wall clock timings or speed figures are reported in the paper.

### Headline detection numbers
The paper reports cross validated **AUC**, not TPR at a fixed FPR ([Gehrmann et al. 2019, Table 1](https://arxiv.org/abs/1906.04043)).

**Setup.** The data is 50 articles from each of 3 generated sources and 3 human sources ([Gehrmann et al. 2019, §4](https://arxiv.org/abs/1906.04043)):
* Generated: GPT 2 1.5B with temperature 0.7, GPT 2 1.5B truncated to top 40, and Washington Post Heliograf.
* Human: CBT, NYT and scientific abstracts.

Models were trained on each combination of four sources and tested on the remaining two.

| Feature | AUC |
|---|---|
| Bag of Words | 0.63 ± 0.11 |
| (Test 1, GPT 2) Average Probability | 0.71 ± 0.25 |
| (Test 2, GPT 2) Top K Buckets | 0.87 ± 0.07 |
| (Test 1, BERT) Average Probability | 0.70 ± 0.27 |
| (Test 2, BERT) Top K Buckets | 0.85 ± 0.09 |

([Gehrmann et al. 2019, Table 1](https://arxiv.org/abs/1906.04043))

**Other reported statistics:**
* The odds ratio is 5.32 for a word outside the top 100 predictions and 0.09 for the top 1 prediction ([Gehrmann et al. 2019, §4 Results](https://arxiv.org/abs/1906.04043)).
* Real text uses words outside the top 100 predictions "2.41 times as frequently under GPT 2 (1.67 for BERT)" as generated text ([Gehrmann et al. 2019, §4 Results](https://arxiv.org/abs/1906.04043)).

**Human subjects study** (35 students):
* Without the overlay, accuracy was 54.2%. With it, accuracy was 72.3% ([Gehrmann et al. 2019, §5 Results](https://arxiv.org/abs/1906.04043)).
* The abstract rounds these to "from 54% to 72%".
* The average treatment effect was +18.1%, with p<0.001 ([Gehrmann et al. 2019, §5 Results](https://arxiv.org/abs/1906.04043)).

**TPR at low FPR:** not reported in the paper.

### Paraphrase robustness
* No experiment: not reported in the paper.
* The Future Work section only notes qualitatively that "adversarial schemes that aim to fool our overlay" are imaginable. It argues that "forcibly sampling from the tail decreases the coherence" ([Gehrmann et al. 2019, §7](https://arxiv.org/abs/1906.04043)).

### Nonnative writer bias
* Not reported in the paper.
* The human study's treatment effect was computed "even after controlling for whether a participant is a native speaker" ([Gehrmann et al. 2019, §5](https://arxiv.org/abs/1906.04043)). That concerns the human judges, not whether the detector is biased against nonnative authors.

---

## 2. DetectGPT (Mitchell et al., 2023)

### Signal
**Perturbation discrepancy.** This is the core quantity:

`d(x, p_θ, q) = log p_θ(x) − E_{x̃~q(·|x)} log p_θ(x̃)`

* `p_θ` is the source (scoring) model.
* `q` is a perturbation function. In practice it is a mask filling model, T5.

([Mitchell et al. 2023, Eq. 1](https://arxiv.org/abs/2301.11305))

**Hypothesis.** Model samples lie in regions of negative log probability curvature. Under this hypothesis:
* `d` is "positive and large" for model samples.
* `d` "tends toward zero" for human text.

([Mitchell et al. 2023, §4](https://arxiv.org/abs/2301.11305))

**Curvature interpretation.** The paper shows `d` approximates the negative trace of the Hessian of log p with respect to the input, via Hutchinson's estimator ([Mitchell et al. 2023, Eqs. 2 to 5](https://arxiv.org/abs/2301.11305)).

**Normalised score used in experiments** (Algorithm 1):
* `d̂_x = log p_θ(x) − μ̃`, where `μ̃ = (1/k) Σ_i log p_θ(x̃_i)`.
* `σ̃_x² = (1/(k−1)) Σ_i (log p_θ(x̃_i) − μ̃)²`.
* The decision rule is `d̂_x / √σ̃_x > ε`.

([Mitchell et al. 2023, Algorithm 1](https://arxiv.org/abs/2301.11305))

The arXiv v2 Algorithm 1 prints `√σ̃_x`, where `σ̃_x²` is the variance. That reads as dividing by the square root of the standard deviation. The paper text says the discrepancy is normalised "by the standard deviation". This is a notational inconsistency in the source, copied as printed.

Normalising "typically increas[es] AUROC by around 0.020" ([Mitchell et al. 2023, §4](https://arxiv.org/abs/2301.11305)).

**Scorer and perturbation models:**
* Scorer: the source LLM itself (white box). Tested from GPT 2 (1.5B) up to GPT NeoX (20B), plus GPT 3 and Jurassic 2 Jumbo (175B) through their APIs.
* Perturbation model: T5 3B for almost all experiments. T5 11B is used for the GPT NeoX and GPT 3 experiments, and mT5 3B for WMT German.
* Masking: 15% of words are masked, in spans of 2 words.

([Mitchell et al. 2023, §5 Hyperparameters](https://arxiv.org/abs/2301.11305))

### Compute cost
**Per text cost (derived from [Mitchell et al. 2023, Algorithm 1](https://arxiv.org/abs/2301.11305)):**
* k mask fill generations from T5.
* k + 1 scoring passes of the source model: one for x and one for each x̃_i.

**Default k:**
* The hypothesis test approximates the expectation "with 100 samples from T5" ([Mitchell et al. 2023, §4](https://arxiv.org/abs/2301.11305)).
* "Detection accuracy continues to improve until 100 perturbations, where it converges" ([Mitchell et al. 2023, §5.3 & Figure 8](https://arxiv.org/abs/2301.11305)).

**Limitations section.** "DetectGPT is more compute intensive than other methods for detection, as it requires sampling and scoring the set of perturbations for each candidate passage" ([Mitchell et al. 2023, §6 Limitations](https://arxiv.org/abs/2301.11305)).

**Wall clock time:** not reported in the DetectGPT paper. The 79,113 second figure for DetectGPT comes from the Fast DetectGPT paper (see §3 below).

### Headline detection numbers
**Metric.** All numbers are **AUROC** ([Mitchell et al. 2023, §5 Datasets & metrics](https://arxiv.org/abs/2301.11305)).

**Abstract headline.** On "fake news articles generated by 20B parameter GPT NeoX", AUROC improves "from 0.81 AUROC for the strongest zero shot baseline to 0.95 AUROC for DetectGPT" ([Mitchell et al. 2023, Abstract](https://arxiv.org/abs/2301.11305)). This matches XSum / NeoX in Table 1: LogRank 0.81 and DetectGPT 0.95.

**Table 1** (500 samples, temperature 1 sampling, AUROC) ([Mitchell et al. 2023, Table 1](https://arxiv.org/abs/2301.11305)):

| Dataset | GPT 2 | OPT 2.7 | Neo 2.7 | GPT J | NeoX | Avg. |
|---|---|---|---|---|---|---|
| XSum: DetectGPT | 0.99 | 0.97 | 0.99 | 0.97 | 0.95 | 0.97 |
| XSum: LogRank (best baseline) | 0.89 | 0.88 | 0.90 | 0.86 | 0.81 | 0.87 |
| SQuAD: DetectGPT | 0.99 | 0.97 | 0.97 | 0.90 | 0.79 | 0.92 |
| SQuAD: LogRank | 0.94 | 0.92 | 0.90 | 0.83 | 0.76 | 0.87 |
| WritingPrompts: DetectGPT | 0.99 | 0.99 | 0.99 | 0.97 | 0.93 | 0.97 |
| WritingPrompts: LogRank | 0.98 | 0.96 | 0.97 | 0.96 | 0.95 | 0.96 |

* In the text: "For 14 of the 15 combinations of dataset and model, DetectGPT provides the most accurate detection performance, with a 0.06 AUROC improvement on average" ([Mitchell et al. 2023, §5.1](https://arxiv.org/abs/2301.11305)).

**Table 2.** 175B models, 150 examples per dataset, AUROC printed as GPT 3 / Jurassic 2 ([Mitchell et al. 2023, Table 2](https://arxiv.org/abs/2301.11305)):
* DetectGPT: PubMedQA 0.84 / 0.77, XSum 0.84 / 0.84, WritingPrompts 0.87 / 0.84, Avg. 0.83.
* RoBERTa large (supervised): PubMedQA 0.71 / 0.64, XSum 0.92 / 0.88, WritingPrompts 0.91 / 0.88, Avg. 0.82.

**Table 3.** Top p (p=0.96) and top k (k=40) sampling, DetectGPT AUROC averaged over five models ([Mitchell et al. 2023, Table 3](https://arxiv.org/abs/2301.11305)):

| Dataset | top p | top k |
|---|---|---|
| XSum | 0.98 | 0.98 |
| SQuAD | 0.94 | 0.93 |
| WritingPrompts | 0.98 | 0.97 |

**TPR at low FPR:** not reported in the paper. Only AUROC is used.

### Paraphrase robustness
* §5.2, "Detecting paraphrased machine generated text", simulates human revision. It does this "by replacing 5 word spans of the text with samples from T5 3B until r% of the text has been replaced" on XSum ([Mitchell et al. 2023, §5.2 & Figure 5](https://arxiv.org/abs/2301.11305)).
* Result: "DetectGPT maintains detection AUROC above 0.8 even when nearly a quarter of the text in model samples has been replaced", and "DetectGPT shows the strongest detection performance for all revision levels" ([Mitchell et al. 2023, §5.2](https://arxiv.org/abs/2301.11305)).
* The per r AUROC values appear only as a plot in Figure 5, so exact values are **UNVERIFIED** (not given as text or table).
* This is span replacement by T5, **not** a paraphrase model such as DIPPER. The paper notes that Sadasivan et al. (2023) and Krishna et al. (2023) "show the effectiveness of paraphrasing as a tool for evading detection, suggesting an important area of study for future work" ([Mitchell et al. 2023, §2](https://arxiv.org/abs/2301.11305)).

### Nonnative writer bias
* No experiment: not reported in the paper.
* Related Work cites Liang et al. (2023), saying "non DetectGPT detectors showing bias against nonnative speakers". It argues this "highlights the advantage of zero shot detectors like DetectGPT", but runs no test of its own ([Mitchell et al. 2023, §2](https://arxiv.org/abs/2301.11305)).

---

## 3. Fast DetectGPT (Bao et al., 2024)

### Signal
**Conditional probability curvature.** Fast DetectGPT replaces DetectGPT's `p_θ(x̃)` with a conditional probability function in which each token is predicted independently given the original prefix:

`p_θ(x̃|x) = Π_j p_θ(x̃_j | x_<j)`

([Bao et al. 2024, Eq. 2](https://arxiv.org/abs/2310.05130))

**Score:**

`d(x, p_θ, q_φ) = (log p_θ(x|x) − μ̃) / σ̃`

* `μ̃ = E_{x̃~q_φ(x̃|x)}[log p_θ(x̃|x)]`.
* `σ̃² = E[(log p_θ(x̃|x) − μ̃)²]`.

([Bao et al. 2024, Eqs. 3 to 4, Algorithm 1](https://arxiv.org/abs/2310.05130))

**Two roles:**
* A **sampling model** `q_φ` draws alternative tokens.
* A **scoring model** `p_θ` scores them.

**Default sample count.** The default is 10,000 samples, drawn with one PyTorch call ([Bao et al. 2024, §2.3](https://arxiv.org/abs/2310.05130)). An analytical solution (Appendix B) "achieves a detection accuracy almost identical to the sampling approximation with 10,000 samples ... but further accelerates the detection process by about 10%" ([Bao et al. 2024, Appendix B](https://arxiv.org/abs/2310.05130)).

**Same model for sampling and scoring.** The numerator becomes the sum of the Likelihood baseline (`log p_θ(x)`) and the Entropy baseline (`−μ̃`) ([Bao et al. 2024, §2.3, Eq. 5](https://arxiv.org/abs/2310.05130)).

**Models used:**
* White box: the source model does both sampling and scoring ("*/*").
* Black box default: GPT J (6B) samples and GPT Neo 2.7B scores ("GPT J/Neo 2.7").
* Neo 2.7 was chosen as the scorer because it was "empirically superior among GPT 2, Neo 2.7, and GPT J".

([Bao et al. 2024, §3.2, Table 2, Table 4](https://arxiv.org/abs/2310.05130))

### Compute cost
**Forward passes.**
* The paper says it "only necessitates a single model forward pass" ([Bao et al. 2024, §5](https://arxiv.org/abs/2310.05130)).
* It also says it "invokes the sampling GPT once to generate all samples and similarly calls the scoring GPT once to evaluate all samples" ([Bao et al. 2024, Figure 2 caption](https://arxiv.org/abs/2310.05130)).
* So it is 1 pass if the same model samples and scores, or 2 passes (one per model) in the black box GPT J/Neo 2.7 setup.
* For comparison, DetectGPT needs "around one hundred model calls" ([Bao et al. 2024, §1](https://arxiv.org/abs/2310.05130)).

**Speedup: "340x".** It appears in three places:
* Abstract: "accelerates the detection process by a factor of 340, as detailed in Table 1" ([Bao et al. 2024, Abstract](https://arxiv.org/abs/2310.05130)).
* Table 1, "Speedup" column: DetectGPT "1x", Fast DetectGPT "340x" ([Bao et al. 2024, Table 1](https://arxiv.org/abs/2310.05130)).
* §3.2, "Inference Speedup": "It totals 79,113 seconds (approximately 22 hours) over five runs. In contrast, Fast DetectGPT completes the task in only 233 seconds (about 4 minutes), achieving a remarkable speedup factor of approximately 340x" ([Bao et al. 2024, §3.2](https://arxiv.org/abs/2310.05130)).

**Speedup setup.** XSum generations from the five Table 2 models, on a Tesla A100 GPU. DetectGPT used 100 perturbations split into 10 batches ([Bao et al. 2024, §3.2; Table 1 caption](https://arxiv.org/abs/2310.05130)).

**Model sizes and hardware.** Sizes range from 1.3B to 20B for local models. Models under 20B were run on a Tesla A100 (80G), with float16 for models above 6B ([Bao et al. 2024, Appendix C.1, Table 4](https://arxiv.org/abs/2310.05130)).

### Headline detection numbers
**Metric.** AUROC, plus "relative ↑" computed as `(new−old)/(1.0−old)` ([Bao et al. 2024, Appendix A](https://arxiv.org/abs/2310.05130)).

**Table 1 headline** ([Bao et al. 2024, Table 1](https://arxiv.org/abs/2310.05130)):

| Method | 5 model generations (white box) | ChatGPT/GPT 4 (black box) | Speedup |
|---|---|---|---|
| DetectGPT | 0.9554 | 0.7225 | 1x |
| Fast DetectGPT | 0.9887 (relative ↑74.7%) | 0.9338 (relative ↑76.1%) | 340x |

**Table 2.** Average AUROC over XSum, SQuAD and WritingPrompts, 500 samples per dataset ([Bao et al. 2024, Table 2](https://arxiv.org/abs/2310.05130)):

| Method | GPT 2 | OPT 2.7 | Neo 2.7 | GPT J | NeoX | Avg. |
|---|---|---|---|---|---|---|
| White box: DetectGPT (T5 3B/*) | 0.9917 | 0.9758 | 0.9797 | 0.9353 | 0.8943 | 0.9554 |
| White box: Fast DetectGPT (*/*) | 0.9967 | 0.9908 | 0.9940 | 0.9866 | 0.9754 | 0.9887 |
| Black box: DetectGPT (T5 3B/Neo 2.7) | 0.8517 | 0.8390 | 0.9797 | 0.8575 | 0.8400 | 0.8736 |
| Black box: Fast DetectGPT (GPT J/Neo 2.7) | 0.9834 | 0.9572 | 0.9984 | 0.9592 | 0.9404 | 0.9677 |

**Table 3.** ChatGPT and GPT 4 generations, black box, 150 samples per dataset ([Bao et al. 2024, Table 3](https://arxiv.org/abs/2310.05130)):
* Fast Detect (GPT J/Neo 2.7) on ChatGPT: XSum 0.9907, Writing 0.9916, PubMed 0.9021, Avg. 0.9615.
* Fast Detect (GPT J/Neo 2.7) on GPT 4: XSum 0.9067, Writing 0.9612, PubMed 0.8503, Avg. 0.9061.
* DetectGPT (T5 11B/Neo 2.7), average: ChatGPT 0.8223, GPT 4 0.6228.
* GPTZero, average: ChatGPT 0.9348, GPT 4 0.8853.

**TPR at low FPR** (§3.4, "Interpretation of AUROC"):
* ChatGPT: "Fast DetectGPT achieves a recall of 87% for machine generated texts with only 1% misclassification of human written text as machine generated. When the tolerance for false positives increases to 10%, the recall reaches 98%."
* GPT 4: "recall of 89% on the condition of a false positive rate less than 10%".

([Bao et al. 2024, §3.4](https://arxiv.org/abs/2310.05130))

**Inconsistency 1 (UNVERIFIED which is correct).** The Introduction says something different from §3.4: "it aptly flags 80% of ChatGPT crafted content, while only misidentifying 1% of human compositions" ([Bao et al. 2024, §1](https://arxiv.org/abs/2310.05130)). That is 80% versus 87% at 1% FPR in the same paper (v3).

**Inconsistency 2.** §3.4 cites "Figure 4" for these numbers. In v3, the log scale ROC curves are Figure 3, and Figure 4 is accuracy versus passage length.

The source of these TPR numbers is the ROC plot on WritingPrompts (Figure 3). No table of TPR@FPR values is given. TPR at 0.01% FPR is not reported.

### Paraphrase robustness
**Main text pointer.** §3.4 points to the results: "We analyze the robustness under paraphrasing attack and propose decoherence attack, finding that Fast DetectGPT consistently outperforms both zero shot and trained detectors" ([Bao et al. 2024, §3.4 → Appendix F.2](https://arxiv.org/abs/2310.05130)).

**Attacks** (applied to ChatGPT generations, black box setting):
* **Paraphrase:** a T5 paraphraser (`Vamsi/T5_Paraphrase_Paws`) rewrites each sentence, "Following ... Sadasivan et al. (2023)".
* **Decoherence:** two adjacent words are randomly swapped in each sentence of more than 20 words.

([Bao et al. 2024, Appendix F.2, Table 11](https://arxiv.org/abs/2310.05130))

**Table 11** (AUROC; XSum / Writing / PubMed / Avg.) ([Bao et al. 2024, Table 11](https://arxiv.org/abs/2310.05130)):

| Method | Paraphrase attack | Decoherence attack |
|---|---|---|
| RoBERTa base | 0.8103 / 0.5368 / 0.5962 / 0.6477 | 0.5778 / 0.5629 / 0.5392 / 0.5600 |
| DetectGPT (T5 11B/GPT 2) | 0.4864 / 0.5698 / 0.6004 / 0.5522 | 0.2919 / 0.7035 / 0.6026 / 0.5326 |
| DetectGPT (T5 11B/Neo 2.7) | 0.5364 / 0.5172 / 0.4763 / 0.5100 | 0.3438 / 0.6894 / 0.5073 / 0.5135 |
| Fast (GPT J/GPT 2) | 0.9233 / 0.9186 / 0.7727 / 0.8715 | 0.7909 / 0.9524 / 0.7697 / 0.8377 |
| Fast (GPT J/Neo 2.7) | 0.9646 / 0.9190 / 0.7172 / 0.8669 | 0.8598 / 0.9622 / 0.7487 / 0.8569 |
| Fast (GPT J/GPT J) | 0.9591 / 0.9476 / 0.7063 / 0.8710 | 0.8750 / 0.9811 / 0.7428 / 0.8663 |

**Before/after in the text.** "RoBERTa base's AUROC decreases from 0.7474 to 0.6477, DetectGPT from 0.8342 to 0.5522, and Fast DetectGPT from 0.9641 to 0.8715, where Fast DetectGPT experiences the smallest relative downgrade" ([Bao et al. 2024, Appendix F.2](https://arxiv.org/abs/2310.05130)).

The preattack values 0.8342 and 0.9641 do **not** appear in Table 3. Table 3 gives 0.8223 for DetectGPT (T5 11B/Neo 2.7) and 0.9615 for Fast Detect (GPT J/Neo 2.7). The post attack values cited match the GPT 2 scorer rows of Table 11. The preattack baselines are therefore presumably the GPT 2 scorer configurations, which are not tabulated. **UNVERIFIED**

**Authors' caveat.** The authors attribute much of the drop to the paraphraser reducing "cross sentential coherence". They support this with the decoherence attack, which causes "a comparable drop in detection accuracy" ([Bao et al. 2024, Appendix F.2](https://arxiv.org/abs/2310.05130)).

### Nonnative writer bias
* No experiment: not reported in the paper.
* The Ethics statement acknowledges the risk: "as emphasized by Liang et al. (2023), LLM based detection systems may exhibit an elevated false positive rate when confronted with text from nonnative English speakers". It suggests swapping in LLMs "trained on more varied and representative corpora" ([Bao et al. 2024, Ethical Considerations](https://arxiv.org/abs/2310.05130)).

---

## 4. Binoculars (Hans et al., 2024)

### Signal
**Score.** The Binoculars score is log perplexity divided by log cross perplexity:

`B_{M1,M2}(s) = log PPL_{M1}(s) / log X-PPL_{M1,M2}(s)`

([Hans et al. 2024, Eq. 4](https://arxiv.org/abs/2401.12070))

**Components:**
* `log PPL_M(s) = −(1/L) Σ_i log(Y_{i,x_i})`: the average negative log likelihood of the observed tokens ([Hans et al. 2024, Eq. 2](https://arxiv.org/abs/2401.12070)).
* `log X-PPL_{M1,M2}(s) = −(1/L) Σ_i M1(s)_i · log(M2(s)_i)`: the average per token cross entropy between the two models' next token distributions on the same text. This requires a shared tokenizer ([Hans et al. 2024, Eq. 3](https://arxiv.org/abs/2401.12070)).

**Direction.** Lower B means more machine like. Human text has "a mean of around 1" ([Hans et al. 2024, §5.4](https://arxiv.org/abs/2401.12070)). The US Constitution scored 0.76, "well into the machine range" ([Hans et al. 2024, §5.3](https://arxiv.org/abs/2401.12070)).

**Motivation.** The "capybara problem": a prompt can make machine text have high perplexity. Cross perplexity normalises for this ([Hans et al. 2024, §3.2 to 3.3](https://arxiv.org/abs/2401.12070)).

**Default models:**
* The numerator PPL uses **Falcon 7B Instruct**.
* The denominator X PPL is computed "with Falcon 7B and Falcon 7B Instruct respectively".

([Hans et al. 2024, §3.3](https://arxiv.org/abs/2401.12070))

**Ablations:**
* Other model pairs are compared in Table 3 ([Hans et al. 2024, Appendix A.3, Table 3](https://arxiv.org/abs/2401.12070)).
* Fully instruction tuned Falcon 7B Instruct performs best as the performer M2 ([Hans et al. 2024, Appendix A.8, Figure 15](https://arxiv.org/abs/2401.12070)).

### Compute cost
* **Two models, Falcon 7B and Falcon 7B Instruct.** Each needs one forward pass over the text to produce the logits Y used in Eqs. 2 to 3 (derived from [Hans et al. 2024, Eqs. 2 to 4](https://arxiv.org/abs/2401.12070)). That is 2 forward passes of a 7B model per text, with no sampling or perturbation.
* **Not reported in the paper:**
  * No count of forward passes is stated.
  * No timing, throughput or speedup figures are given.
* **Limitation noted:** "Due to limited GPU memory, we do not perform broader studies with larger (30B+) open source models" ([Hans et al. 2024, §6](https://arxiv.org/abs/2401.12070)).

### Headline detection numbers
**Metric.** The primary metric is **TPR at 0.01% FPR**: "we focus on true positive rates (TPR) at low false positive rates (FPR), and adopt a standard FPR threshold of 0.01%" ([Hans et al. 2024, §4.2](https://arxiv.org/abs/2401.12070)). The authors also report AUC, F1, and TPR at 0.1%, 1% and 5% FPR in the appendix.

**Abstract headline.** "Binoculars detects over 90% of generated samples from ChatGPT (and other LLMs) at a false positive rate of 0.01%" ([Hans et al. 2024, Abstract](https://arxiv.org/abs/2401.12070)).

**Figure 1.** TPR at 0.01% FPR on ChatGPT generated text, using the Ghostbuster datasets of Verma et al. 2023 ([Hans et al. 2024, Figure 1](https://arxiv.org/abs/2401.12070)):
* Values were read from the bar labels in the v3 Figure 1 SVG. The text is outlined as glyphs and was rendered to an image to read it.
* There is no table version. Each value can be cross checked against Table 4 below.

| Detector | News | Creative Writing | Student Essay |
|---|---|---|---|
| **Binoculars** | 0.949 | 0.935 | 0.976 |
| Ghostbuster (OOD) | 0.911 | 0.900 | 0.869 |
| GPTZero | 0.991 | 0.505 | 0.647 |
| DetectGPT (LLaMA 2 to 13B) | 0.010 | 0.045 | 0.010 |
| Fast DetectGPT | 0.966 | 0.905 | 0.918 |
| DNA GPT | 0.004 | 0.000 | 0.007 |

**Notes on Figure 1:**
* Bootstrap standard errors for Binoculars' TPR at 0.01% FPR are 2.92e 3 (News), 2.15e 3 (Creative Writing) and 3.89e 3 (Student Essay). The AUC standard errors are 2.12e 5, 2.50e 4 and 8.99e 5 ([Hans et al. 2024, Appendix A.9, Table 7](https://arxiv.org/abs/2401.12070)).
* In this comparison, DetectGPT used LLaMA 2 to 13B as the scorer with T5 for mask filling. Fast DetectGPT used GPT J 6B for reference and GPT Neo 2.7B for scoring ([Hans et al. 2024, Appendix A.1.3](https://arxiv.org/abs/2401.12070)).

**Table 4.** TPR at several FPRs, comparing PPL alone, X PPL alone and Binoculars ([Hans et al. 2024, Appendix, Table 4](https://arxiv.org/abs/2401.12070)):

| Dataset | Detector | AUC | TPR @0.01% FPR | @0.1% | @1% | @5% |
|---|---|---|---|---|---|---|
| Writing Prompts | Binoculars Falcon | 1.00 | 0.93 | 0.93 | 0.96 | 1.00 |
| Writing Prompts | Binoculars LLaMA | 1.00 | 0.95 | 0.95 | 0.98 | 1.00 |
| Writing Prompts | Falcon PPL (alone) | 1.00 | 0.86 | 0.86 | 0.94 | 0.98 |
| News | Binoculars Falcon | 1.00 | 0.95 | 0.99 | 1.00 | 1.00 |
| News | Binoculars LLaMA | 1.00 | 0.99 | 0.99 | 1.00 | 1.00 |
| News | Falcon PPL (alone) | 0.99 | 0.65 | 0.77 | 0.90 | 0.95 |
| Essay | Binoculars Falcon | 1.00 | 0.98 | 0.98 | 0.99 | 1.00 |
| Essay | Binoculars LLaMA | 1.00 | 0.99 | 0.99 | 1.00 | 1.00 |
| Essay | Falcon PPL (alone) | 1.00 | 0.78 | 0.78 | 0.88 | 0.99 |

**Table 3** ([Hans et al. 2024, Table 3](https://arxiv.org/abs/2401.12070)):
* Table 3 reports TPR at 0.01% FPR for many (PPL scorer, X PPL pair) rows "evaluated on our reference datasets".
* The first row is the default Falcon 7B Instruct / (Falcon 7B, Falcon 7B Instruct) and shows TPR@0.01% FPR **100.0000** and AUC **1.0000**.
* The arXiv v3 HTML has **no dataset column**, so it is unclear which dataset each row refers to. Per row dataset attribution is **UNVERIFIED**.

**Other headline numbers:**
* **Open Orca**, using the global threshold, accuracy on machine only samples: "Binoculars detects 92% of GPT 3 samples and 89.57% of GPT 4 samples" ([Hans et al. 2024, §5.4](https://arxiv.org/abs/2401.12070)).
* **GPT 4 and Gemini APIs, March 2024**, 129 Open Orca prompts each ([Hans et al. 2024, Appendix A.10, Table 8](https://arxiv.org/abs/2401.12070)):
  * gemini 1.0 pro latest: accuracy 96.89%, FNR 3.10%.
  * gpt 4: accuracy 41.86%, **FNR 58.13%**.
* **Low resource languages (M4):** "reasonable precision but poor recall" in Bulgarian, Urdu and two other languages ([Hans et al. 2024, §5.2, Figure 6](https://arxiv.org/abs/2401.12070)). The figure values are not given as text. **UNVERIFIED**

### Paraphrase robustness
* No paraphrase attack experiment: not reported in the paper.
* The authors state: "we do not consider explicit efforts to bypass detection" ([Hans et al. 2024, §6](https://arxiv.org/abs/2401.12070)). They also say they "do not guarantee any performance in settings where a motivated adversary tries to fool our system" ([Hans et al. 2024, Impact Statement](https://arxiv.org/abs/2401.12070)).
* **Closest related test: prompt stylisation.** LLaMA 2 to 13B chat was prompted to write like Carl Sagan, in a "nonrobotic" style, or like a pirate. "The biggest impact we observe arises when asking for pirate sounding output, and this only decreases the sensitivity (increases the false negative rate) by 1%" ([Hans et al. 2024, §5.4, Figure 8](https://arxiv.org/abs/2401.12070)).
* Third party paraphrase results for Binoculars are in the RAID section below.

### Nonnative writer bias
This is an explicit experiment, under the heading "False positive rates on nonnative speakers' writing" ([Hans et al. 2024, §5.2](https://arxiv.org/abs/2401.12070)).

**Data.** Essays from **EssayForum**, "a web page for ESL students to improve their academic writing". The dataset contains "both the original essays, as well as grammar corrected versions" ([Hans et al. 2024, §5.2](https://arxiv.org/abs/2401.12070)).

**Result.** "Binoculars attains equal accuracy at 99.67% for both corrected and uncorrected essay datasets (see Figure 7)" ([Hans et al. 2024, §5.2](https://arxiv.org/abs/2401.12070)).
* Because all the essays are human written, an accuracy of 99.67% implies an FPR of roughly 0.33% on this set. This is an inference; the paper does not state the FPR directly.

**Score distributions.** The ESL score distribution "highly overlaps with that of grammar corrected versions of the same essays". Figure 7 caption: "Both original and corrected essays are unambiguously classified as human written" ([Hans et al. 2024, §5.2, Figure 7](https://arxiv.org/abs/2401.12070)).
* Read from the rendered Figure 7: both distributions centre near a score of about 1.0, and the "Binoculars Optimal Threshold" line sits near 0.90.

**Unstated details:**
* The number of essays is not stated in the text. **UNVERIFIED**
* The paper calls the dataset "similar" to the TOEFL set of Liang et al. (2023). It is **not** the TOEFL set itself.

**Context the paper gives.** It cites Liang et al. (2023): "TOEFL essays written by nonnative English speakers were wrongly marked as machine generated 48 to 76% of the time by commercial detectors" ([Hans et al. 2024, §2](https://arxiv.org/abs/2401.12070)). That figure comes from Liang et al., not from a Binoculars measurement.

---

## 5. RAID benchmark (Dugan et al., ACL 2024): results for these four methods

### What metric RAID uses
**Name.** The metric is **"Accuracy at FPR=5%"**, also written "Accuracy Score at FPR=5%" in table captions.

**Definition.** "we select a threshold for each model such that the resulting false positive rate of the detector is 5%. In practical terms, accuracy at a fixed FPR of 5% represents how well each detector identifies machine generated text while only mis classifying 5% of human written text" ([Dugan et al. 2024, §5.2](https://arxiv.org/abs/2405.07940)).

**Answer to "is it TPR at FPR=5%?"** Functionally yes: it is the percentage of *machine generated* texts detected when the threshold is set to 5% FPR on human text. Appendix B phrases it as "What percentage of generations are detected given that we tolerate an x% chance of wrongly accusing someone" ([Dugan et al. 2024, Appendix B](https://arxiv.org/abs/2405.07940)). However, **the paper itself calls it "accuracy", never "TPR"**. A text search of the paper finds no use of "TPR".

**Thresholds are tuned per domain.** "we find the threshold for each detector for each domain that results in 5% FPR on that domain" ([Dugan et al. 2024, Appendix C, Table 13](https://arxiv.org/abs/2405.07940)).

**Why not F1.** Appendix B argues against F1 and precision. The dataset has "a roughly 40:1 ratio of generated to human written text", so precision would be misleading ([Dugan et al. 2024, Appendix B](https://arxiv.org/abs/2405.07940)).

**Scale.** RAID contains "roughly 6.2 million generations" ([Dugan et al. 2024, Figure 2 caption](https://arxiv.org/abs/2405.07940)). The paraphrase attack uses DIPPER 11B, "a fine tuned version of T5 11B", with "sentence interval of 3 with lexical diversity of 60 and order diversity of 0", applied to 100% of outputs ([Dugan et al. 2024, §3.6, Appendix E.4, Table 11](https://arxiv.org/abs/2405.07940)).

### Detector configurations RAID used
RAID used each repository's default models ([Dugan et al. 2024, Appendix F.1](https://arxiv.org/abs/2405.07940)):
* **GLTR:** "cutoff set at rank=10 and the language model set to GPT2 small".
* **FastDetectGPT:** scoring model GPT Neo 2.7B and reference model "GPT J 7B". GPT J is a 6B model. "7B" is as printed in RAID, so treat it as a likely typo; this is not independently verified.
* **Binoculars:** Falcon 7B and Falcon 7B Instruct, using the official repository code.
* **DetectGPT (original): NOT evaluated in RAID.**
  * The metric based detectors tested are "GLTR, Binoculars, Fast DetectGPT, LLMDet" ([Dugan et al. 2024, §5.1](https://arxiv.org/abs/2405.07940)).
  * DetectGPT appears only as a reference and in the description of FastDetectGPT.
  * **There are no DetectGPT numbers in the RAID paper.** The RAID online leaderboard was not consulted for this file, because the task scope was the paper.

### Scores (Accuracy at FPR=5%)
**Overall, nonadversarial.** "Total" column of Table 15, which equals the "None" column of Table 16 ([Dugan et al. 2024, Table 15](https://arxiv.org/abs/2405.07940); [Table 16](https://arxiv.org/abs/2405.07940)):

| Detector | Overall (no attack) | Paraphrase attack (PP) |
|---|---|---|
| GLTR | 62.6 | 47.2 (down 15.4) |
| Fast DetectGPT ("F DGPT") | 73.6 | 71.8 |
| Binoculars | 79.6 | 80.3 (+0.7) |
| DetectGPT | not evaluated in the paper | not evaluated in the paper |

**Sources for the paraphrase column:**
* Paraphrase scores come from Table 16, which covers all detectors and all 11 attacks ([Dugan et al. 2024, Table 16](https://arxiv.org/abs/2405.07940)).
* The bracketed deltas for GLTR and Binoculars are as printed in Table 6, which covers only "select detectors" ([Dugan et al. 2024, Table 6](https://arxiv.org/abs/2405.07940)).
* **Fast DetectGPT does not appear in Table 6.** Its paraphrase score of 71.8 comes only from Table 16, which prints no delta.

**Table 16, all attacks, for the three evaluated methods** ([Dugan et al. 2024, Table 16](https://arxiv.org/abs/2405.07940)):

| Detector | None | AS | AD | HG | IP | NS | PP | MS | SYN | ULS | WSA | ZWS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GLTR | 62.6 | 61.2 | 52.1 | 24.3 | 61.4 | 59.9 | 47.2 | 59.8 | 31.2 | 48.1 | 45.8 | 97.2 |
| F DGPT | 73.6 | 71.6 | 64.7 | 51.4 | 72.0 | 68.2 | 71.8 | 70.7 | 34.0 | 60.4 | 64.4 | 98.9 |
| Binoculars | 79.6 | 78.2 | 74.3 | 37.7 | 71.7 | 77.1 | 80.3 | 78.0 | 43.5 | 73.8 | 70.1 | 99.1 |

Abbreviations: AS Alternative Spelling, AD Article Deletion, HG Homoglyph, IP Insert Paragraphs, NS Number Swap, PP Paraphrase, MS Misspelling, SYN Synonym Swap, ULS Upper Lower Swap, WSA Whitespace Addition, ZWS Zero Width Space ([Dugan et al. 2024, Table 16 caption](https://arxiv.org/abs/2405.07940)).

**Missing aggregate.** The paper does **not** report one aggregate "overall including all attacks" score per detector. Only the per attack columns are given.

**In the text:** "Binoculars and other metric based methods degrade as much as 36.1% when a small portion of words are swapped with synonyms" ([Dugan et al. 2024, §6 Finding 6](https://arxiv.org/abs/2405.07940)).

### Other RAID results relevant to these methods
**Table 4: FPR at naive thresholds τ** (0.25 / 0.5 / 0.75 / 0.95), without calibration ([Dugan et al. 2024, Table 4](https://arxiv.org/abs/2405.07940)):
* GLTR: 100% / 99.3% / 21.0% / 0.05%.
* F DetectGPT: 47.3% / 23.2% / 13.1% / 1.70%.
* Binoculars: 0.07% / 0.00% / 0.00% / 0.00%.

**Finding 2: minimum achievable FPR.** "Some detectors failed to achieve the lowest FPR we tested, plateauing at 16.9% (ZeroGPT), 0.88% (FastDetectGPT), and 0.62% (Originality) ... Binoculars ... was particularly strong at low FPR" ([Dugan et al. 2024, §6 Finding 2, Figure 4](https://arxiv.org/abs/2405.07940)).

**Table 5: decoding strategy and repetition penalty.** The hardest cell is open source nonchat models with sampling and a repetition penalty ([Dugan et al. 2024, Table 5](https://arxiv.org/abs/2405.07940)):
* GLTR: 0.5.
* F DetectGPT: 0.6.
* Binoculars: 0.6.

The same three detectors on open source chat models with greedy decoding and no repetition penalty:
* GLTR: 89.8.
* F DetectGPT: 98.6.
* Binoculars: 99.9.

**Table 7: RAID extra (Code / Czech / German / Total)** ([Dugan et al. 2024, Table 7](https://arxiv.org/abs/2405.07940)):
* GLTR: 40.7 / 51.9 / 68.9 / 56.7.
* F DetectGPT: 51.1 / 55.2 / 75.5 / 62.7.
* Binoculars: 59.9 / 67.0 / 76.7 / 69.6.

**Nonnative bias.** RAID runs no ESL experiment. The Ethics Statement cites Liang et al. (2023c) and says "Our results also support this and suggest that the problem of false positives remains unsolved". No ESL specific numbers are reported ([Dugan et al. 2024, Ethics Statement](https://arxiv.org/abs/2405.07940)).

---

## Summary of gaps and UNVERIFIED items
1. **GLTR:** BERT model size is not stated. No TPR@low FPR, paraphrase or ESL results.
2. **DetectGPT:**
   * Per revision level AUROC exists only as the Figure 5 plot. **UNVERIFIED**
   * No wall clock cost in its own paper.
   * No TPR@low FPR or ESL experiment.
   * Algorithm 1 prints `√σ̃_x` as the normaliser (copied as printed).
3. **Fast DetectGPT:**
   * 80% (Introduction) versus 87% (§3.4) recall at 1% FPR on ChatGPT is an internal inconsistency.
   * §3.4 references "Figure 4", but the ROC plot is Figure 3.
   * Preattack paraphrase baselines (0.8342 and 0.9641) are not traceable to a table. **UNVERIFIED**
4. **Binoculars:**
   * Figure 1 values were read from rendered SVG bar labels. They agree with Table 4 to two decimals.
   * Table 3 dataset attribution is missing in the HTML. **UNVERIFIED**
   * The EssayForum sample size is not stated. **UNVERIFIED**
   * M4 / low resource language numbers exist only in figures. **UNVERIFIED**
   * Compute cost is not reported.
5. **RAID:**
   * DetectGPT was not evaluated.
   * No overall with attacks aggregate is reported.
   * Fast DetectGPT is absent from Table 6 and appears only in Table 16.
   * "GPT J 7B" is printed as is.
6. **Versions:** the camera ready ACL, ICML and ICLR PDFs were not cross checked against the arXiv versions listed at the top. Table and figure numbering could differ.
