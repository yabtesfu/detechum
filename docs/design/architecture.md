# Phase 3: Detechum architecture

Design goal: **every number Detechum prints must be calibrated, explained, and reproducible.**
Method choices are justified in [`../research/phase1_methods.md`](../research/phase1_methods.md);
every metric referred to here is defined in [`../evaluation/plan.md`](../evaluation/plan.md).

## 1. What the user sees

```
Document: 412 words · English · domain: student essay (detected automatically, editable)

P(AI generated) ............ 0.71   (90% interval 0.58 to 0.82)
Verdict .................... Likely AI generated  [threshold set for ≤1% false positives]
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
| Binoculars style cross perplexity ratio | second, partly independent signal + explanations | zero shot, TPR@0.01%FPR 0.935 to 0.976 in its paper and stable under DIPPER, but **drops to 28% TPR@5% on commercially humanized text**, so it cannot be the only signal |
| Fast DetectGPT conditional curvature | optional third signal | zero shot, 1 to 2 passes; check its value against Binoculars before shipping both |
| Token rank / entropy features (GLTR family) | **explanation layer** | easy to read ("top 1 prediction"); weak alone (RAID 62.6 → 47.2 under paraphrase) |
| Style features (sentence length variance, transition phrase density, type to token ratio) | explanation layer only | readable; never used alone for the verdict |

Scorers are pinned by model ID **and** Hugging Face commit hash. A scorer change is a new release, with a
new reliability diagram (see §4).

### 2.3 Aggregate

* **Document score**: a small logistic model over scorer outputs plus length features, fitted on the
  calibration split only. Kept small so it stays explainable and auditable.
* **Sentence scores**: the same scorers on a sliding window (sentence ± neighbours). Sentence level scores
  are noisier than document level ones. The UI marks them as lower confidence, and they have their
  own calibration curve.
* **Mixed authorship** (later milestone): change point detection over the per token score series, to
  report "sentences 8 to 14 look different from the rest" instead of one blended number.

## 3. (a) P(AI) with an uncertainty range

Three separate layers, each answering a different question:

1. **Calibration map**: isotonic regression from aggregate score to P(AI), fitted on a held out
   calibration split stratified by domain × length bucket × native/nonnative. Answers: "of documents
   scored like this, what fraction were AI?"
2. **Interval**: bootstrap the calibration split (B = 1000), refit the map each time, and report the 5th to 95th
   percentile of P(AI) for this score. Answers: "how sure are we of that fraction, given finite
   calibration data?" Wide intervals occur where calibration data is thin, and the report says so.
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

## 8. Open decisions

* Minimum length for a verdict (candidates: 100 or 150 words), decide from the length stratified curves in
  the evaluation plan, not in advance.
* Which open scorer models to host (memory and latency budget vs. accuracy). Decide after reproducing Phase 1
  numbers locally.
* How to name the abstain state in the UI.
