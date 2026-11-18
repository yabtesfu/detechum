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

`.venv/bin/python eval/fetch_models.py` downloads the pinned model weights (about 10.3 GB) into `data/external/models`,
which is not committed. Weights download as 32 MB ranges over parallel connections, and a stalled
connection is retried automatically. If the run is interrupted, start it again: completed ranges are kept.
Each assembled file is checked against the SHA 256 published for its pinned revision.

## Scoring a text

```bash
.venv/bin/detechum score essay.txt --calibration results/calibration_pilot_v1/calibration.json
```

The command removes invisible characters and lookalike letters, scores the text with GPTTrace v8s 1B, maps the
score to P(AI) with a 90% interval and prints a verdict with its reasons. Use `-` as the file name to read
standard input, and `--json` for the full result. Without `--calibration` it prints the raw score and no
verdict.

Current limits:

* The only calibration file is a pilot fitted on 746 texts from 2023
  ([report](results/calibration_pilot_v1/report.md)). Its probabilities are not validated for any real use.
* Texts under 150 words get no verdict.
* GPTTrace reads at most 512 tokens. For longer texts only the beginning is scored, and the output says so.
* Sentence level reasons are not implemented yet.

`.venv/bin/python eval/calibration_pilot.py` rebuilds the pilot calibration and its report from the committed
scores. It needs no model weights.
