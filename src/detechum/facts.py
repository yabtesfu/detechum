"""Fact preservation check for revision mode (docs/design/architecture.md §6).

Compares an original text with a rewrite and reports checkable facts that were dropped, changed or
introduced: numbers, dates, quoted spans and capitalised names. Extraction is pattern based and
deliberately conservative: an equivalent restatement it cannot recognise (for example "a dozen" for
"12") is reported as missing, so the writer reviews it instead of the change passing silently.
"""

import re
from dataclasses import dataclass, field

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
MONTHS.update({name[:3]: num for name, num in list(MONTHS.items())})
MONTHS["sept"] = 9

# "one" is left out: it is far more often a pronoun ("one of the") than a quantity.
NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split()) if w != "one"}
NUMBER_WORDS.update({"thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
                     "eighty": "80", "ninety": "90", "hundred": "100"})

QUOTE_CHARS = {"“": '"', "”": '"', "‘": "'", "’": "'"}

_MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))
_DATE_PATTERNS = [
    # 14 Nov 2026, 14 November 2026
    (re.compile(rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\.?,?\s+(\d{{4}})\b", re.I), ("d", "m", "y")),
    # November 14, 2026
    (re.compile(rf"\b({_MONTH_ALT})\.?\s+(\d{{1,2}}),?\s+(\d{{4}})\b", re.I), ("m", "d", "y")),
    # 2026-11-14 (ISO 8601)
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), ("y", "mi", "d")),
]
_NUMBER = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|(?<![\w.])\d+(?:\.\d+)?%?")
_QUOTED = re.compile(r'"([^"\n]{3,})"')
_SENTENCE_START = re.compile(r"(?:^|[.!?:]\s+|\n\s*)([A-Z][\w'&.]*)")
_CAPITALISED = re.compile(r"\b[A-Z][\w'&]*(?:[ ][A-Z][\w'&]*)*")
_NAME_STOPWORDS = {"I", "I'm", "I've", "I'd", "I'll", "The", "A", "An", "This", "That", "These", "Those",
                   "It", "We", "They", "He", "She", "You"}


@dataclass
class FactCheck:
    missing: dict[str, list[str]] = field(default_factory=dict)
    added: dict[str, list[str]] = field(default_factory=dict)

    @property
    def preserved(self) -> bool:
        """True when no fact from the original is missing. Added facts do not fail the check but need review."""
        return not any(self.missing.values())


def _normalise_quotes(text: str) -> str:
    return "".join(QUOTE_CHARS.get(c, c) for c in text)


def _dates(text: str) -> tuple[set[tuple[int, int, int]], list[tuple[int, int]]]:
    found, spans = set(), []
    for pattern, order in _DATE_PATTERNS:
        for m in pattern.finditer(text):
            parts = dict(zip(order, m.groups()))
            month = int(parts["mi"]) if "mi" in parts else MONTHS[parts["m"].lower().rstrip(".")]
            found.add((int(parts["y"]), month, int(parts["d"])))
            spans.append(m.span())
    return found, spans


def _numbers(text: str, skip: list[tuple[int, int]]) -> set[str]:
    out = set()
    for m in _NUMBER.finditer(text):
        if any(a <= m.start() < b for a, b in skip):
            continue  # already counted as part of a date
        out.add(m.group().replace(",", ""))
    for word in re.findall(r"[A-Za-z]+", text):
        if word.lower() in NUMBER_WORDS:
            out.add(NUMBER_WORDS[word.lower()])
    return out


def _names(text: str) -> set[str]:
    # A capitalised word that opens a sentence is ambiguous (ordinary word or name), so only
    # mid sentence capitals count as names. Presence is later checked anywhere in the other text,
    # which keeps a name that moved to a sentence start from being reported as missing.
    sentence_initial = {m.start(1) for m in _SENTENCE_START.finditer(text)}
    names = set()
    for m in _CAPITALISED.finditer(text):
        phrase = m.group()
        if m.start() in sentence_initial:
            words = phrase.split(" ")[1:]
            phrase = " ".join(words)
        if phrase and phrase not in _NAME_STOPWORDS:
            names.add(phrase.rstrip("."))
    return names


def extract_facts(text: str) -> dict[str, set]:
    text = _normalise_quotes(text)
    dates, date_spans = _dates(text)
    return {
        "numbers": _numbers(text, date_spans),
        "dates": dates,
        "quotes": {" ".join(q.split()) for q in _QUOTED.findall(text)},
        "names": _names(text),
    }


def check_facts(original: str, rewrite: str) -> FactCheck:
    orig, new = extract_facts(original), extract_facts(rewrite)
    rewrite_flat = " ".join(_normalise_quotes(rewrite).split())
    original_flat = " ".join(_normalise_quotes(original).split())
    result = FactCheck()
    for kind in ("numbers", "dates", "quotes"):
        result.missing[kind] = sorted(map(str, orig[kind] - new[kind]))
        result.added[kind] = sorted(map(str, new[kind] - orig[kind]))
    result.missing["names"] = sorted(n for n in orig["names"] if n not in rewrite_flat)
    result.added["names"] = sorted(n for n in new["names"] if n not in original_flat)
    return result
