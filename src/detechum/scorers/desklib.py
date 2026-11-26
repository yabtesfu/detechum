"""Desklib AI text detector v1.01, a candidate second signal (docs/evaluation/plan.md §10).

Model card: https://huggingface.co/desklib/ai-text-detector-v1.01 (MIT). DeBERTa v3 large fine tuned on
RAID, with mean pooling over the tokens and one linear layer. The score is that layer's logit; the card
turns it into a probability with a sigmoid and a cut at 0.5, which is the vendor's choice, not ours.

The card defines the model in its usage code rather than in the package. The same layers are built here
and the weights are loaded with every key required, so a file that does not match fails to load.
"""

from pathlib import Path

import torch
from safetensors.torch import load_file
from torch import nn
from transformers import AutoConfig, AutoModel, AutoTokenizer

MAX_TOKENS = 768  # the card's usage example truncates here


class _DesklibModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.model = AutoModel.from_config(config)
        self.classifier = nn.Linear(config.hidden_size, 1)

    def forward(self, input_ids, attention_mask):
        hidden = self.model(input_ids, attention_mask=attention_mask)[0]
        mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return self.classifier(pooled).squeeze(-1)


class DesklibScorer:
    name = "desklib_ai_text_detector_v1.01"

    def __init__(self, folder: str, device: str):
        folder = Path(folder)
        self.tokenizer = AutoTokenizer.from_pretrained(folder)
        model = _DesklibModel(AutoConfig.from_pretrained(folder))
        model.load_state_dict(load_file(folder / "model.safetensors"), strict=True)
        self.model = model.to(device).eval()
        self.device = device

    def is_truncated(self, text: str) -> bool:
        """True when `text` exceeds the input limit, so `score` sees only its beginning."""
        return len(self.tokenizer(text, truncation=False)["input_ids"]) > MAX_TOKENS

    @torch.inference_mode()
    def score(self, texts: list[str], batch_size: int = 8) -> list[float]:
        out: list[float] = []
        for i in range(0, len(texts), batch_size):
            enc = self.tokenizer(texts[i:i + batch_size], truncation=True, max_length=MAX_TOKENS, padding=True,
                                 return_tensors="pt").to(self.device)
            out.extend(self.model(enc["input_ids"], enc["attention_mask"]).float().tolist())
        return out
