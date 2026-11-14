"""Binoculars style score with a configurable observer and performer pair.

Follows the reference implementation (github.com/ahans30/Binoculars): log perplexity of the text
under the performer, divided by the cross entropy between observer and performer next token
distributions. Low raw values indicate machine text, so `ai_score` is the negated ratio.

The paper's numbers were measured with Falcon 7B and Falcon 7B Instruct. Any other pair, including
the small Qwen pair used in our experiments, is an unvalidated configuration and must be reported
as such.
"""

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

MAX_TOKENS = 512


class BinocularsScorer:
    def __init__(self, observer_dir: str, performer_dir: str, device: str, name: str):
        self.name = name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(observer_dir)
        self.tokenizer.padding_side = "right"
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        # Both models must share one tokenizer; the cross entropy compares their distributions token by token.
        performer_tok = AutoTokenizer.from_pretrained(performer_dir)
        if performer_tok.get_vocab() != self.tokenizer.get_vocab():
            raise ValueError("observer and performer tokenizers differ")
        kwargs = {"dtype": torch.bfloat16}
        self.observer = AutoModelForCausalLM.from_pretrained(observer_dir, **kwargs).to(device).eval()
        self.performer = AutoModelForCausalLM.from_pretrained(performer_dir, **kwargs).to(device).eval()

    @torch.inference_mode()
    def raw_scores(self, texts: list[str], batch_size: int = 1) -> list[float]:
        out: list[float] = []
        for i in range(0, len(texts), batch_size):
            enc = self.tokenizer(texts[i:i + batch_size], truncation=True, max_length=MAX_TOKENS,
                                 padding=True, return_tensors="pt").to(self.device)
            obs = self.observer(**enc).logits.float()
            perf = self.performer(**enc).logits.float()

            # Perplexity: shifted next token loss under the performer (reference metrics.perplexity).
            shift_mask = enc["attention_mask"][:, 1:].float()
            token_loss = F.cross_entropy(perf[:, :-1].transpose(1, 2), enc["input_ids"][:, 1:], reduction="none")
            log_ppl = (token_loss * shift_mask).sum(1) / shift_mask.sum(1)

            # Cross perplexity: the reference averages over every position without shifting
            # (metrics.entropy), so the last position is included here as well.
            full_mask = enc["attention_mask"].float()
            x_ent = -(F.softmax(obs, dim=-1) * F.log_softmax(perf, dim=-1)).sum(-1)
            log_x_ppl = (x_ent * full_mask).sum(1) / full_mask.sum(1)
            out.extend((log_ppl / log_x_ppl).tolist())
        return out

    def score(self, texts: list[str], batch_size: int = 1) -> list[float]:
        return [-r for r in self.raw_scores(texts, batch_size)]
