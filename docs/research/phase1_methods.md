# Phase 1: Detection methods and what the primary sources show

Compiled 14 Nov 2026. This is the summary. Every number here is taken from the three detailed reports, which
cite a table, figure or section of the original paper for each value:

* [`phase1/01_zero_shot_detectors.md`](phase1/01_zero_shot_detectors.md), GLTR, DetectGPT, Fast DetectGPT, Binoculars, and their RAID results
* [`phase1/02_trained_detectors_attacks_watermarks_bias.md`](phase1/02_trained_detectors_attacks_watermarks_bias.md), Ghostbuster, RoBERTa detectors, DIPPER, watermarking, the nonnative bias literature
* [`phase1/03_newer_methods_and_humanizer_studies.md`](phase1/03_newer_methods_and_humanizer_studies.md), RAID leaderboard (accessed 14 Nov 2026), 2024 to 2026 methods, commercial self reports, humanizer studies

**How this was gathered.** Three research agents read the papers (mostly arXiv HTML versions) and copied the
numbers. We then spot checked the claims everything else depends on against the primary pages:
[Karr et al. 2026](https://arxiv.org/abs/2608.11256), [Wang et al. 2026](https://arxiv.org/abs/2611.00359)
and [Liang et al. 2023](https://arxiv.org/abs/2304.02819). Items marked **UNVERIFIED** in the detailed reports
stay unverified here. Camera ready PDFs were not cross checked, so table numbers may differ from the
published versions.

## Read this first: three metrics that are not the same thing

| Metric | Who uses it | What it hides |
|---|---|---|
| AUROC | DetectGPT, GLTR, most papers | says nothing about the low FPR region that matters for accusations |
| TPR at a fixed FPR (0.01%, 1%, 5%) | Binoculars (0.01%), Fast DetectGPT (1%), DIPPER (1%) | the threshold is often set on the test set |
| RAID "accuracy" = TPR @ **5%** FPR | RAID paper and leaderboard | **thresholds are set per domain on hidden human test text, an oracle**; so RAID does not test calibration ([detail](phase1/03_newer_methods_and_humanizer_studies.md#12-what-the-metric-is-checked-precisely)) |

The brief asked for "TPR @ 1% FPR on RAID". The RAID paper's tables report only 5%. The leaderboard JSON
files also carry TPR @ 1%, and we quote those where available.

## Method by method

| Method | Signal | Cost per text | Best low FPR result (paper) | RAID (TPR@5%, no attack → DIPPER paraphrase) | Paraphrase robustness | Nonnative evidence |
|---|---|---|---|---|---|---|
| **GLTR** (2019) | rank of each token under GPT 2 (top 10/100/1000 buckets) | 1 forward pass, GPT 2 | AUC 0.87 ± 0.07 (Table 1); no TPR@FPR | 62.6 → 47.2 | collapses under paraphrase (RAID) | not reported |
| **DetectGPT** (2023) | log prob curvature: original vs ~100 T5 perturbed copies | ~100 perturbations + scoring passes | AUROC 0.95 (GPT NeoX/XSum); TPR@0.01% FPR **0.010 to 0.045** (per Binoculars Fig. 1) | not evaluated in RAID | DIPPER: 70.3 → **4.6** TPR@1%FPR (GPT 2 1.5B) | not reported |
| **Fast DetectGPT** (2024) | *conditional* probability curvature, analytic, no perturbations | 1 to 2 forward passes; **340×** faster than DetectGPT (79,113 s → 233 s) | 87% recall @1% FPR on ChatGPT (§3.4; Introduction says 80%, inconsistent) | 73.6 → 71.8 | T5 paraphrase AUROC ≈ 0.87 (vs ≈ 0.53 for DetectGPT) | ethics statement only |
| **Binoculars** (2024) | log PPL(Falcon 7B Instruct) ÷ cross PPL(Falcon 7B vs Falcon 7B Instruct) | 2 forward passes of a 7B model | TPR @**0.01%** FPR: News 0.949, Creative 0.935, Essay 0.976 (Fig. 1 / Table 4) | 79.6 → 80.3 | stable under DIPPER in RAID; **falls to 28.23% TPR@5% on commercially humanized text** ([DAMAGE](https://arxiv.org/html/2501.03437v1), vendor authored) | EssayForum ESL essays: 99.67% accuracy, original and grammar corrected (§5.2), so ≈0.33% FPR (inferred); sample size not stated |
| **Ghostbuster** (2024) | features from unigram/trigram/ada/davinci token probabilities → linear classifier | 2 GPT 3 API passes + local n grams; ~1k+1k docs/domain training | F1 99.0 in domain, 97.0 out of domain; **no TPR@FPR reported** | n/a | Undetectable.ai rewrite: recall 99% → **62%** | TOEFL11 99.9%, Lang8 95.5%, **Liang TOEFL 91: 74.7%** (worse than RoBERTa baseline 96.7%) |
| **RoBERTa, GPT 2 detector** (Solaiman 2019) | fine tuned encoder, 125M / 356M | 1 pass | ~95% acc. on GPT 2 1.5B text | 56.7 to 59.1 → DIPPER **raised** large to 72.9 | odd: improves under DIPPER in RAID | **58.24% FPR on TOEFL 91** (reconstructed from Liang's data); 93.1% FPR on nonnative manuscripts ([Park et al. 2026](https://arxiv.org/abs/2608.26710)) |
| **RoBERTa, HC3** (2023) | fine tuned roberta base on HC3 | 1 pass | F1 99.82 in dist; 81.89 on single sentences | 44.8 → 49.2; 15.8% FPR at τ=0.5 | n/a | not reported |
| **DIPPER** (2023, attack) | 11B T5 XXL paraphraser with lexical/order diversity controls | 1 generation | at 60L/60O, TPR@1%FPR: watermark 100.0 → 57.2; GPTZero 13.9 → 1.2; OpenAI classifier 21.6 → 14.8 | is RAID's paraphrase attack | n/a | n/a |
| **Retrieval defense** (same paper) | BM25 search over provider's output log | 1 search | 96.2 to 97.8% detection @1% FPR after strongest DIPPER | n/a | designed for it | n/a |
| **KGW watermark** (2023) | green list token bias, z test | 0 model calls | TPR 0.984 at z=4, 0 observed FP (δ=2, γ=0.5, ~200 tokens) | n/a | after paraphrase: AUC > 0.9 by 600 tokens; human paraphrase needs ~800 tokens for 0.00001 FPR | FPR does not depend on style, by construction |
| **SynthID Text** (Nature 2024) | tournament sampling watermark | 0 LLM calls; +0.57% generation latency | TPR@1%FPR plotted only (UNVERIFIED numerically) | n/a | "quite strong" degradation under paraphrase (plotted) | n/a |

**Watermarks do not apply to Detechum's main case.** They only detect text from providers that embed them.
SynthID's own Limitations section says so, and open weight models are out of reach. Detechum can add a
watermark check for participating providers, but cannot rely on it.

## Nonnative writers: what is actually established

1. **The original finding.** [Liang et al. 2023](https://arxiv.org/abs/2304.02819): 7 detectors, 91 TOEFL
   essays vs 88 US 8th grade essays. Average FPR **61.22%** vs **5.19%** (paper body; the abstract gives no
   numbers). Per detector values run from 75.82% (Originality) to 48.35% (ZeroGPT); these were reconstructed
   from the authors' released scores and reproduce both averages exactly.
2. **Length is a big confounder.** On 1,000 full length TOEFL11 essays, every detector Ghostbuster tested scored ≥ 98.1% accuracy.
3. **The bias has not gone away.** The best commercial detector tested by [Al Ali et al. 2026](https://arxiv.org/abs/2602.05769)
   still had **23.1% FPR on TOEFL 91 vs 0.0%** on the native set. In Czech the effect reverses (nonnative
   text has *higher* entropy), so the mechanism depends on the language.
4. **Real world scale.** [Park et al. 2026](https://arxiv.org/abs/2608.26710): 135,389 nonnative manuscripts,
   FPR from 0% to 100% across 13 detectors (no native control group).
5. **Disputed.** A 2024 GRE study (Jiang et al.) reportedly found no bias with in domain detectors. The paper
   is paywalled; known only via a coauthor's description; **UNVERIFIED**.
6. **No newer open method reports nonnative FPR at all** (DNA DetectLLM, AdaDetectGPT, Lastde++, Glimpse, ImBD, GPTTrace, MELD, DeBERTa ConPara).

Implication: Detechum has to **measure** nonnative FPR on its own calibration data and gate releases on
it. No published method lets us assume it is low.

## Newer methods that report beating the baselines

All figures are **self reported** unless marked otherwise. Details and links are in report 03.

| Method | Claim | Independent check |
|---|---|---|
| GPTTrace Ettin 1B (open weights, 2026) | RAID TPR@5% 99.93, @1% 99.54, paraphrase 99.72 | **On the leaderboard** (primary), but trained on RAID train, so in distribution; self reports only 0.791 TPR@5% on commercial humanizers |
| MELD (open, MIT, 2026) | RAID 99.78 | leaderboard; training data not stated |
| DeBERTa ConPara (AACL 2026) | RAID 99.01; Unicode normalization brings homoglyph/zero width TPR to 96.98% | leaderboard + peer reviewed paper |
| DNA DetectLLM (NeurIPS 2025) | avg AUROC 90.86 vs Binoculars 86.08; ~0.8 s/sample on A100 | none found |
| Lastde++ (ICLR 2025) | black box AUROC 91.47 vs Fast DetectGPT 85.68 | none found |
| MCP conformal calibration (ACL 2025) | wrapping Binoculars: realized FPR 7.68% → **0.72%**; TPR@1% 78.98 → 86.28 | none found; it is a calibration method, not a detector, and directly relevant to Detechum |
| DAMAGE / Pangram (vendor) | humanizer aware training keeps 98.26% TPR@5% on humanized text | vendor authored; contradicted by Karr et al. below |

Commercial detectors on the RAID leaderboard (TPR@5%, attacks included): Winston AI 99.98 (#1),
QuillBot 99.62 (#15), Grammarly 99.47 (#18), GPTZero 97.24 (#24). **Pangram and Originality have not submitted.**

## Humanizers vs detectors: the independent evidence

* **[Karr et al. 2026](https://arxiv.org/abs/2608.11256)** (abstract, verified):
  * after Undetectable AI humanization, "fewer than 4% of AI labeled rewrites remain flagged";
  * unedited 2023 to 2025 human originals are flagged at **9 to 15%**;
  * light, guideline compliant AI editing is flagged at **38 to 80%**;
  * "Honest AI editing results in a higher sanction risk than humanizer assisted evasion."
  * Per detector values (Pangram 3.2: 1.5 to 3.4%; GPTZero 3.9 to 4.0%; theology 26.6%) come from the body as read by the research agent; not spot checked.
* **[Wang et al. 2026](https://arxiv.org/abs/2611.00359)** (abstract, verified): all **11** commercial humanizers changed or dropped a checkable
  number, date, name or quote in **35 to 65%** of documents that contained one. Report 03 also says Binoculars
  and Fast DetectGPT scored below chance on 2026 era AI styled text (body; not spot checked).
* **RAID rank does not predict humanizer robustness.** On the AI Humanizer Benchmark data (run by a humanizer
  vendor; no human controls, so no FPR), the mean human probability on humanized text was Pangram 0.054,
  Originality 0.110, GPTZero 0.430, QuillBot 0.695, Grammarly 0.764 (lower = harder to fool), even though
  QuillBot and Grammarly sit near the top of RAID.

## What this means for Detechum's design

1. **Zero shot scores alone are not enough.** Binoculars style scores are calibratable and explainable, but
   commercial humanizers break them. Use them as a *second, interpretable* signal.
2. **The primary scorer should be an open supervised encoder** (Ettin, ModernBERT or DeBERTa family) trained with
   adversarial **and humanizer** outputs, evaluated on humanizer tools held out of training.
3. **Normalize Unicode before scoring.** It is cheap, and it beats homoglyph and zero width attacks (DeBERTa ConPara).
4. **Calibrate with conformal methods per length bin and per writer group.** MCP shows that raw thresholds give realized FPRs far above their nominal values.
5. **Do not take RAID scores as calibration evidence.** RAID uses oracle thresholds; Detechum must report realized FPR at its own threshold.
6. **Fact preservation matters in revision mode.** The independent evidence says every commercial humanizer tested
   changes facts in a large share of documents. Checking numbers, names, dates and quotes is the cheapest way for Detechum to do better than them.
