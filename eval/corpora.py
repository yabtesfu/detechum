"""Load the evaluation corpora from data/external as records with text and metadata.

Sources are fetched by eval/fetch_data.py, and the Liang et al. repository by a git clone at the
commit named in docs/evaluation/plan.md §8. Record fields follow the manifest of plan §1.
`group_key` names the unit that must stay inside one split: the prompt for essays and for
generated text, the document for everything else.

`flags` records what limits the use of a text:

* "pilot": its scores and labels were seen in the pilots, so it may only be in calib.
* "source_in_scorer_training": it comes from RAID, on which the GPTTrace scorer was trained, so it
  is no evidence about unseen human text.
"""

import csv
import io
import json
import zipfile
from pathlib import Path

ELLIPSE_TEST_PASSWORD = b"ellipse_test"  # published in the corpus README

# (folder, label, author group, domain, generator)
LIANG_GROUPS = [
    ("Human_Data/TOEFL_real_91", "human", "nonnative", "student_essay", None),
    ("Human_Data/HewlettStudentEssay_real_88", "human", "native", "student_essay", None),
    ("Human_Data/CollegeEssay_real_70", "human", "native", "student_essay", None),
    ("Human_Data/CS224N_real_145", "human", "unknown", "academic", None),
    ("Human_Data/TOEFL_gpt4polished_91", "ai_edited", "nonnative", "student_essay", "gpt-4 (polish)"),
    ("Human_Data/HewlettStudentEssay_GPTsimplify_88", "ai_edited", "native", "student_essay", "chatgpt (simplify)"),
    ("GPT_Data/CollegeEssay_gpt3_31", "ai", None, "student_essay", "gpt-3"),
    ("GPT_Data/CollegeEssay_gpt3PromptEng_31", "ai", None, "student_essay", "gpt-3 (prompt engineered)"),
    ("GPT_Data/CS224N_gpt3_145", "ai", None, "academic", "gpt-3"),
    ("GPT_Data/CS224N_gpt3PromptEng_145", "ai", None, "academic", "gpt-3 (prompt engineered)"),
]


def _record(text, source, source_id, label, author_group, domain, generator, group_key, license, date_written,
            flags=()):
    return {"text": text, "source": source, "source_id": str(source_id), "label": label,
            "author_group": author_group, "domain": domain, "generator": generator,
            "group_key": f"{source}/{group_key}", "license": license, "date_written": date_written,
            "flags": list(flags)}


def _jsonl(path: Path) -> list[dict]:
    # Split on the newline only: str.splitlines also breaks at separators such as U+2028, which occur
    # inside the texts.
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def ellipse(root: Path) -> list[dict]:
    csv.field_size_limit(10 ** 9)
    with (root / "ELLIPSE_Final_github_train.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with zipfile.ZipFile(root / "ELLIPSE_Final_github_test.zip") as archive:
        data = archive.read("ELLIPSE_Final_github_test.csv", pwd=ELLIPSE_TEST_PASSWORD)
    rows += list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))
    # The date is an upper bound from the public release of these essays, not a date of writing.
    return [_record(r["full_text"], "ellipse", r["text_id_kaggle"], "human", "nonnative", "student_essay", None,
                    f"prompt/{r['prompt']}", "CC BY 4.0", "2022-08 or earlier") for r in rows]


def textsight(root: Path) -> list[dict]:
    data = root / "data"
    out = []
    for r in _jsonl(data / "human_literature_publicdomain.jsonl"):
        out.append(_record(r["text"], "textsight", r["id"], "human", "unknown", "literature", None,
                           f"work/{r['attribution']}", "public domain", "before 1940"))
    for r in _jsonl(data / "human_pmc_ccby_nonanglophone.jsonl"):
        # Nonnative is inferred by the dataset from the country of the authors' affiliation.
        out.append(_record(r["text"], "textsight", r["id"], "human", "nonnative", "academic", None,
                           f"pmc/{r['pmc_id']}", r["licence"], r["publication_year"]))
    for r in _jsonl(data / "human_wikipedia_pre2022.jsonl"):
        out.append(_record(r["text"], "textsight", r["id"], "human", "unknown", "encyclopedic", None,
                           f"article/{r['id'].rsplit('-', 1)[0]}", r["licence"], "before 2022"))
    for r in _jsonl(data / "ai_generated_2026-09-29.jsonl"):
        out.append(_record(r["text"], "textsight", r["id"], "ai", None, r["genre"], r["source"],
                           f"topic/{r['topic']}", "CC BY SA 4.0", r["generated"]))
    return out


def meld(root: Path) -> list[dict]:
    out = []
    for r in _jsonl(root / "meld_sample.jsonl"):
        human = r["label"] == 0
        out.append(_record(
            r["text"], "meld", r["id"], "human" if human else "ai", "unknown" if human else None, r["domain"],
            None if human else r["generator"], r["prompt_id"], "terms of the original source",
            "not stated (earlier public corpora, notably RAID)" if human else "2026",
            flags=("source_in_scorer_training",) if human else ()))
    return out


def liang(root: Path) -> list[dict]:
    out = []
    for folder, label, author_group, domain, generator in LIANG_GROUPS:
        name = Path(folder).name
        docs = json.loads((root / "Data_and_Results" / folder / "data.json").read_text(encoding="utf-8"))
        for i, d in enumerate(docs):
            out.append(_record(d["document"], "liang", f"{name}/{i}", label, author_group, domain, generator,
                               f"{name}/{i}", "none stated", "2023 or earlier", flags=("pilot",)))
    return out


def load_all(root: Path) -> list[dict]:
    """Every record of every corpus under `root`, in a fixed order."""
    return (ellipse(root / "ellipse") + textsight(root / "textsight") + meld(root / "meld")
            + liang(root / "liang"))
