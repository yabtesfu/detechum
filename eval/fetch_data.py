"""Download the pinned evaluation corpora into data/external (docs/evaluation/plan.md §1).

Three sources, about 23 MB in total:

* ELLIPSE (Crossley et al. 2023): essays by English language learners in grades 8 to 12. CC BY 4.0.
* TextSight AI text detection benchmark 2026: human passages and AI text from five 2026 models.
  CC BY SA 4.0.
* MELD-eval (arXiv 2605.06903), from an unmodified mirror: AI text from four 2026 chat models and
  the human passages they were conditioned on. The file is 634 MB, so only fixed byte ranges of it
  are fetched and a sample of its unattacked rows is kept. Labels are CC BY 4.0; the texts stay
  under the terms of their sources.

Every file is checked against a pinned SHA 256. For ELLIPSE and TextSight the pinned digests were
computed on 2026-11-19 from copies whose git blob ids matched the listing of the pinned revision.
The digest of the MELD sample pins the result of the range requests below.

Texts stay in data/external, which is not committed.

Usage: .venv/bin/python eval/fetch_data.py [--dest data/external]
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from detechum.models import sha256_of

USER_AGENT = "detechum-fetch/0.1"
TIMEOUT = 60
MAX_ATTEMPTS = 8

ELLIPSE_URL = "https://raw.githubusercontent.com/scrosseye/ELLIPSE-Corpus/710963bbf1acf23a28e40643d9f937d06f047dd4/"
TEXTSIGHT_URL = ("https://huggingface.co/datasets/textsightai/ai-text-detection-benchmark-2026/resolve/"
                 "423b1768f0827675295fd6dc3cd255ad2f411183/")
# (local path under the destination, URL, SHA 256)
FILES = [
    ("ellipse/ELLIPSE_Final_github_train.csv", ELLIPSE_URL + "ELLIPSE_Final_github_train.csv",
     "782344e99668a3ff508d7410c0eb6e36da70f3b28f81c96e367f1ca04924b06c"),
    # Encrypted by its authors; the password is published in the corpus README.
    ("ellipse/ELLIPSE_Final_github_test.zip", ELLIPSE_URL + "ELLIPSE_Final_github_test.zip",
     "9ecddfcda83f6a99c8a24dda47fb1c30673fedeaf578a0fadac6645fd151a2f8"),
    ("ellipse/README.md", ELLIPSE_URL + "README.md",
     "141dfce9ee17925b83cce22805aab7bfb0f1adc1ca27ddd549319e4ccd6ac3fc"),
    ("textsight/data/ai_generated_2026-09-29.jsonl", TEXTSIGHT_URL + "data/ai_generated_2026-09-29.jsonl",
     "173df332cdc095f4f193e0d429efd9b9ff33a0e7c55f6281570fcee1fa91a93e"),
    ("textsight/data/human_literature_publicdomain.jsonl", TEXTSIGHT_URL + "data/human_literature_publicdomain.jsonl",
     "92cb6e64d875d9f4cc4b585e7c8370635923d59a33a242b6bebf3b12ff61806c"),
    ("textsight/data/human_pmc_ccby_nonanglophone.jsonl", TEXTSIGHT_URL + "data/human_pmc_ccby_nonanglophone.jsonl",
     "9a813ee0b1abc1c451eb27c7a42a27f77df587f7a4299df439f1ec39d3a3e395"),
    ("textsight/data/human_wikipedia_pre2022.jsonl", TEXTSIGHT_URL + "data/human_wikipedia_pre2022.jsonl",
     "bb9e9f918a4edf44a491400850f6e3027916943b26c153df2a56ae75b6853889"),
    ("textsight/README.md", TEXTSIGHT_URL + "README.md",
     "31fd6010989b7befddf11e95dbd9fc5334a71be0f28e9fb9679c742ead57a537"),
]

MELD_URL = ("https://huggingface.co/datasets/odeveloper/meld-eval/resolve/"
            "b0c10f3bdf7737aae2b61f6d0332f47c291a1319/meld_eval.jsonl")
MELD_SIZE = 634064489
# The file is ordered by generator, then attack, then domain, with the unattacked rows first in
# each generator's block and the human rows at the end. These are the byte ranges of the five
# unattacked sections, located on 2026-11-19 by bisection with small range requests.
# (generator, first byte, byte after the section)
MELD_SECTIONS = [
    ("gpt-5.4-mini", 0, 21760082),
    ("gemini-3-flash", 154100216, 174731989),
    ("claude-haiku", 300248937, 321766541),
    ("qwen-3.6-plus", 452579282, 476172918),
    ("human", 619591965, MELD_SIZE),
]
MELD_WINDOWS = 40          # evenly spaced windows per section, so that every domain is reached
MELD_WINDOW_BYTES = 55000
MELD_SAMPLE = "meld/meld_sample.jsonl"
MELD_SAMPLE_SHA256 = "cb8f2fd2a80f07b28fbbbdbd96318e0bbf6395a70c8770655e7322e8f4518114"


def get(url: str, byte_range: tuple[int, int] | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if byte_range:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as r:
                if byte_range and r.status != 206:
                    raise ConnectionError(f"expected HTTP 206 for a range request, got {r.status}")
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            print(f"  retry {attempt}: {exc}", flush=True)
            time.sleep(min(30, 2 * attempt))
    raise SystemExit(f"could not download {url}")


def fetch_file(url: str, out: Path, sha: str) -> None:
    if out.exists() and sha256_of(out) == sha:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(get(url))
    if sha256_of(out) != sha:
        out.unlink()
        raise SystemExit(f"{out} failed SHA 256 verification and was removed")
    print(f"  {out}: verified", flush=True)


def meld_rows(section: tuple[str, int, int]) -> list[dict]:
    """Unattacked rows of one section that lie whole inside its sampling windows."""
    generator, start, end = section
    rows = []
    for i in range(MELD_WINDOWS):
        offset = start + i * (end - start) // MELD_WINDOWS
        lines = get(MELD_URL, (offset, min(MELD_SIZE, offset + MELD_WINDOW_BYTES) - 1)).split(b"\n")
        # A window starts inside a row unless it starts the section, and it ends inside a row unless
        # it ends the file. Those partial rows are dropped.
        lines = lines[0 if offset == start else 1:None if offset + MELD_WINDOW_BYTES >= MELD_SIZE else -1]
        for line in lines:
            if line.strip():
                row = json.loads(line)
                if row["generator"] == generator and row["attack"] == "none":
                    rows.append(row)
    return rows


def fetch_meld_sample(out: Path) -> None:
    if out.exists() and sha256_of(out) == MELD_SAMPLE_SHA256:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, kept = set(), []
    for section in MELD_SECTIONS:
        for row in meld_rows(section):
            if row["id"] not in seen:
                seen.add(row["id"])
                kept.append(row)
        print(f"  MELD-eval {section[0]}: {len(kept)} rows so far", flush=True)
    out.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in kept),
                   encoding="utf-8")
    if sha256_of(out) != MELD_SAMPLE_SHA256:
        out.unlink()
        raise SystemExit(f"{out} failed SHA 256 verification and was removed")
    print(f"  {out}: {len(kept)} rows, verified", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", type=Path, default=Path("data/external"))
    args = ap.parse_args()
    for path, url, sha in FILES:
        fetch_file(url, args.dest / path, sha)
    fetch_meld_sample(args.dest / MELD_SAMPLE)
    print("all evaluation data downloaded and verified", flush=True)


if __name__ == "__main__":
    main()
