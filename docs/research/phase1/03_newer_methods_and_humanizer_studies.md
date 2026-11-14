# Phase 1: Methods that beat the classic baselines (2024 to late 2026)

Researched 14 Nov 2026 for Detechum. Every number has an inline source. Anything I could not check against a primary source is marked **UNVERIFIED**. Baselines covered elsewhere (GLTR, DetectGPT, Fast DetectGPT, Binoculars, Ghostbuster, RoBERTa, DIPPER, Kirchenbauer) appear here only as comparison points.

Abbreviations: **TPR@k%** = true positive rate (recall on AI text) at a k% false positive rate on human text. **SR** = self reported by the method's authors or vendor. **IND** = independent evaluation.

---

## 1. RAID leaderboard (Dugan et al., ACL 2024)

### 1.1 Access and method

* **Accessed 14 Nov 2026.** The page at https://raid-bench.xyz/leaderboard is a JavaScript app; WebFetch received only the title. I rebuilt the ranking from the same per submission JSON files the site loads: index at https://raid-bench.xyz/data/submissions/_index.json, files at `https://raid-bench.xyz/data/submissions/<name>.json`. These files are copies of `leaderboard/submissions/<name>/results.json` in https://github.com/liamdugan/raid; the script that copies them is https://raw.githubusercontent.com/liamdugan/raid/main/leaderboard/copy-results-to-web-dist.sh.
* The newest repo commit on the access date was 12 Nov 2026 ("Merge pull request #237 … aicheck v5r") (GitHub API, https://api.github.com/repos/liamdugan/raid/commits).
* **63 submissions in all; 59 have a full aggregate score.** The other four have no `all` aggregate: Binoculars and FastDetectGPT (incomplete splits), and Gaussian Extreme and Luminar (null accuracy). Each file carries the note "This submission will not appear in the main leaderboard" (e.g. https://raid-bench.xyz/data/submissions/binoculars.json).
* **Cross check.** A vendor blog dated August 2026 listed the leaderboard at that time as Zhuque #1 at 99.80%, MELD #2 at 99.78%, Trinka #3 at 99.76%, QuillBot #7 at 99.62%, Slop or Not #8 at 99.52%, Grammarly #9 at 99.47% and GPTZero #16 at 97.24%, "43 submissions, 4 partial" (https://slopornot.ai/blog/slop-or-not-raid-benchmark-ai-detector-accuracy). Every one of those scores matches my recomputation exactly. My ranks differ only where entries were added after August (Winston, GPTTrace, XYZ, FLAIRD, ParaTrace v8 and others).

### 1.2 What the metric is (checked precisely)

* **Ranking metric: "accuracy" at FPR = 5%, i.e. TPR@5%.** Default view: all domains, all generators, all decodings, adversarial attacks included (`score_agg.all.accuracy["0.05"]`). Each file also reports TPR@1% and AUROC. The RAID paper's definition: thresholds are chosen so a detector "only mis classif[ies] 5% of human written text", and Appendix C sets them **per domain** (https://arxiv.org/html/2405.07940). The evaluation CLI defaults to `--target_fpr 0.05` (https://github.com/liamdugan/raid).
* **Calibration caveat that matters for Detechum.** The evaluator sets the thresholds per domain on the hidden human test texts. The `thresholds` and `fpr` fields show it: for MELD, the 5% thresholds range from 0.0139 (recipes) to 0.2427 (abstracts) (https://raid-bench.xyz/data/submissions/meld.json). So RAID uses an **oracle threshold for each domain**. It does not test whether a detector's own threshold or probability is calibrated.
* **Contamination caveat.** RAID train has labels and covers the same 8 domains as RAID test, whose labels are hidden (https://github.com/liamdugan/raid). Several top entries say they trained on RAID train: GPTTrace's card says it was trained on RAID train with held out titles excluded (https://huggingface.co/nakas/gpttrace-v8s-1b); DeBERTa ConPara lists RAID in its training corpora (https://arxiv.org/abs/2610.00883); one entry is called "ParaTrace v8 (RAID tuned)". Top RAID scores are therefore largely **in distribution** results.

### 1.3 Top entries (TPR at fixed FPR, in %; recomputed from the leaderboard JSON files)

Columns: TPR@5% and TPR@1% overall (attacks included), AUROC, TPR@5% with no attack, TPR@5% and TPR@1% on paraphrase, TPR@5% on synonym and homoglyph attacks. Source for each row: `https://raid-bench.xyz/data/submissions/<file>.json`.

| # | Detector (file) | All @5% | All @1% | AUROC | No attack @5% | Paraphrase @5% | Paraphrase @1% | Synonym @5% | Homoglyph @5% | `date_released` | Open or commercial |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Winston AI (`winston-ai`) | 99.98 | 99.89 | 99.89 | 100.00 | 99.92 | 99.34 | 99.99 | 99.98 | 24 Sep 2026 | Commercial, closed (gowinston.ai) |
| 2 | GPTTrace Ettin 1B v8s (`gpttrace-ettin1b`) | 99.93 | 99.54 | 99.94 | 99.95 | 99.72 | 97.54 | 99.87 | 99.95 | 1 Nov 2026 | **Open weights** (CC BY SA 4.0, Ettin 1B encoder, trained on RAID train) ([HF](https://huggingface.co/nakas/gpttrace-v8s-1b)); no paper |
| 3 | XYZ SCIENCE (`XYZ-SCIENCE-20261031`) | 99.91 | 99.35 | 99.94 | 99.95 | 99.53 | 95.68 | 99.83 | 99.95 | 31 Oct 2026 | Closed. Website only; nature UNVERIFIED |
| 4 | GPTTrace Ettin 150M (`gpttrace-ettin150`) | 99.80 | 98.91 | 99.89 | 99.90 | 99.19 | 93.06 | 99.65 | 99.90 | 16 Oct 2026 | Open weights (HF link in metadata) |
| 5 | Zhuque AI Detection Assistant, Tencent (`SevenModel`) | 99.80 | 98.33 | 99.83 | 99.95 | 98.84 | 91.97 | 99.70 | 99.85 | 14 Apr 2026 | Commercial, closed (matrix.tencent.com/ai detect) |
| 6 | MELD (`meld`) | 99.78 | 99.24 | 99.82 | 99.76 | 99.03 | 96.47 | 99.72 | 99.85 | 29 Apr 2026 | **Open weights** (MIT, gated, ModernBERT family Ettin 1B, anonymous, under review) ([HF](https://huggingface.co/anon-review-meld-2026/meld)); training data not stated |
| 7 | FLAIRD (`FLAIRD`) | 99.77 | 99.00 | 99.87 | 99.96 | 99.23 | 96.08 | 99.85 | 99.57 | 30 Sep 2026 | Unknown: no links, email only |
| 8 | Trinka AI (`trinka`) | 99.76 | 98.46 | 99.89 | 99.88 | 99.23 | 92.24 | 99.74 | 99.74 | 26 May 2026 | Commercial, closed |
| 9 | ParaTrace v8, RAID tuned (`paratrace-v8-raid`) | 99.76 | 99.20 | 99.24 | 99.80 | 99.62 | 98.04 | 99.58 | 99.80 | 16 Oct 2026 | Commercial site (paratrace.net); closed (UNVERIFIED) |
| 10 | FCM (`FCM`) | 99.67 | 98.49 | 99.83 | 99.92 | 99.04 | 95.08 | 99.80 | 99.42 | 1 Oct 2026 | Unknown (same contact as FLAIRD) |
| 11 | GiantMelon | 99.66 | 98.62 | 99.90 | 99.88 | 98.75 | 92.75 | 99.50 | 99.70 | 27 Nov 2025 | Unknown |
| 12 | Veredict Labs | 99.65 | 98.64 | 99.88 | 99.87 | 98.68 | 92.97 | 99.55 | 99.63 | 23 Jan 2025 | Commercial |
| 13 | provenance | 99.65 | 98.91 | 99.89 | 99.86 | 97.94 | 93.54 | 99.52 | 99.86 | 31 Oct 2026 | Unknown |
| 14 | SpeedAI | 99.62 | 98.55 | 99.85 | 99.86 | 98.68 | 92.39 | 99.48 | 99.64 | 8 May 2025 | Commercial |
| 15 | QuillBot | 99.62 | 98.10 | 99.62 | 99.72 | 99.03 | 94.07 | 99.34 | 99.61 | 30 Jan 2025 | Commercial |
| 18 | Grammarly | 99.47 | 98.21 | 99.87 | 99.91 | 98.88 | 95.66 | 99.72 | 99.21 | 9 Feb 2026 | Commercial |
| 19 | DeBERTa ConPara | 99.01 | 96.57 | 99.61 | 99.04 | 98.33 | 89.61 | 99.10 | 99.04 | 25 Aug 2026 | **Open** (paper, code and weights; AACL IJCNLP 2026) ([arXiv 2610.00883](https://arxiv.org/abs/2610.00883)) |
| 24 | GPTZero | 97.24 | 92.93 | 99.25 | 98.37 | 89.11 | 71.60 | 95.49 | 98.36 | 7 Oct 2025 | Commercial |
| 48 | DivEye | 80.62 | 59.11 | 95.15 | 93.63 | 74.36 | 45.10 | 67.10 | 61.60 | 20 Nov 2025 | Open (arXiv 2509.18880) |
| 53 | RADAR (NeurIPS 2023) | 63.91 | 43.12 | 81.92 | 65.61 | 62.36 | 44.06 | 62.74 | 44.83 | 7 Jul 2023 | Open |
| 56 | GLTR | 51.48 | 36.48 | 70.90 | 59.69 | 42.95 | 23.71 | 28.74 | 20.32 | 10 Jun 2019 | Open |
| unranked | Binoculars | n/a | n/a | n/a (no attack AUROC 84.40) | 78.98 (@1%: 69.54) | not submitted | not submitted | 42.06 | 36.10 | 22 Jan 2024 | Open |

Notes:
* **GPTZero.** Its no attack TPR@1% on the leaderboard is 95.72% (https://raid-bench.xyz/data/submissions/gptzero.json). That matches GPTZero's marketing claim of "95.7% … ~1% FPR" on RAID. I found that claim only in secondary sources and could not open GPTZero's own post, so the claim is UNVERIFIED, but the leaderboard number is primary.
* **Pangram and Originality.ai have no leaderboard submission.** There is no directory for either under `leaderboard/submissions` (GitHub API listing, 14 Nov 2026). Originality.ai appears only in the original RAID paper. Its TPR@5% was 85.0 with no attack and **96.7 under paraphrase**, against GPTZero 66.5 and 64.0 and Binoculars 79.6 and 80.3 (RAID paper Table 6, https://arxiv.org/html/2405.07940). Originality's blog says the version tested was "Originality.ai 2.0 Standard", now retired (https://originality.ai/blog/robust-ai-detection-study-raid).
* **RAID Shared Task (COLING 2025).** 9 teams submitted 23 detectors, and "multiple participants" exceeded 99% TPR at 5% FPR (https://arxiv.org/abs/2501.08913).
* **Takeaway.** At the top, RAID is saturated: 18 entries are at or above 99.47% TPR@5% with attacks included. Supervised encoders fine tuned on RAID train (Ettin, ModernBERT, DeBERTa) now match or beat commercial tools on the board. RAID does not include modern commercial humanizers, and it uses oracle thresholds per domain. Section 4.4 shows that tools near the top of RAID (QuillBot, Grammarly) are among the easiest to bypass with commercial humanizers.

---

## 2. Newer open methods with reported gains over Binoculars and Fast DetectGPT

All numbers in this section are SR unless marked otherwise.

### 2.1 DNA DetectLLM (NeurIPS 2025 main track)
* **Venue:** NeurIPS 2025 Main Conference Track, DOI 10.52202/085713 to 0065 (https://proceedings.neurips.cc/paper_files/paper/2025/hash/0287c393907259ae6a269fca5e3509cd-Abstract-Conference.html); arXiv 2509.15550. Code: github.com/Xiaoweizhu57/DNA DetectLLM.
* **Signal:** Zero shot. The text is repaired token by token toward the "ideal AI sequence" (each token's optimal choice). The **repair score** (the effort that takes) is compared with a calibrated threshold. Uses two models: Falcon 7B Instruct as reference and Falcon 7B as observer, a Binoculars style pair (https://arxiv.org/html/2509.15550v2).
* **Compute:** "under 0.8s" per sample (0.78 s) on 300 token texts, A100 80GB, batch size 1. Other repair orders took about 14 s (Table 10) (same source).
* **Headline AUROC, average:** 98.30 vs Binoculars 97.39 vs Fast DetectGPT 96.20 on XSum, WritingPrompts and Arxiv with GPT 4 Turbo, Gemini 2.0 Flash and Claude 3.7 Sonnet (Table 1). On public benchmarks the averages are 90.86 vs 86.08 vs 85.07 (Table 2). Per benchmark: M4 91.74 / 90.00 / 89.77; DetectRL Multi LLM 88.97 / 83.21 / 82.26; DetectRL Multi Domain 88.23 / 77.45 / 74.98; RealDet 94.48 / 93.64 / 93.25 (same source).
* **TPR at low FPR:** not reported as numbers; the paper says only that gains are "particularly pronounced under low false positive rate (FPR) conditions". Fixed threshold F1: 84.58 vs 81.05 vs 77.47 (Table 4).
* **Paraphrase (DIPPER, GPT 4 Turbo):** AUROC 98.02 vs Binoculars 97.23 vs Fast DetectGPT 96.70 (Table 6). The prose says "97.23%", which conflicts with the table; probably a typo.
* **Nonnative writer FPR:** not evaluated.

### 2.2 AdaDetectGPT (NeurIPS 2025)
* **Venue:** arXiv 2510.01268; the comments field says "Accepted by NeurIPS2025" (https://arxiv.org/abs/2510.01268). Code: github.com/Mamba413/AdaDetectGPT.
* **Signal:** Fast DetectGPT's statistic with a **learned witness function** on token log probabilities: a B spline basis fitted by solving a linear system, chosen to maximize a lower bound on TNR. It comes with finite sample bounds on TPR, FPR, TNR and FNR. Needs a small training set; the experiments used 500 human and 500 machine paragraphs from datasets other than the test set (https://arxiv.org/html/2510.01268v4).
* **Compute:** witness training "typically requires less than one minute", memory "below 0.5 GB"; inference costs the same as Fast DetectGPT (same source).
* **Headline numbers:** White box average AUC on SQuAD 0.8864 vs Fast DetectGPT 0.8571, Writing 0.9233 vs 0.8886, XSum 0.8379 vs 0.8009 (Table 1). Black box: GPT 4o 0.9589 vs Fast DetectGPT 0.9571 vs Binoculars 0.9552; Claude 3.5 Haiku 0.9478 vs 0.9439 vs 0.9440 (Table 2). The headline claim of "12.5% to 37%" is a relative gain, and in black box mode the absolute gains are under 1 AUC point.
* **TPR at low FPR:** theoretical bounds only, no empirical values.
* **Paraphrase:** e.g. 0.8781 vs 0.8679 for Fast DetectGPT (Table 3).
* **Nonnative writers:** not evaluated; only cited (Liang et al. 2023).

### 2.3 Lastde / Lastde++ (ICLR 2025)
* **Venue:** ICLR 2025 (https://proceedings.iclr.cc/paper_files/paper/2025/file/2fcd27d2806a6d4f616cb4e6084d74f3-Paper-Conference.pdf); arXiv 2410.06072. The name stands for "Likelihood and sequential token probability diversity entropy" (https://arxiv.org/html/2410.06072v1).
* **Signal:** Zero shot, no training. The token probability sequence is treated as a time series. Global log likelihood is divided by an aggregate of multiscale diversity entropy, which captures local fluctuation.
* **Compute:** Lastde++ uses 100 samples, "1/100 of Fast DetectGPT". When the scoring and sampling models are the same, it can be done "by only calling the model once".
* **Headline AUROC:** White box, 12 models: Lastde++ 98.85 vs Fast DetectGPT 97.82. Black box, including GPT 4 Turbo: 91.47 vs 85.68. No Binoculars comparison numbers.
* **Paraphrase (T5 paraphraser, not DIPPER):** AUROC drop on XSum 8.48 vs 10.6 for Fast DetectGPT (white box). On black box Reddit, Lastde++ dropped more (3.36 vs 3.00) but still scored higher afterward (87.90 vs 83.04).
* **TPR at low FPR:** not reported. **Nonnative:** not evaluated; German and Chinese data were tested.

### 2.4 Glimpse (ICLR 2025)
* **Venue:** arXiv 2412.11506; comments: "ICLR 2025 camera version" (https://arxiv.org/abs/2412.11506). Code: github.com/baoguangsheng/glimpse. Same group as Fast DetectGPT.
* **Signal:** Estimates the **full token distribution** from the top K logprobs a proprietary API returns (Geometric, Zipfian or MLP estimator). This lets white box statistics (Entropy, Rank, Log Rank, Fast DetectGPT) run on GPT 3.5/4 class scoring models.
* **Headline:** Fast DetectGPT with GPT 3.5 reaches "an average AUROC of about 0.95 in five latest source models" (abstract, same source).
* **Cost:** one API call per text, which needs logprob access. TPR at low FPR, paraphrase robustness and nonnative FPR: UNVERIFIED (the HTML full text timed out twice).

### 2.5 ImBD, Imitate Before Detect (AAAI 2025)
* **Venue:** AAAI 25, DOI 10.1609/aaai.v39i22.34525, pp. 23559 to 23567 (https://ojs.aaai.org/index.php/AAAI/article/view/34525); arXiv 2412.10432.
* **Signal:** "Style preference optimization" (SPO) fine tunes a scoring LLM toward machine style preferences. The score is a style conditional probability curvature (Style CPC). It targets **machine revised** (polished or expanded) text.
* **Headline:** AUC gains of 13% on text revised by open source LLMs, and 5% and 19% on GPT 3.5 and GPT 4o revisions. Beats GPTZero "with only 1,000 samples and five minutes of SPO" (abstract).
* TPR at low FPR, paraphrase and nonnative results: UNVERIFIED (full text not read).

### 2.6 DeTeCtive (NeurIPS 2024)
* **Venue:** NeurIPS 2024 main (https://proceedings.neurips.cc/paper_files/paper/2024/hash/a117a3cd54b7affad04618c77c2fb18b-Abstract.html); arXiv 2410.20964. Code: github.com/heyongxin233/DeTeCtive.
* **Signal:** Supervised multi level contrastive learning over writing style, plus dense retrieval (kNN). "Training Free Incremental Adaptation" adds new OOD data to the database without retraining.
* **Headline:** the abstract gives no numbers ("outperforms existing approaches by a large margin" OOD) (https://arxiv.org/abs/2410.20964). Benchmark numbers: UNVERIFIED (not read).

### 2.7 RADAR (NeurIPS 2023) and Raidar (ICLR 2024)
* **RADAR:** Detector and paraphraser trained adversarially against each other (https://arxiv.org/abs/2307.03838). **IND results are poor:** RAID leaderboard TPR@5% 63.91 overall and 62.36 on paraphrase (https://raid-bench.xyz/data/submissions/radar.json). In DAMAGE (Pangram authors) RADAR's TPR@5% was 3.33% on AI text and 5.05% on humanized text (https://arxiv.org/html/2501.03437v1). On humanized federal texts its AUROC was 0.650 (https://arxiv.org/html/2611.00359).
* **Raidar:** An LLM rewrites the input; the detector measures the edit distance, since LLMs change AI text less. F1 gains "up to 29 points" (https://arxiv.org/abs/2401.12970). One secondary aggregator lists Raidar as best on the Humanize 16K *after attack* split at 0.911 AUROC (https://www.sota2.com/research/sota/ai-text-detection-on-humanize-after-16k). That figure comes from an aggregator and is UNVERIFIED against the Triospect paper.

### 2.8 Other 2025 to 2026 open work with reported gains

* **MCP, Multiscaled Conformal Prediction (ACL 2025; arXiv 2505.05084).** Not a new score: it is a **calibration wrapper** that guarantees "no more than α" of future human texts are flagged, using thresholds per length bin. Applied to the baselines (https://arxiv.org/html/2505.05084v2):
  * TPR@1%, vanilla → MCP: Binoculars RealDet 78.98 → 86.28, MAGE 56.04 → 75.80, M4 64.52 → 66.68, RAID 67.50 → 70.33. Fast DetectGPT RealDet 63.74 → 73.20, MAGE 57.00 → 67.92.
  * TPR@0.5%: Binoculars MAGE 28.52 → 73.32.
  * Realized FPR on RealDet: Fast DetectGPT 9.84% → 1.98%, Binoculars 7.68% → 0.72%. Platt scaling and isotonic regression stayed above 5% (Table 7).
  * Also releases RealDet: 847,909 texts, 15 domains, 22 LLMs. Nonnative writers not evaluated.
* **Triospect (TACL; arXiv 2606.31074, June 2026).** Same group as Fast DetectGPT and Glimpse. Adds "content" and "expression" perspectives to a statistical detector. SR: +22.3% AUROC and +13% TPR@1% on the Humanize 16K after attack subset; +9.1% AUROC and +22% TPR@1% on adversarial RAID, both "over the strong baseline" (https://arxiv.org/abs/2606.31074). Humanize 16K is built with commercial humanizers including BypassGPT, Humbot and Undetectable AI (search result summary of the paper; full text timed out). Detailed tables are UNVERIFIED.
* **DeBERTa ConPara (AACL IJCNLP 2026; arXiv 2610.00883).** Open supervised DeBERTa trained on HC3 Plus, M4, MAGE and RAID. SR: 99.61% AUROC, 99.01% TPR@5% and 96.57% TPR@1% on the RAID hidden test; 93.14% balanced accuracy on HC3 Plus and MAGE at a fixed threshold (https://arxiv.org/abs/2610.00883). These match the leaderboard file (99.01 / 96.57 / 99.61; https://raid-bench.xyz/data/submissions/DeBERTa-ConPara.json), so they are **corroborated**.
  * Key engineering finding: **Unicode normalization at inference** raises homoglyph and zero width space TPR from 11.05% and 1.12% to 96.98%. Normalizing the *training* data instead hurts.
  * Negative results: paraphrase augmentation and contrastive learning did not help.
* **GPTTrace (open weights, no paper).** SR on its card (https://huggingface.co/nakas/gpttrace-v8s-1b): RAID held out TPR@5% 99.94; MAGE paraphrased AUROC 0.919; **commercial humanizers TPR@5% 0.791**, down from 0.956 for v5, which the card lists as a weak spot. The RAID figure is corroborated by the leaderboard (99.93 overall).
* **Luminol AIDetect (arXiv 2604.25860, under review).** Perplexity before and after random shuffling of the text, followed by density estimation. SR: "up to 17x lower FPR" across 8 domains, 11 attacks and 18 languages (https://arxiv.org/abs/2604.25860). No head to head numbers checked: UNVERIFIED.
* **NormDetect (arXiv 2610.41459).** A search snippet describes Binoculars on Unicode normalized text plus a learned head per section. The abstract page timed out, so it is **UNVERIFIED**.
* **DivEye (arXiv 2509.18880).** IND on RAID: 80.62 TPR@5% overall and 74.36 on paraphrase (https://raid-bench.xyz/data/submissions/diveye.json).

**Nonnative writer FPR:** None of the open methods above reports it (checked for DNA DetectLLM, AdaDetectGPT, Lastde and MCP). The reference result is still Liang et al. 2023: a 61.22% average FPR on 91 TOEFL essays (https://arxiv.org/pdf/2304.02819).

---

## 3. Commercial detectors: self reported claims vs independent evidence

### 3.1 Pangram Labs
**Self reported:**
* **2024 report** (arXiv 2402.14873, v3 dated 29 Jul 2024): "over 38 times lower error rates" than DetectGPT and commercial tools on 10 domains and 8 LLMs (https://arxiv.org/abs/2402.14873).
* **DAMAGE** (arXiv 2501.03437, by Pangram authors Masrour, Emi and Spero): audited 19 humanizer and paraphraser tools (list in §4.1). TPR@5% on academic text, AI → humanized AI (https://arxiv.org/html/2501.03437v1):
  * GPTZero 99.73% → 60.04%
  * Binoculars 94.15% → 28.23%
  * RADAR 3.33% → 5.05%
  * DAMAGE 100.00% → 98.26%
  
  On RAID, TPR@5% for paraphrase and synonym: DAMAGE 93.0 and 97.0, Binoculars 80.3 and 43.5, GPTZero 64.0 and 61.0. DAMAGE's FPR at the default threshold is 3.40%.
* **Pangram 4 Technical Report** (arXiv 2607.27183, 29 Jul 2026, Pangram and UMD) (https://arxiv.org/html/2607.27183v1):
  * Architecture: open weight MoE backbone with LoRA adapters, a 3 class head per token, a humanizer probe, and CRF decoding.
  * Overall English: AUROC 0.9916. FPR 0.0041% (95% CI 0.0032 to 0.0050%) on more than a million human texts. FNR 0.3396%.
  * **Nonnative English FPR: 1 false positive in 24,586 (0.0041%)**; 0 on ELLIPSE, ICNALE and TOEFL; PELIC 1 in 15,005.
  * Humanized text flagged as AI: 97.67%. TPR per commercial humanizer ranges from 91.52% to 99.39%, with tools anonymized as A to F.
  * UChicago benchmark, TPR@1% on humanized full length text: **Pangram 4 98.93%, Originality 28.49%, GPTZero 44.32%**. On humanized text under 50 words: Pangram 4 73.32%, GPTZero 0.00%.
  * Perkins benchmark, accuracy on baseline / manipulated AI text: Pangram 4 100.0% / 94.1%, Copyleaks 73.9% / 58.7%, Turnitin 50.0% / 7.9%, GPTZero 26.4% / 16.7%.
  * Regressions in its own tables: DetectRL F1 95.30 vs 96.70 for Pangram 3; Sem Detect TPR@0.1% 95.5% vs 100.0%.
  * The comparisons were run by Pangram on third party datasets; there is no external replication. **Not on the RAID leaderboard.**

**Independent evidence:**
* **Jabarian & Imas, NBER WP 34223 (Sept 2025).** Evaluated Pangram, OriginalityAI, GPTZero and RoBERTa. Pangram had "near zero FNR and FPR" that held across short passages (≤50 words) and humanizers (StealthGPT), and was the only tool to meet a strict FPR cap of 0.005 without losing accuracy (https://www.nber.org/papers/w34223). The per detector numbers are in the PDF, which I could not render: **UNVERIFIED**. Pangram's own report quotes figures on this benchmark (above), but those are Pangram rerunning it, not the authors' numbers.
* **Karr et al., Notre Dame (arXiv 2608.11256, Aug 2026; acknowledgments thank Pangram for API access).** Pangram 3.2 TPR at τ=0.5 on AI rewritten abstracts: 80.6% (2013 to 15) and 86.5% (2023 to 25). After **Undetectable AI v11** humanization: **1.5% and 3.4%**. GPTZero: 55.8% and 61.6% before, 4.0% and 3.9% after. Flag rate on unmodified 2023 to 25 human abstracts: Pangram 14.9%, GPTZero 8.9%; theology 26.6% and political science 24.1% for Pangram (https://arxiv.org/html/2608.11256v2). This strongly contradicts the vendor's humanizer claims. Caveats: a single fixed threshold, published abstracts rather than student essays, and possible undisclosed AI use in the "human" abstracts.
* **AI Humanizer Benchmark, Nov 2026** (data: §4.4): Pangram had the lowest mean human probability on humanized outputs, 0.054.
* **Xu et al., "Base Models Look Human To AI Detectors"** (arXiv 2605.19516, CMU): GPTZero and Pangram often judge **base model** (noninstruction tuned) text "overwhelmingly human". The iterative paraphrasing attack HIP evades both (https://arxiv.org/abs/2605.19516). The abstract gives no numbers.

### 3.2 GPTZero
**Self reported** (arXiv 2602.13042, Feb 2026, GPTZero 4.1b; https://arxiv.org/html/2602.13042):
* AUC / accuracy / recall at 1% FPR: Abstracts 99.9 / 99.4 / 99.2, Essays 99.9 / 99.8 / 99.7. Pangram 3.1 on the same: 92.8 / 93.6 / 87.2 and 99.9 / 99.8 / 99.8. Binoculars on Abstracts: 40.0 / 49.5 / 0.0.
* Recall on bypassers (9 services): GPTZero 93.5%, Originality 57.3%, Pangram 49.7%.
* No ESL FPR and no RAID numbers.

**Independent evidence:**
* RAID leaderboard: 97.24 TPR@5% overall, 89.11 paraphrase @5%, 71.60 paraphrase @1% (https://raid-bench.xyz/data/submissions/gptzero.json).
* RAID paper (older version): 66.5 with no attack, 64.0 on paraphrase (https://arxiv.org/html/2405.07940).
* Karr et al.: 3.9 to 4.0% TPR after Undetectable AI (above).
* AI Humanizer Benchmark Nov 2026: mean human probability 0.430 on humanized text (§4.4).
* Each vendor's report ranks itself first against the others (GPTZero's vs Pangram 4's). Treat both as SR.

### 3.3 Originality.ai
* **SR:** Turbo 3.0.2 "99%+" accuracy and up to 97% on humanized text; FPR 1.5%. The search snippets also say the Turbo model was retired in September 2026 (originality.ai pages via search). Not opened directly: **UNVERIFIED**.
* **IND:**
  * RAID paper: TPR@5% 85.0 with no attack and 96.7 on paraphrase (best in the paper). Weak on homoglyph and zero width attacks per its blog (https://arxiv.org/html/2405.07940; https://originality.ai/blog/robust-ai-detection-study-raid).
  * Arabic study (arXiv 2511.16690): Originality was the best commercial tool at 92% accuracy, but fell to **12%** on human articles lightly polished by Mistral or Gemma 3 (https://arxiv.org/abs/2511.16690).
  * AI Humanizer Benchmark: mean human probability on humanized text was **0.722 in Oct 2026 and 0.110 in Nov 2026**. That suggests a model change between cycles (my computation, §4.4).

### 3.4 Turnitin
* **SR:** FPR under 1% for documents with ≥20% AI writing; about 4% at the sentence level; ELL vs native FPR 0.014 vs 0.013 on documents of at least 300 words. The Turnitin pages returned HTTP 403, so these come from secondary summaries in search results: **UNVERIFIED** against the primary page. "AI bypasser detection" launched 27 Aug 2025 (https://www.plagiarismtoday.com/2025/08/27/turnitin-launches-anti-ai-humanizer-feature/).
* **IND:**
  * Perkins et al. 2024 (7 detectors): accuracy 39.5% falling to 17.4% on manipulated content (https://arxiv.org/abs/2403.19148). Turnitin specific numbers not checked.
  * Pangram 4's table on the Perkins data: Turnitin 50.0% / 7.9% (SR by a competitor).
  * Turnitin is not on RAID and not on the AI Humanizer Benchmark panel.

### 3.5 Other commercial tools on RAID
QuillBot 99.62, Grammarly 99.47 and Winston 99.98 TPR@5%. These same tools pass humanized text at high rates (§4.4).

---

## 4. Robustness benchmarks and humanizer studies

### 4.1 Humanizer studies (most important)

**DAMAGE (Pangram, Jan 2025; arXiv 2501.03437)** (https://arxiv.org/html/2501.03437v1)
* 19 tools. Paraphrasers: DIPPER, Grammarly, Quillbot. Humanizers: Bypass GPT, Ghost AI, HIX Bypass, Humbot AI, HumanizeAI.io, HumanizeAI.pro, Humanizer.com, Phrasly.ai, Semihuman AI, StealthGPT, StealthWriter.AI, Surfer SEO, Undetectable AI, Twixify, WriteHuman.ai, GPTInf, AIHumanizer.com.
* Quality tiers: Undetectable AI, HIX Bypass, WriteHuman and others fall in the worst tier (L3).
* Numbers are in §3.1. Training only on L1 (best quality) humanizer data generalized to unseen humanizers. Adding all humanizers raised FPR to 6.00%. A GPT 4o humanizer fine tuned against the detector kept DAMAGE's TPR@5% at 100%. **Conflict of interest: the authors are a detector vendor.**

**Karr, Khvatskii, Hua & Chawla, "Why AI Detection Fails for Academic Integrity" (Notre Dame; arXiv 2608.11256, AILS '26)** (https://arxiv.org/html/2608.11256v2)
* 642 OpenAlex abstracts in 4 fields and 2 periods. Rewrites by Gemini 3 Flash; humanizer Undetectable AI v11 (Balanced, Doctorate and Article modes).
* After humanization, Pangram 3.2 and GPTZero flag **under 4%** of AI rewrites (1.5 to 4.0%).
* Flag rates on 2023 to 25 human originals differ by field: chemistry 2.1% / 1.1%, theology 26.6% / 15.2% (Pangram / GPTZero).
* Detector scores track long token and academic word density.

**Wang, Zhu & Chen, "Humanized but Still True?" (arXiv 2611.00359, Oct 2026)** (https://arxiv.org/html/2611.00359)
* **Fact preservation:** all 11 commercial humanizers changed at least one checkable fact (number, name or quote) in **35 to 65%** of documents. Examples: aihumanize and writehuman 13/20, undetectable ai 11/20, hix bypass 7/20. No tool kept more than 4 of 15 quoted spans verbatim.
* **No reliable trade off between fidelity and evasion:** Spearman ρ = −0.46 (95% CI −0.65 to 0.08).
* **Detectors on 92 human federal passages vs AI drafts and 368 rewrites by an open 12B humanizer**, AUROC and TPR@5% (draft → rewrite):

  | Detector | AUROC draft | AUROC rewrite | TPR@5% draft | TPR@5% rewrite |
  |---|---|---|---|---|
  | Jev (commercial, TypeSafe AI) | 0.943 | 0.864 | 0.728 | 0.565 |
  | Fast DetectGPT | 0.567 | 0.688 | 0.076 | 0.201 |
  | Binoculars | 0.543 | 0.654 | 0.054 | 0.082 |
  | RoBERTa | 0.435 | 0.661 | 0.043 | 0.196 |
  | RADAR | 0.717 | 0.650 | 0.043 | 0.052 |

  On the 2026 subset, Binoculars (0.37) and Fast DetectGPT (0.39) were **below chance**.
* Caveats: oracle thresholds; no conflict of interest statement despite the headline result being for a commercial detector.

**Perkins et al. 2024 (IJETHE 21:53; arXiv 2403.19148).** 7 detectors, 805 samples, 6 manipulation techniques. Accuracy 39.5% falls to 17.4% under manipulation. Added spelling errors and "burstiness" were the most effective evasions. Higher FPR for nonnative speakers (https://arxiv.org/abs/2403.19148).

**Jabarian & Imas (NBER 34223).** See §3.1; per detector numbers UNVERIFIED.

### 4.2 Humanize 16K (from Triospect, TACL 2026)
Six humanizing attacks, 4 domains, 6 source models, built with commercial humanizers (search summary of arXiv 2606.31074). Triospect claims are in §2.8. Details are UNVERIFIED because the full text timed out.

### 4.3 Classic robustness benchmarks
* **M4GT Bench** (ACL 2024; arXiv 2402.11175): three tasks (binary detection, multi way generator attribution, and the human/machine boundary in mixed text). Main finding: good detection "usually requires access to training data from the same domain and generators" (https://arxiv.org/abs/2402.11175).
* **MAGE** (ACL 2024; arXiv 2305.13242): the best detector identifies 86.54% of OOD text from an unseen LLM (https://arxiv.org/abs/2305.13242). Binoculars TPR@1% on MAGE is 56.04, or 75.80 with MCP (https://arxiv.org/html/2505.05084v2).
* **DetectRL** (NeurIPS 2024 D&B; arXiv 2410.23746): arXiv abstract human text; GPT 3.5, PaLM 2, Claude instant and Llama 2 to 70b; prompt, word substitution and spelling attacks. Zero shot detectors "often struggle" (https://arxiv.org/abs/2410.23746). AUROC on DetectRL Multi Domain: Fast DetectGPT 74.98, Binoculars 77.45, DNA DetectLLM 88.23 (https://arxiv.org/html/2509.15550v2).

### 4.4 AI Humanizer Benchmark (monthly; my computation from its published data)

**Operator and conflict of interest.** Run by "the team that makes UndetectedGPT", a humanizer that is ranked on the benchmark; the site discloses this (https://aihumanizerbenchmark.com/).

**Design.** 33 AI source texts per cycle, written by 6 models from OpenAI, Anthropic and Google from Oct 2026. 7 detectors; "Pangram replaced Winston AI from November 2026". Each detector score is "the detector's human probability" (https://huggingface.co/datasets/AIHumanizerBenchmark/ai-humanizer-benchmark). There are **no human control texts**, so FPR is not measured.

**Per detector results.** I computed the mean human probability (pass rate) per detector from `detector-scores.json`: https://huggingface.co/datasets/AIHumanizerBenchmark/ai-humanizer-benchmark/resolve/main/data/cycles/2026-11/detector-scores.json and the matching `2026-10` file. Lower means harder to fool.

| Detector | Mean human prob, Oct 2026 (n=363) | Mean human prob, Nov 2026 (n=330) |
|---|---|---|
| Pangram | not on panel | **0.054** |
| Originality.ai | 0.722 | **0.110** |
| GPTZero | 0.436 | 0.430 |
| Copyleaks | 0.598 | 0.561 |
| Winston AI | 0.649 | not on panel |
| ZeroGPT | 0.762 | 0.643 |
| QuillBot | 0.720 | 0.695 |
| Grammarly | 0.777 | 0.764 |

* **Strongest humanizers in Nov 2026** (human prob against GPTZero / Pangram / Originality): CleverHumanizer 0.83 / 0.09 / 0.31 and Rephrasy 0.83 / 0.17 / 0.28.
* **Weakest:** Undetectable AI 0.03 / 0.00 / 0.04 and ReHumanize 0.01 / 0.00 / 0.04.
* The site lists aggregate bypass rates: CleverHumanizer 89.6, Undetectable AI 3.5 (https://aihumanizerbenchmark.com/leaderboard).
* **Contradiction:** Karr et al. found Undetectable AI v11 defeated Pangram and GPTZero. Possible explanations are different versions or modes, a different domain (academic abstracts), or different thresholds: UNVERIFIED.
* **Key finding:** RAID rank does not predict robustness to humanizers. QuillBot (#15) and Grammarly (#18) are near the top of RAID but have the highest humanizer pass rates here.
* Sample sizes are small (33 sources × 10 to 11 tools), and a humanizer vendor runs the benchmark.

---

## 5. Recommendation candidates (open, calibrated, explainable)

**Candidate A: a zero shot two model statistical core with MCP conformal calibration.**
* **Score:** Binoculars family or DNA DetectLLM, optionally with an AdaDetectGPT witness function.
* **Calibration:** Multiscaled Conformal Prediction, which gives a distribution free FPR bound per length bin. On RealDet it cut Binoculars' realized FPR from 7.68% to 0.72% while raising TPR@1% from 78.98 to 86.28 (https://arxiv.org/html/2505.05084v2).
* **Accuracy:** DNA DetectLLM adds +4.8 AUROC on average over Binoculars on public benchmarks (90.86 vs 86.08), including DetectRL Multi Domain 88.23 vs 77.45, at about 0.8 s per sample on an A100 (https://arxiv.org/html/2509.15550v2).
* **Explainability:** natural per token surprisal and cross perplexity, or the repair steps, can be shown to users.
* **Weakness, with evidence:** humanizers break this family. Binoculars TPR@5% fell from 94.15% to 28.23% on humanized text (https://arxiv.org/html/2501.03437v1). Binoculars and Fast DetectGPT were below chance on 2026 AI styled federal text (https://arxiv.org/html/2611.00359). It must be paired with Candidate B.

**Candidate B: an open weight supervised encoder trained with adversarial and humanizer data, with Unicode normalization at inference.**
* **Models:** Ettin or ModernBERT or DeBERTa encoders such as GPTTrace (CC BY SA), MELD (MIT) or DeBERTa ConPara (paper at AACL 2026).
* **Evidence:** best open RAID results. GPTTrace Ettin 1B: 99.93 TPR@5% and 99.54 TPR@1% overall, 99.72 on paraphrase (https://raid-bench.xyz/data/submissions/gpttrace-ettin1b.json), above every commercial tool except Winston. DeBERTa ConPara has a peer reviewed recipe: normalization raises homoglyph and zero width TPR to 96.98% (https://arxiv.org/abs/2610.00883).
* **Weaknesses:**
  * RAID scores are in distribution (trained on RAID train, oracle thresholds per domain).
  * GPTTrace self reports only 0.791 TPR@5% on commercial humanizers (https://huggingface.co/nakas/gpttrace-v8s-1b).
  * None of these report nonnative FPR.
  * It needs its own conformal calibration (Candidate A's wrapper applies) and post hoc attribution (e.g. a per token head as in Pangram 4) to be explainable.

**Candidate C, for the humanizer gap: a DAMAGE style humanizer aware training regime.**
* **Recipe:** train on outputs from many commercial humanizers, prefer the higher quality ones, hold out tools to test generalization. Evaluate monthly on the AI Humanizer Benchmark data, adding human controls, and on Humanize 16K.
* **Evidence:** DAMAGE kept 98.26% TPR@5% on humanized text vs 28.23% for Binoculars and generalized to unseen humanizers (https://arxiv.org/html/2501.03437v1). In the Nov 2026 benchmark, Pangram, trained this way, let only 0.054 mean human probability through, vs 0.43 to 0.76 for others. Triospect (TACL) is an open, statistical alternative claiming +22.3% AUROC on humanized text (https://arxiv.org/abs/2606.31074; details UNVERIFIED).
* **Caveat:** DAMAGE and Pangram are vendor authored. Independent work (Karr et al.) showed Undetectable AI v11 driving Pangram 3.2 to 1.5 to 3.4% TPR (https://arxiv.org/html/2608.11256v2), so humanizer robustness is version dependent and must be remeasured continually.

**Practical synthesis for Detechum:** combine an open encoder (B), trained with humanizer data (C), with a zero shot statistical feature (A). Calibrate the combined score with MCP thresholds per length bin on an in house human corpus that **must include nonnative English** (ELLIPSE, ICNALE, TOEFL, PELIC, as used in https://arxiv.org/html/2607.27183v1) and subjects like theology and political science, where flag rates were 24 to 27% (https://arxiv.org/html/2608.11256v2). Report TPR@1% and realized FPR, not RAID style oracle accuracy.

---

## Could not access, or UNVERIFIED

* raid bench.xyz/leaderboard as rendered HTML (JS app). The ranking above is recomputed from the site's own data files.
* Turnitin primary pages: the blog and the guides.turnitin.com FAQ returned HTTP 403. All Turnitin figures are from secondary summaries.
* Jabarian & Imas PDF (NBER w34223): could not render (no PDF tooling). Per detector FPR and FNR are UNVERIFIED. The Chicago Booth Review summary timed out.
* Full text of Triospect (2606.31074), Glimpse (2412.11506 HTML) and NormDetect (2610.41459): fetches timed out. Abstracts only, or nothing for NormDetect.
* Full text of ImBD, DeTeCtive and Luminol AIDetect: not read; abstract level claims only.
* Originality.ai Turbo claims and GPTZero's "95.7% at 1% FPR" blog claim: secondary sources only. The GPTZero figure is consistent with the leaderboard's 95.72 no attack TPR@1%.
* Nature and openness of RAID entries XYZ SCIENCE, FLAIRD, FCM, ParaTrace and provenance: their metadata gives no paper or code.
