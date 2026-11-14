"""Input normalisation before scoring, with a report of what was changed (docs/design/architecture.md \u00a72.1).

The original text is never modified; `normalize` returns a scoring copy plus counts. Invisible
characters and mixed script lookalike letters are reported as possible evasion. Typographic spaces
are reported separately because word processors insert them on their own.

Multilingual text is protected:
* a word written entirely in Cyrillic or Greek is left alone; lookalikes are mapped only inside
  words that mix them with Latin letters;
* zero width joiner and non joiner are removed only between Latin letters, since emoji sequences and
  scripts such as Persian and the Indic scripts depend on them.
"""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

ZWJ, ZWNJ = "\u200d", "\u200c"

# Cyrillic and Greek letters that render like Latin letters in common fonts.
LOOKALIKES = {
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0443": "y", "\u0445": "x",
    "\u0456": "i", "\u0458": "j", "\u0455": "s", "\u04bb": "h", "\u0501": "d", "\u051b": "q", "\u051d": "w",
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M", "\u041d": "H", "\u041e": "O",
    "\u0420": "P", "\u0421": "C", "\u0422": "T", "\u0425": "X", "\u0406": "I", "\u0408": "J", "\u0405": "S",
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0399": "I", "\u039a": "K",
    "\u039c": "M", "\u039d": "N", "\u039f": "O", "\u03a1": "P", "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
    "\u03bf": "o", "\u03bd": "v", "\u03b9": "i", "\u03ba": "k", "\u03c1": "p", "\u03c4": "t", "\u03c5": "u",
    "\u03b1": "a",
}
_WORD = re.compile(r"[^\W\d_]+")
_LATIN = re.compile(r"[A-Za-z\u00c0-\u024f]")


@dataclass
class NormalizationReport:
    invisible: Counter = field(default_factory=Counter)      # code point name -> count removed
    lookalikes: Counter = field(default_factory=Counter)     # "Cyrillic \u0430 -> a" style key -> count
    typographic_spaces: Counter = field(default_factory=Counter)

    @property
    def evasion_suspected(self) -> bool:
        return bool(self.invisible or self.lookalikes)

    def summary(self) -> list[str]:
        lines = []
        if self.invisible:
            lines.append(f"{sum(self.invisible.values())} invisible characters removed before scoring")
        if self.lookalikes:
            lines.append(f"{sum(self.lookalikes.values())} lookalike letters inside Latin words replaced")
        if self.typographic_spaces:
            lines.append(f"{sum(self.typographic_spaces.values())} typographic spaces replaced with normal spaces")
        return lines


def _is_latin(ch: str) -> bool:
    return bool(ch) and bool(_LATIN.match(ch))


def _strip_invisible(text: str, report: NormalizationReport) -> str:
    out = []
    for i, ch in enumerate(text):
        if unicodedata.category(ch) != "Cf" and not ("\ufe00" <= ch <= "\ufe0f"):
            out.append(ch)
            continue
        if ch in (ZWJ, ZWNJ):
            prev = text[i - 1] if i > 0 else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if not (_is_latin(prev) and _is_latin(nxt)):
                out.append(ch)  # legitimate joiner (emoji sequence or a non Latin script)
                continue
        if "\ufe00" <= ch <= "\ufe0f":
            prev = text[i - 1] if i > 0 else ""
            if prev and not _is_latin(prev) and not prev.isspace():
                out.append(ch)  # variation selector attached to an emoji or symbol
                continue
        report.invisible[unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
    return "".join(out)


def _fix_lookalikes(text: str, report: NormalizationReport) -> str:
    def fix(m: re.Match) -> str:
        word = m.group()
        if not any(c in LOOKALIKES for c in word) or not _LATIN.search(word):
            return word  # pure Cyrillic or Greek words stay as written
        mapped = []
        for c in word:
            if c in LOOKALIKES:
                report.lookalikes[f"{unicodedata.name(c)} -> {LOOKALIKES[c]}"] += 1
                mapped.append(LOOKALIKES[c])
            else:
                mapped.append(c)
        return "".join(mapped)

    return _WORD.sub(fix, text)


def _fix_spaces(text: str, report: NormalizationReport) -> str:
    out = []
    for ch in text:
        if ch != " " and unicodedata.category(ch) == "Zs":
            report.typographic_spaces[unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def normalize(text: str) -> tuple[str, NormalizationReport]:
    report = NormalizationReport()
    cleaned = _strip_invisible(text, report)
    cleaned = _fix_lookalikes(cleaned, report)
    cleaned = _fix_spaces(cleaned, report)
    return cleaned, report
