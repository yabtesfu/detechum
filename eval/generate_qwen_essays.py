"""Write AI student essays with the local Qwen 2.5 1.5B Instruct model, for eval_plan_v2.

The tasks come from `essay_tasks.tasks`, so these essays share topics, kinds, lengths and voices with the
essays of the other generators. Each essay is saved as <id>.txt in the output folder, and one row per
essay goes to records.jsonl with the task, the model revision, the decoding settings and the time. A run
that is stopped continues with the essays that are missing.

The model files are verified against their pinned SHA 256 before loading. Nothing is downloaded.
Generation keeps the machine busy for a few hours, so run it when the machine is free:

    cd eval && caffeinate -i ../.venv/bin/python generate_qwen_essays.py
    cd eval && caffeinate -i ../.venv/bin/python generate_qwen_essays.py --short   # the batch of short essays

The batch of short essays was added before the tag eval_plan_v2, because calib held few AI essays of 150 to
249 words (plan §10). Qwen writes about one and a half times the target it is given, so the targets are 120
and 160 words, with a larger token budget so that the essays are not cut off.
"""

import argparse
import datetime
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from detechum.models import QWEN_INSTRUCT, ModelVerificationError, verify_model
from essay_tasks import LENGTHS, tasks

SEED = 20261121
N_ESSAYS = 400
BATCH = 8
DECODING = {"do_sample": True, "temperature": 0.8, "top_p": 0.95, "repetition_penalty": 1.05}
TOKENS_PER_WORD = 1.6  # the token budget is this times the target length, plus a margin
# (id prefix, seed, target lengths, number of essays, tokens per word) of each batch
BATCHES = {"main": ("qwen-", SEED, LENGTHS, N_ESSAYS, TOKENS_PER_WORD),
           "short": ("qwen-short-", 20261122, [120, 160], 400, 2.5)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", type=Path, default=Path("../data/external/models"))
    ap.add_argument("--out", type=Path, default=Path("../data/external/generated/qwen"))
    ap.add_argument("--short", action="store_true", help="write the batch of short essays")
    ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    args = ap.parse_args()
    prefix, seed, lengths, n, tokens_per_word = BATCHES["short" if args.short else "main"]

    try:
        folder = verify_model(QWEN_INSTRUCT, args.models)
    except ModelVerificationError as exc:
        raise SystemExit(f"{exc}; rerun eval/fetch_models.py")
    args.out.mkdir(parents=True, exist_ok=True)
    todo = [t for t in tasks(n, seed, prefix, lengths) if not (args.out / f"{t['id']}.txt").exists()]
    print(f"{len(todo)} of {n} essays to write", flush=True)
    if not todo:
        print("done", flush=True)
        return

    torch.manual_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(folder, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(folder, dtype=torch.bfloat16).to(args.device).eval()

    # Tasks of one length share a batch, so that no essay waits for a much longer one.
    todo.sort(key=lambda t: t["target_words"])
    for start in range(0, len(todo), BATCH):
        batch = todo[start:start + BATCH]
        prompts = [tokenizer.apply_chat_template([{"role": "user", "content": t["instruction"]}],
                                                 tokenize=False, add_generation_prompt=True) for t in batch]
        inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(args.device)
        budget = int(max(t["target_words"] for t in batch) * tokens_per_word) + 64
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=budget, pad_token_id=tokenizer.eos_token_id,
                                    **DECODING)
        when = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        with (args.out / "records.jsonl").open("a", encoding="utf-8") as log:
            for t, row in zip(batch, output[:, inputs["input_ids"].shape[1]:]):
                text = tokenizer.decode(row, skip_special_tokens=True).strip()
                hit_budget = bool((row != tokenizer.eos_token_id).all())
                (args.out / f"{t['id']}.txt").write_text(text + "\n", encoding="utf-8")
                log.write(json.dumps(t | {"generator": "qwen2.5-1.5b-instruct", "model": QWEN_INSTRUCT.record(),
                                          "decoding": DECODING | {"max_new_tokens": budget}, "seed": seed,
                                          "written_at": when, "stopped_at_token_budget": hit_budget}) + "\n")
        print(f"{start + len(batch)}/{len(todo)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
