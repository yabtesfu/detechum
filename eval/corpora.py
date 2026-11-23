"""Load the evaluation corpora from data/external as records with text and metadata.

Sources are fetched by eval/fetch_data.py, and the Liang et al. repository by a git clone at the
commit named in docs/evaluation/plan.md §8. Record fields follow the manifest of plan §1.
`group_key` names the unit that must stay inside one split: the prompt for essays and for
generated text, the document for everything else.

`flags` records what limits the use of a text:

* "pilot": its scores and labels were seen in the pilots, so it may only be in calib.
* "source_in_scorer_training": it comes from RAID, on which the GPTTrace scorer was trained, so it
  is no evidence about unseen human text.
* "attacked": AI text that was paraphrased or rewritten to hide its origin (plan §2, M4). It stays out
  of the AI error rates and is reported on its own.
* "seen_before_freeze": its scores were looked at before eval_plan_v2 was tagged, so it may only be
  in calib.

The corpora added for eval_plan_v2 (plan §10) also carry `variant`, the way a text was produced, and,
for essays written on an ELLIPSE prompt, `topic`, the name of that prompt.
"""

import csv
import io
import json
import re
import sqlite3
import zipfile
from pathlib import Path

ELLIPSE_TEST_PASSWORD = b"ellipse_test"  # published in the corpus README
from essay_tasks import TOPICS as ELLIPSE_TOPICS  # noqa: E402  the 44 ELLIPSE prompt names

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
            flags=(), **extra):
    return {"text": text, "source": source, "source_id": str(source_id), "label": label,
            "author_group": author_group, "domain": domain, "generator": generator,
            "group_key": f"{source}/{group_key}", "license": license, "date_written": date_written,
            "flags": list(flags), **extra}


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


GEDE_LICENSE = "CC BY-NC-SA 4.0"
GEDE_DATASETS = {1: "argument-annotated-essays", 3: "BAWE"}  # 2 is PERSUADE, left out (plan §9)
GEDE_PLAIN = {"task", "task+summary", "summary", "task+resource"}
GEDE_EDITED = {"improve-human", "rewrite-human"}


def gede(root: Path) -> list[dict]:
    """GEDE (Gehring et al.): BAWE university essays and essays from an online forum, with AI essays.

    The human essays of the forum set are not in the database, so only BAWE gives human text. Its writers
    are native when their first language is English. An AI rewrite of an AI essay and a DIPPER
    paraphrase are marked as attacked.
    """
    db = sqlite3.connect(root / "database.db")
    rows = db.execute("""
        select a.id, a.answer, a.is_human, a.question_id, q.dataset_id, j.model, j.prompt_mode, h.L1,
               a.created_at
        from answers a join questions q on q.id = a.question_id
        left join jobs j on j.id = a.job_id left join human_meta h on h.answer_id = a.id
        where q.dataset_id in (1, 3) and a.answer is not null""").fetchall()
    out = []
    for aid, text, is_human, qid, ds, model, mode, l1, created in rows:
        common = dict(source="gede", source_id=aid, domain="student_essay", group_key=f"question/{qid}",
                      license=GEDE_LICENSE)
        if is_human:
            group = "unknown" if l1 is None else "native" if l1 == "English" else "nonnative"
            out.append(_record(text, label="human", author_group=group, generator=None,
                               date_written="before 2008", variant=GEDE_DATASETS[ds], **common))
        elif mode in GEDE_PLAIN or mode in GEDE_EDITED:
            out.append(_record(text, label="ai" if mode in GEDE_PLAIN else "ai_edited", author_group=None,
                               generator=model, date_written=created[:10], variant=mode, **common))
        else:  # "dipper-<job>" or "rewrite-<job>": a paraphrase of an AI essay
            out.append(_record(text, label="ai", author_group=None, generator=model, date_written=created[:10],
                               variant=mode.split("-")[0], flags=("attacked",), **common))
    return out


def ghostbuster(root: Path) -> list[dict]:
    """Ghostbuster essays (Verma et al.): IvyPanda essays and essays by GPT 3.5 and Claude on their prompts.

    The rows named "prompts" hold the prompts, not essays, and are left out. `file_number` names the
    prompt, so it is the group.
    """
    import pyarrow.parquet as pq
    out = []
    for r in pq.read_table(root / "train-00000-of-00001.parquet").to_pylist():
        if r["model"] == "prompts":
            continue
        human = r["model"] == "human"
        generator = None if human else "claude (2023)" if r["model"] == "claude" else "gpt-3.5-turbo (2023)"
        out.append(_record(r["text"], "ghostbuster", f"{r['model']}/{r['file_number']}", "human" if human else "ai",
                           "unknown" if human else None, "student_essay", generator, f"prompt/{r['file_number']}",
                           "CC BY 3.0", "2023 or earlier", variant=r["model"]))
    return out


def dactyl(root: Path) -> list[dict]:
    """The AI student essays of the DACTYL test split.

    Its human essays are left out: their source is not stated, and they may come from PERSUADE, which may
    overlap the scorer's training data. AI essays written on an ELLIPSE prompt carry that prompt as topic.
    """
    import pyarrow.parquet as pq
    topics = {t.lower(): t for t in ELLIPSE_TOPICS}
    out = []
    for r in pq.read_table(root / "test.parquet").to_pylist():
        if r["domain"] != "student_essays" or r["model"] == "human":
            continue
        info = json.loads(r["category_info"]) if r["category_info"] not in (None, "None") else {}
        topic = topics.get(str(info.get("topic", "")).lower())
        voice = "learner" if info.get("ELL") == "True" else "plain"
        out.append(_record(r["text"], "dactyl", r["id"], "ai", None, "student_essay", r["model"],
                           f"topic/{topic}" if topic else f"text/{r['id']}", "MIT", str(r["created_at"])[:10],
                           variant=voice, topic=topic))
    return out


def generated(root: Path, name: str, flags=()) -> list[dict]:
    """Essays written for this project from `essay_tasks` (plan §10), with their records.jsonl."""
    out = []
    for r in _jsonl(root / "records.jsonl"):
        text = (root / f"{r['id']}.txt").read_text(encoding="utf-8")
        out.append(_record(text, name, r["id"], "ai", None, "student_essay", r["generator"], f"topic/{r['topic']}",
                           "written for this project", r["written_at"][:10], flags=flags,
                           variant=f"{r['kind']}/{r['voice']}", topic=r["topic"]))
    return out


def ellipse_topic(record: dict) -> str | None:
    """The ELLIPSE prompt of an ELLIPSE essay, read from its group key."""
    m = re.fullmatch(r"ellipse/prompt/(.+)", record["group_key"])
    return m.group(1) if m else None


def load_all_v2(root: Path) -> list[dict]:
    """Every record of the corpora of eval_plan_v2: those of eval_v1 plus the ones added in plan §10."""
    out = load_all(root)
    for r in out:
        r["topic"] = ellipse_topic(r)
    out += gede(root / "gede") + ghostbuster(root / "ghostbuster") + dactyl(root / "dactyl")
    out += generated(root / "generated" / "claude", "claude_essays", flags=("seen_before_freeze",))
    if (root / "generated" / "qwen" / "records.jsonl").exists():
        out += generated(root / "generated" / "qwen", "qwen_essays")
    return out


def load_all(root: Path) -> list[dict]:
    """Every record of every corpus under `root`, in a fixed order."""
    return (ellipse(root / "ellipse") + textsight(root / "textsight") + meld(root / "meld")
            + liang(root / "liang"))
