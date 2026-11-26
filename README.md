# detechum

Open-source AI content detection and analysis platform focused on accuracy, explainability, and reducing false positives.

## Research and design docs

| Phase                            | Document                                                                                                                                       |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1: Methods from primary sources  | [docs/research/phase1_methods.md](docs/research/phase1_methods.md) (detailed, cited reports in [docs/research/phase1/](docs/research/phase1/)) |
| 2: Commercial tool surface map   | [docs/research/phase2_commercial_tools.md](docs/research/phase2_commercial_tools.md)                                                           |
| 3: Architecture                  | [docs/design/architecture.md](docs/design/architecture.md)                                                                                     |
| 4: Preregistered evaluation plan | [docs/evaluation/plan.md](docs/evaluation/plan.md)                                                                                             |

Pilot results on nonnative writer bias, with per text scores: [results/bias_v1/report.md](results/bias_v1/report.md).
Runs on the test split of the evaluation plan: [results/eval_v2/report.md](results/eval_v2/report.md) (current) and
[results/eval_v1/report.md](results/eval_v1/report.md) (first).

## Development

Requirements: Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -e ".[models]"
.venv/bin/python -m unittest discover -s tests
```

The core package requires NumPy and SciPy.
The `models` extra adds PyTorch and Transformers for the scorers in `src/detechum/scorers` and the
experiments in `eval/`.

`.venv/bin/python eval/fetch_models.py` downloads the pinned model files (about 12 GB) into `data/external/models`,
which is not committed. Weights download as 32 MB ranges over parallel connections, and a stalled
connection is retried automatically. If the run is interrupted, start it again: completed ranges are kept.
Every file is checked against the SHA 256 pinned for its revision in `src/detechum/models.py`. `--only gpttrace`
fetches the 4.1 GB that the command needs; the other models are used only by experiments in `eval/`.

## Scoring a text

```bash
.venv/bin/detechum score essay.txt --calibration results/eval_v2/calibration.json
.venv/bin/detechum score essay.txt --calibration results/eval_v2/calibration.json --kind student_essay
```

The command removes invisible characters and lookalike letters, scores the text with GPTTrace v8s 1B, maps the
score to P(AI) with a 90% interval and prints a verdict with its reasons. A label is given only when the
whole interval lies on one side of the threshold and the calibration texts of similar length rule out the
other class. Otherwise the verdict is "Can't tell reliably". It then removes each sentence in
turn, scores the rest again, and lists the sentences whose removal lowers the score most. Use `-` as the
file name to read standard input, `--json` for the full result and `--no-explain` to skip the sentence
analysis, which needs one scorer pass per sentence. Without `--calibration` it prints the raw score and no
verdict. `--kind student_essay` compares the text only with the student essays of the calibration; the
command does not check that the text is one.

Before it loads the model, the command checks every file in the model folder against the size and SHA 256
pinned in `src/detechum/models.py`: the weights, the tokenizer, the configuration and the model's
`normalize.py`. A missing, changed or extra file stops the command with the name of the file, and no score
is printed. Reading the 4.1 GB of weights took about 4 seconds on the development machine (Apple silicon).
The JSON result records the model repository, revision and weights digest. The check catches a wrong
revision, a broken download and a replaced file. It does not protect against someone who can also change
the installed code.

Current limits:

* The calibration was fitted on the calib split of eval_plan_v2: 4,653 human and 4,011 AI texts, and for
  `--kind student_essay` 4,197 human and 2,187 AI essays ([report](results/eval_v2/report.md)). P(AI)
  assumes that mix of texts.
* On the test split, no essay of an English learner (0 of 3,245) or of a native writer (0 of 242) was
  flagged. 15 of 3,910 human student essays of 150 words or more were labelled as AI, all of them polished
  essays by unknown writers from one source (IvyPanda). Of the AI student essays, 90.6% were flagged at a 1%
  false positive rate.
* Weak spots: AI essays of small Llama models (about 70% flagged), AI essays written in the voice of an
  English learner (about 77%) and Claude student essays (79%). A humanlike AI essay can get "Can't tell
  reliably": its score overlaps human essays, and a second detector tested on calib did not separate them
  without flagging more essays of English learners (plan §10).
* Tested attacks are DIPPER paraphrases and AI rewrites, which lowered detection by at most 1.7 points.
  Commercial humanizers and light human edits are not tested. The nonnative release gate of the plan could
  not be evaluated, because no native text was flagged and its ratio has no value.
* The earlier pilot calibration is kept in [results/calibration_pilot_v2/](results/calibration_pilot_v2/report.md).
  With it, no text is labelled as AI, because no length band has the 99 human texts that the 1% error target
  needs.
* The command does not detect the language or the kind of text. A text unlike the calibration texts is
  scored like any other.
* Texts under 150 words get no verdict.
* The label "Likely AI written or AI edited" covers both cases. The scorer flags most human essays that an
  AI polished and cannot separate them from text an AI wrote.
* GPTTrace reads at most 512 tokens. For longer texts only the beginning is scored, and the output says so.
* The sentence list shows what moves the score, not which sentences are AI written. In a test with one
  planted AI sentence per essay, the top ranked sentence was the planted one in 27 of 50 essays
  ([report](results/attribution_pilot_v1/report.md)).
* Reasons based on word predictability are not shown. That signal runs higher for nonnative writers
  ([report](results/explanation_pilot_v1/report.md)).

`.venv/bin/python eval/calibration_pilot.py` rebuilds the pilot calibration files and their report from the
committed scores. It needs no model weights.

To rebuild `results/eval_v1` from the corpora:

```bash
git clone https://github.com/Weixin-Liang/ChatGPT-Detector-Bias data/external/liang
.venv/bin/python eval/fetch_data.py                 # about 23 MB, every file checked against its SHA 256
.venv/bin/python eval/build_manifests.py            # compare with the committed eval/manifests
cd eval
../.venv/bin/python score_corpora.py --data ../data/external --manifests manifests \
    --models ../data/external/models --out ../results/eval_v1
../.venv/bin/python run.py && ../.venv/bin/python report.py ../results/eval_v1
```

Scoring the 12,318 texts took about three hours on the development machine and keeps it busy. It can be
stopped and started again; scores already saved are kept. `run.py` refuses to run on test when
`results/eval_v1/metrics.json` exists, so move that file away first to recompute it.

To rebuild `results/eval_v2`, after the steps above:

```bash
.venv/bin/python eval/fetch_data.py --v2            # about 156 MB more
cd eval && ./night_v2.sh                            # Qwen essays, v2 manifests and scores, a few hours
../.venv/bin/python run_v2.py && ../.venv/bin/python report_v2.py ../results/eval_v2
```

The manifests need the 300 Claude essays of calib, which were written by Claude Code subagents and are not
distributed (`eval/record_claude_essays.py` holds their tasks). Their scores are committed in
`results/eval_v2/scores.jsonl`, and `run_v2.py` reads only the manifests and the scores, so the last line
works without them.

The `eval_plan_v1` tag is the freeze reference for the metrics, thresholds and verdict rules in
[docs/evaluation/plan.md](docs/evaluation/plan.md) and `eval/config/thresholds.yaml`. The one run on its test split,
`eval_v1`, is recorded in §9 of the plan. The tag `eval_plan_v2` does the same for its run, `eval_v2`.
