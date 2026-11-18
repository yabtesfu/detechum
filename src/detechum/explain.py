"""Sentence level attribution for the document score (docs/design/architecture.md §5).

A sentence's contribution is the drop in the scorer's own score when that sentence is removed and
the rest of the text is scored again. The measure uses only the scorer that produces the verdict,
so it introduces no second signal. Contributions do not add up to the score: sentences interact,
and removing one changes the context of the others.
"""

import re
from dataclasses import dataclass

# Provisional. For a logit margin scorer, 1.0 multiplies the model's own odds by about 2.7.
MIN_CONTRIBUTION = 1.0
# Every sentence costs one more pass of the scorer.
MAX_SENTENCES = 60

_ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "prof", "st", "vs", "etc", "e.g", "i.e", "fig", "al", "cf"}
_CLOSERS = "\"')\\]" + chr(0x201D) + chr(0x2019)
_END = re.compile(rf"[.!?]+[{_CLOSERS}]*(?=\s)|\n\s*\n")


@dataclass(frozen=True)
class SentenceContribution:
    index: int             # position of the sentence in the text, starting at 1
    text: str
    score_without: float   # score of the text with this sentence removed
    contribution: float    # full score minus score_without; positive means the sentence raises the score


def _ends_sentence(text: str, start: int, end: int) -> bool:
    following = text[end:].lstrip()
    if following[:1].islower():
        return False
    last_word = text[start:end].split()[-1].rstrip(_CLOSERS.replace("\\", "")).rstrip(".!?")
    if last_word.lower() in _ABBREVIATIONS:
        return False
    return not (len(last_word) == 1 and last_word.isupper())  # an initial, as in "J. Smith"


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) character spans of the sentences of `text`, in order.

    Splits after ., ! or ? followed by whitespace, and at blank lines. Built for English prose: a
    period after a listed abbreviation or a single capital letter does not end a sentence.
    """
    spans, start = [], 0

    def close(end: int) -> None:
        nonlocal start
        begin = start + len(text[start:end]) - len(text[start:end].lstrip())
        if text[begin:end].strip():
            spans.append((begin, begin + len(text[begin:end].rstrip())))
        start = end

    for match in _END.finditer(text):
        if match.group().strip() == "":
            close(match.start())
            start = match.end()
        elif text[start:match.end()].strip() and _ends_sentence(text, start, match.end()):
            close(match.end())
    close(len(text))
    return spans


def sentence_contributions(text: str, scorer, full_score: float) -> list[SentenceContribution]:
    """Measure how much each of the first MAX_SENTENCES sentences raises or lowers `full_score`.

    `scorer.score` is called once with one variant of the text per sentence. Returns an empty list
    for a text with fewer than two sentences, where removal would leave nothing to score.
    """
    spans = split_sentences(text)
    if len(spans) < 2:
        return []
    spans = spans[:MAX_SENTENCES]
    variants = [f"{text[:a].rstrip()} {text[b:].lstrip()}".strip() for a, b in spans]
    scores = scorer.score(variants)
    return [SentenceContribution(index=i, text=text[a:b], score_without=float(s), contribution=full_score - float(s))
            for i, ((a, b), s) in enumerate(zip(spans, scores), start=1)]
