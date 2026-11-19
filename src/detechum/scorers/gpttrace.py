"""GPTTrace Ettin 1B (v8s) supervised detector.

Model card: https://huggingface.co/nakas/gpttrace-v8s-1b (CC BY SA 4.0).
The score is the logit margin `logit[machine] - logit[human]`; the card states that a margin of
9.3 flags about 1% of the vendor's pooled human texts. That claim is the vendor's, not ours.
"""

import types
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MAX_TOKENS = 512  # the card's usage example truncates here


def _load_normalizer(snapshot_dir: Path):
    # normalize.py ships with the model and must match the preprocessing used in training, so it is
    # loaded from the pinned snapshot rather than copied into this repository. It is compiled from
    # source on every load: the import system would run a cached .pyc beside the file in place of the
    # source that detechum.models verifies.
    path = snapshot_dir / "normalize.py"
    module = types.ModuleType("gpttrace_normalize")
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module.normalize_text


class GPTTraceScorer:
    def __init__(self, snapshot_dir: str, device: str, typography: bool):
        snapshot = Path(snapshot_dir)
        self.name = f"gpttrace_v8s_1b_typography_{'on' if typography else 'off'}"
        self.typography = typography
        self._normalize = _load_normalizer(snapshot)
        self.tokenizer = AutoTokenizer.from_pretrained(snapshot / "model")
        self.model = AutoModelForSequenceClassification.from_pretrained(snapshot / "model").to(device).eval()
        self.device = device

    def is_truncated(self, text: str) -> bool:
        """True when `text` exceeds the input limit, so `score` sees only its beginning."""
        ids = self.tokenizer(self._normalize(text, typography=self.typography), truncation=False)["input_ids"]
        return len(ids) > MAX_TOKENS

    @torch.inference_mode()
    def score(self, texts: list[str], batch_size: int = 8) -> list[float]:
        out: list[float] = []
        for i in range(0, len(texts), batch_size):
            batch = [self._normalize(t, typography=self.typography) for t in texts[i:i + batch_size]]
            enc = self.tokenizer(batch, truncation=True, max_length=MAX_TOKENS, padding=True,
                                 return_tensors="pt").to(self.device)
            logits = self.model(**enc).logits.float()
            out.extend((logits[:, 1] - logits[:, 0]).tolist())
        return out
