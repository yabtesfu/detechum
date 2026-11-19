"""Per token predictability under a causal language model (the GLTR family of signals).

For every token after the first, records whether it was the model's single most likely next token
and its surprisal in nats. These values describe a text. They are not an `ai_score`, and they do
not feed the verdict (docs/design/architecture.md §2.4).
"""

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

MAX_TOKENS = 512


@dataclass(frozen=True)
class TokenStats:
    """Values for the predicted tokens of one text, in order. The first token has no prediction."""

    spans: list[tuple[int, int]]   # character offsets of each predicted token in the input text
    top1: list[bool]               # the token was the model's most likely next token
    surprisal: list[float]         # negative log probability of the token, in nats
    truncated: bool                # the text was longer than MAX_TOKENS

    @property
    def top1_rate(self) -> float:
        return sum(self.top1) / len(self.top1) if self.top1 else float("nan")


class TokenStatsScorer:
    def __init__(self, model_dir: str, device: str, name: str):
        self.name = name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.tokenizer.padding_side = "right"
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16).to(device).eval()

    @torch.inference_mode()
    def stats(self, texts: list[str], batch_size: int = 4) -> list[TokenStats]:
        out: list[TokenStats] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            enc = self.tokenizer(batch, truncation=True, max_length=MAX_TOKENS, padding=True,
                                 return_offsets_mapping=True, return_tensors="pt")
            offsets = enc.pop("offset_mapping")
            lengths = enc["attention_mask"].sum(1).tolist()
            enc = enc.to(self.device)
            logits = self.model(**enc).logits[:, :-1]
            targets = enc["input_ids"][:, 1:]
            target_logit = logits.gather(-1, targets.unsqueeze(-1))
            # Ties count as most likely: bfloat16 logits can coincide at the top.
            top1 = ((logits > target_logit).sum(-1) == 0).cpu()
            surprisal = F.cross_entropy(logits.float().transpose(1, 2), targets, reduction="none").cpu()
            for row, text in enumerate(batch):
                n = lengths[row]
                full_length = len(self.tokenizer(text, truncation=False)["input_ids"])
                out.append(TokenStats(
                    spans=[tuple(pair) for pair in offsets[row, 1:n].tolist()],
                    top1=top1[row, :n - 1].tolist(),
                    surprisal=surprisal[row, :n - 1].tolist(),
                    truncated=full_length > MAX_TOKENS))
        return out
