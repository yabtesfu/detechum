# detechum
Open-source AI content detection and analysis platform focused on accuracy, explainability, and reducing false positives.

## Research and design docs

| Phase | Document |
|---|---|
| 1: Methods from primary sources | [docs/research/phase1_methods.md](docs/research/phase1_methods.md) (detailed, cited reports in [docs/research/phase1/](docs/research/phase1/)) |
| 2: Commercial tool surface map | [docs/research/phase2_commercial_tools.md](docs/research/phase2_commercial_tools.md) |
| 3: Architecture | [docs/design/architecture.md](docs/design/architecture.md) |
| 4: Preregistered evaluation plan | [docs/evaluation/plan.md](docs/evaluation/plan.md) |

## Development

Requirements: Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -e ".[models]"
.venv/bin/python -m unittest discover -s tests
```

The `models` extra installs PyTorch and Transformers, which the scorers in `src/detechum/scorers` and the
experiments in `eval/` need. The core package (`detechum.verdict`, `detechum.facts`) has no dependencies.

`eval/fetch_models.sh` downloads the pinned model weights (about 10.3 GB) into `data/external/models`,
which is not committed. If the connection drops or stalls, the script exits with an error; run it again.
Completed files are skipped and a partial file resumes where it stopped.
