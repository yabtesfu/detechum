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

`.venv/bin/python eval/fetch_models.py` downloads the pinned model weights (about 10.3 GB) into `data/external/models`,
which is not committed. Weights download as 32 MB ranges over parallel connections, and a stalled
connection is retried automatically. If the run is interrupted, start it again: completed ranges are kept.
Each assembled file is checked against the SHA 256 published for its pinned revision.
