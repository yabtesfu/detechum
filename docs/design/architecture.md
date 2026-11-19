# Phase 3: Detechum architecture

Design goal: **every number Detechum prints must be calibrated, explained, and reproducible.**
Method choices are justified in [`../research/phase1_methods.md`](../research/phase1_methods.md);
every metric referred to here is defined in [`../evaluation/plan.md`](../evaluation/plan.md).

## 1. What the user sees

```
Document: 412 words · English · domain: student essay (detected automatically, editable)

P(AI generated) ............ 0.71   (90% interval 0.58 to 0.82)
Verdict .................... Likely AI written or AI edited  [threshold set for ≤1% false positives]
Sentences flagged .......... 9 of 23  (39%)        [each sentence scored on its own]
Reliability of this result . Medium: 412 words; domain seen in calibration; English

Why (top reasons, strongest first)
 S4  "Furthermore, consistent physical activity…"  83% of words were a language model's
     top 1 prediction (human essays in our calibration set: median 46%).
 S2  Sentence lengths in ¶1 vary less than in 92% of human essays we calibrated on.
 …
These are statistical signals, not proof of authorship. Human writers, especially those
writing in a second language, can trigger them.
```

Two rules shape this screen:

1. **P(AI) and "sentences flagged" are separate numbers, never merged.** P(AI) is a calibrated
   probability for the whole document. The flagged share is a count of sentences over a
   sentence level threshold. The two can disagree (e.g. a human essay with three AI sentences),
   and the UI says so instead of averaging them.
2. **The page always shows an abstain state.** When the interval straddles the decision threshold, or the
   input is outside calibrated conditions (too short, unseen language or domain), the verdict is
   "Can't tell reliably", not a number made to look precise.

## 2. Pipeline

```
text → normalize → segment → score → aggregate → calibrate → explain → report
         │            │           │          │            │            │
         │            │           │          │            │            └ reason templates + evidence
         │            │           │          │            └ isotonic map + bootstrap interval
         │            │           │          │              + conformal abstain set
         │            │           │          └ document score; per sentence scores
         │            │           └ zero shot scorers (+ optional trained head)
         │            └ sentences, paragraphs, token offsets
         └ Unicode NFKC; strip and REPORT zero width chars, homoglyphs, odd whitespace
```

### 2.1 Normalize (and treat tampering as a finding)

Zero width characters, Cyrillic look alike letters and odd whitespace are standard tricks for
evading detectors (RAID includes homoglyph and whitespace attacks; see Phase 1). Detechum removes them
**before** scoring and **lists them in the report** ("14 zero width characters removed"). They never move
P(AI) directly; they are reported as a separate fact.

### 2.2 Scorers (pluggable, each one versioned)

Each scorer implements one interface and returns per token and per sentence values. These are all
the scoring stage computes:

| Scorer | Role | Why (evidence in [Phase 1](../research/phase1_methods.md#what-this-means-for-detechums-design)) |
|---|---|---|
| Open supervised encoder (Ettin / ModernBERT / DeBERTa family), fine tuned with adversarial **and humanizer** outputs | **primary document signal** | best open RAID results (e.g. GPTTrace Ettin 1B 99.54 TPR@1%); humanizer aware training is the only approach with evidence of surviving humanizers (DAMAGE, vendor authored). Generalization measured on held out humanizers |
| Binoculars style cross perplexity ratio | candidate second signal, **not admitted to the verdict yet** (see §2.4) | zero shot, TPR@0.01%FPR 0.935 to 0.976 in its paper and stable under DIPPER, but **drops to 28% TPR@5% on commercially humanized text**, so it cannot be the only signal. In the local pilot, an unvalidated Qwen 2.5 1.5B pair flagged 52.7% of nonnative essays at a threshold that flags 1% of native essays |
| Fast DetectGPT conditional curvature | optional third signal, subject to the same admission test (§2.4) | zero shot, 1 to 2 passes; check its value against Binoculars before shipping both |
| Token rank / entropy features (GLTR family) | **explanation layer** | easy to read ("top 1 prediction"); weak alone (RAID 62.6 → 47.2 under paraphrase) |
| Style features (sentence length variance, transition phrase density, type to token ratio) | explanation layer only | readable; never used alone for the verdict |

Scorers are pinned by model ID **and** Hugging Face commit hash. A scorer change is a new release, with a
new reliability diagram (see §4).

### 2.3 Aggregate

* **Document score**: a small logistic model over the outputs of admitted scorers (§2.4) plus length
  features, fitted on the calibration split only. Kept small so it stays explainable and auditable.
* **Sentence scores**: the same scorers on a sliding window (sentence ± neighbours). Sentence level scores
  are noisier than document level ones. The UI marks them as lower confidence, and they have their
  own calibration curve.
* **Mixed authorship** (later milestone): change point detection over the per token score series, to
  report "sentences 8 to 14 look different from the rest" instead of one blended number.

### 2.4 Admission test for scorers that feed the verdict

A scorer's output enters the document score only after the scorer passes the nonnative gate of the
evaluation plan ([M3](../evaluation/plan.md#m3-nonnative-false-positive-rate)) on its own: at the threshold
that flags 1% of native human text, the upper bound of the nonnative FPR is ≤ 2% and the nonnative to
native FPR ratio is ≤ 1.5. A scorer that fails stays out of the document score and the verdict. The
aggregate is fitted on calibration data, so it cannot be relied on to cancel a large bias in strata where
nonnative calibration data is thin.

Pilot evidence ([`results/bias_v1/report.md`](../../results/bias_v1/report.md), described in
[evaluation plan §8](../evaluation/plan.md#8-pilot-runs-recorded-before-tagging)), with 95% Clopper Pearson
intervals:

| Scorer | Threshold | Nonnative essays flagged (TOEFL) | Native essays cut to the same lengths | AUROC |
|---|---|---|---|---|
| GPTTrace v8s 1B | flags 1% of native essays (`7.945`) | 2/91 = 2.2% (0.3 to 7.7) | 1/91 = 1.1% (0.0 to 6.0) | 0.997 |
| GPTTrace v8s 1B | model card value (`9.3`) | 0/91 = 0.0% (0.0 to 4.0) | 0/91 = 0.0% (0.0 to 4.0) | 0.997 |
| Binoculars style ratio, Qwen 2.5 1.5B base and instruct | flags 1% of native essays (`-0.958`) | 48/91 = 52.7% (42.0 to 63.3) | 1/91 = 1.1% (0.0 to 6.0) | 0.831 |

What follows from the pilot:

* **The supervised encoder stays the primary signal.** GPTTrace has not passed the gate yet. It has not
  failed it either: 91 nonnative essays with none flagged give an upper bound of 4.0%, and the gate's 2%
  bound needs at least 183 nonnative texts with none flagged.
* **The Binoculars style ratio with this model pair is excluded from the verdict.** The pair is not the one
  from the Binoculars paper (Falcon 7B and Falcon 7B Instruct), and that paper reports 99.67% accuracy on
  ESL essays. The pilot result therefore applies to the Qwen pair only. A validated pair can be admitted
  if it passes the same test.

## 3. (a) P(AI) with an uncertainty range

Three separate layers, each answering a different question:

1. **Calibration map**: isotonic regression from aggregate score to P(AI), fitted on a held out
   calibration split stratified by domain × length bucket × native/nonnative. Answers: "of documents
   scored like this, what fraction were AI?"
2. **Interval**: bootstrap the calibration split (B = 1000), refit the map each time, and report the 5th to 95th
   percentile of P(AI) for this score. Answers: "how sure are we of that fraction, given finite
   calibration data?" Wide intervals occur where calibration data is thin, and the report says so.
   The range is widened to the exact binomial interval of the pooled block the score falls in. Without
   that, a block holding only AI texts would report a range of zero width, however few texts it holds.
3. **Abstain / verdict**: split conformal prediction (Mondrian, per stratum; per length bin as in
   Multiscaled Conformal Prediction, which cut Binoculars' realized FPR from 7.68% to 0.72%, see Phase 1) at the chosen error rate.
   If the prediction set is {AI, human}, the verdict is "Can't tell reliably". Answers: "can we commit to a
   label at the promised error rate?"

The **decision threshold** is set so that FPR ≤ 1% on human text **in every stratum, including nonnative
writers**, not just on average. If no threshold reaches that for a stratum, Detechum abstains for that
stratum and documents it. It does not quietly accept a higher false positive rate.

Out of distribution guard: inputs under the minimum length, or in a language or domain without
calibration data, receive no verdict, only the raw signals.

## 4. (c) Calibration you can inspect

* Each release publishes reliability diagrams (equal mass bins), ECE and Brier score
  **per stratum**, built in CI from the frozen test split. See the evaluation plan.
* The report links to the diagram for the stratum it used, so a user can check "when Detechum says 0.7,
  is it right ~70% of the time for documents like mine?"
* Calibration drifts as new LLMs come out. Each release lists its calibration data generation date and the
  generator models it covered. Unseen generators are an explicit limitation, not a hidden one.

## 5. (b) Sentence reasons the writer can act on

Each reason is a **template plus measured evidence plus a comparison to calibrated human text**, never free
text from an LLM (that would be unverifiable).

| Signal | Template | Writer action |
|---|---|---|
| Top 1 token rate | "{p}% of words were a language model's single most likely choice (human median: {m}%)." | Use your own specific wording, examples or details. |
| Low perplexity span | "This phrase is highly predictable: {span}." | Say it the way you would explain it to a friend. |
| Sentence length uniformity | "Sentence lengths in this paragraph vary less than {q}% of human texts." | Vary the rhythm where it suits the content. |
| Stock transitions | "Opens with a common template transition ({word})." | Connect ideas with content, not connectors. |
| Tampering found | "{n} invisible characters were removed before scoring." | n/a |

Rules:

* A reason is shown **only if it actually drives that sentence's score**: attribution over the
  aggregate model's inputs (exact for a linear aggregator), with a minimum contribution to qualify.
* Every reason carries the caveat that it is a signal, not proof. Nonnative writers in particular may
  show low perplexity for legitimate reasons. The report links to the measured nonnative FPR.
* Reasons describe the *text*, never the person's intent.

Status of the implementation (`src/detechum/explain.py`):

* **Sentence effects are implemented by removal.** Each sentence is removed in turn and the rest is scored
  again with the primary scorer. The drop in the score is that sentence's contribution. This is exact about
  the scorer and needs no second signal. Contributions do not add up to the score, and for a text longer
  than the scorer's input limit they are less reliable.
* **A listed sentence is not proof that it is AI written.** With one GPT 3 sentence planted in each of 50
  native human essays, the planted sentence ranked first in 27 (chance: 6.9%), and a human first sentence
  ranked first in 9 of 48 (chance: 6.9%). Only 11 of the 50 planted sentences moved the score by the display
  minimum of 1.0. The report states this next to the list (evaluation plan §8).
* **The templates of the table above are not implemented.** The top 1 token rate did not pass the nonnative
  test (§8 below). The others have not been tested.

## 6. (d) Revision mode

Revision mode suggests rewrites, sentence by sentence. It is honest about what it changed and what it
achieved.

```
For each flagged sentence:
  propose ≤3 rewrites (LLM, constrained prompt: keep meaning, keep facts, keep citations)
  → check each rewrite:
       meaning:  bidirectional NLI entailment (orig ⇒ new AND new ⇒ orig)
                 + BERTScore F1 vs original
       facts:    numbers, named entities and citations must match exactly
  → reject any rewrite that fails a check (logged, not hidden)
  → the writer accepts or rejects each one (never applied automatically)
Final report:
  * diff of every change, with the reason that triggered it
  * meaning preserved: entailment pass rate, mean BERTScore
  * BEFORE/AFTER scores from HELD OUT detectors (not used to tune the rewriter):
      e.g. tuned against Binoculars → reported on Fast DetectGPT, a RoBERTa head, and
      any external API the user configures
  * the date and versions of those detectors
```

Hard rules (enforced in code and tests):

* **Never print "undetectable", "guaranteed human", or "bypasses X".** The output wording is fixed: "Scored
  {a}→{b} on {detector}@{version} on {date}. Detectors change; this is not a guarantee."
* **No degradation tricks**: no deliberate typos, homoglyphs, zero width characters, random synonym swaps
  or grammar errors. Revision output goes back through the normalizer (§2.1), and any such trick fails the
  release test suite.
* **No tuning against the reporting detectors.** The detectors used to pick rewrites and the detectors
  used to report results are disjoint sets, recorded in the report.
* The writer makes the final choice on every edit. The tool's job is to explain, not to launder.

## 7. Reproducibility

* Every report includes: Detechum version, scorer model IDs + commit hashes, calibration set manifest
  hash, threshold, stratum, and a JSON export of all signals, so the number can be recomputed offline.
* The `detechum score` command, with its explain and JSON options, produces the same output as the UI; the UI is a view over that JSON.

Status of the implementation:

* **Model files are verified before every score.** `detechum.models` pins the size and SHA 256 of every file
  of each model revision, including the `normalize.py` that the GPTTrace scorer executes. `detechum score`
  stops without a score if a file is missing, changed or not part of the pinned revision. The result records
  the model repository, the revision and the weights digest. The digests of the weights are the ones the hub
  publishes. The hub publishes no SHA 256 for the smaller files, so theirs were computed from copies whose
  git blob ids matched the hub's listing.
* **Not in the result yet:** the Detechum version and a hash of the calibration set manifest. A calibration
  file is tied to a scorer by name, not to a model revision.

## 8. Open decisions

* Which open scorer models to host (memory and latency budget vs. accuracy). Decide after reproducing Phase 1
  numbers locally.
* How to name the abstain state in the UI.
* What reference the token rank and entropy templates compare against. In the pilot, 83 of 91 TOEFL essays
  have a top 1 token rate above the median of native essays of the same length (evaluation plan §8), so a
  single "human median" misleads nonnative writers. These templates stay out of the report until a
  reference by writer group and length passes the nonnative test.

Decided by the project owner on 19 Nov 2026:

* **The minimum length for a verdict is 150 words.** This was chosen directly and not read from the length
  stratified results of the evaluation plan. Known cost: none of the 91 TOEFL essays of the pilot data is
  long enough for a verdict (evaluation plan §8).
* **Human writing that an AI edited shares a label with AI writing.** The label reads "Likely AI written or
  AI edited", and the report says that a person may have written the text and an AI edited it, and that
  the tool cannot tell the two cases apart. The reason is the pilot: GPTTrace at its model card threshold
  flags 75/91 (82.4%) of TOEFL essays polished by GPT 4 and 40/88 (45.5%) of native essays simplified by GPT,
  so a label that says "AI generated" would be wrong for many flagged texts. A separate "AI edited" label
  needs a signal that separates the two cases, and none has been tested.
