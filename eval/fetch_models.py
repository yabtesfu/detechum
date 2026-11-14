"""Download the pinned model files used by eval/bias_experiment.py into data/external/models.

Weight files are fetched as fixed size byte ranges over several connections. Each range is stored as
its own part file, so an interrupted run loses at most the unfinished ranges and a rerun skips every
completed one. Assembled files are checked against the SHA 256 published for the pinned revision.

Usage:
    .venv/bin/python eval/fetch_models.py [--dest data/external/models] [--workers 8]
"""

import argparse
import concurrent.futures
import hashlib
import shutil
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "detechum-fetch/0.1"
CHUNK = 32 * 1024 * 1024
READ_TIMEOUT = 30  # seconds without data before a connection is abandoned and retried
MAX_ATTEMPTS = 200

# Listed in download priority order: the primary scorer first.
MODELS = [
    {
        "repo": "nakas/gpttrace-v8s-1b", "revision": "ac748e32ca8c90bb8858fadc427757728e27b063",
        "folder": "gpttrace-v8s-1b",
        "small": ["normalize.py", "model/config.json", "model/tokenizer.json", "model/tokenizer_config.json"],
        "weights": ("model/model.safetensors", 4125087720,
                    "379b154cadb0fd6a226badd2f745705f49c19461ef150ee6b97fec92e82ba538"),
    },
    {
        "repo": "Qwen/Qwen2.5-1.5B", "revision": "8faed761d45a263340a0528343f099c05c9a4323",
        "folder": "qwen2.5-1.5b",
        "small": ["config.json", "generation_config.json", "merges.txt", "vocab.json", "tokenizer.json",
                  "tokenizer_config.json"],
        "weights": ("model.safetensors", 3087467144,
                    "a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796"),
    },
    {
        "repo": "Qwen/Qwen2.5-1.5B-Instruct", "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
        "folder": "qwen2.5-1.5b-instruct",
        "small": ["config.json", "generation_config.json", "merges.txt", "vocab.json", "tokenizer.json",
                  "tokenizer_config.json"],
        "weights": ("model.safetensors", 3087467144,
                    "dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee"),
    },
]


def hub_url(repo: str, revision: str, path: str) -> str:
    return f"https://huggingface.co/{repo}/resolve/{revision}/{path}"


def resolve(url: str) -> str:
    # The hub answers with a redirect to a signed CDN URL that expires, so it is resolved again on every attempt.
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r:
        return r.url


def fetch_small(url: str, out: Path) -> None:
    if out.exists() and out.with_suffix(out.suffix + ".done").exists():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r:
                out.write_bytes(r.read())
            out.with_suffix(out.suffix + ".done").touch()
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f"  retry {attempt} for {out.name}: {e}", flush=True)
            time.sleep(min(30, 2 * attempt))
    raise SystemExit(f"could not download {url}")


class Progress:
    def __init__(self, total: int, done: int):
        self.total, self.done, self.lock = total, done, threading.Lock()
        self.start, self.start_done = time.monotonic(), done

    def add(self, n: int) -> None:
        with self.lock:
            self.done += n

    def line(self) -> str:
        rate = (self.done - self.start_done) / max(1e-9, time.monotonic() - self.start)
        left = (self.total - self.done) / rate if rate > 0 else float("inf")
        eta = f"{left / 60:.0f} min" if left != float("inf") else "unknown"
        return f"{self.done / 1e9:.2f} of {self.total / 1e9:.2f} GB, {rate / 1e6:.2f} MB/s, about {eta} left"


def fetch_range(url: str, start: int, end: int, part: Path, progress: Progress) -> None:
    expected = end - start + 1
    for attempt in range(1, MAX_ATTEMPTS + 1):
        have = part.stat().st_size if part.exists() else 0
        if have == expected:
            return
        if have > expected:
            part.unlink()
            have = 0
        try:
            req = urllib.request.Request(resolve(url), headers={
                "User-Agent": USER_AGENT, "Range": f"bytes={start + have}-{end}"})
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r, part.open("ab") as fh:
                if r.status != 206:
                    raise ConnectionError(f"expected HTTP 206 for a range request, got {r.status}")
                while block := r.read(1 << 20):
                    fh.write(block)
                    progress.add(len(block))
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            time.sleep(min(30, 2 * attempt))
    raise SystemExit(f"gave up on {part.name} after {MAX_ATTEMPTS} attempts")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_weights(url: str, out: Path, size: int, sha: str, workers: int) -> None:
    marker = out.with_suffix(out.suffix + ".done")
    if out.exists() and marker.exists():
        return
    parts_dir = out.parent / (out.name + ".parts")
    parts_dir.mkdir(parents=True, exist_ok=True)
    ranges = [(i, s, min(s + CHUNK, size) - 1) for i, s in enumerate(range(0, size, CHUNK))]
    already = sum(p.stat().st_size for p in parts_dir.glob("*.part"))
    progress = Progress(size, already)
    stop = threading.Event()

    def report():
        while not stop.wait(30):
            print(f"  {out.name}: {progress.line()}", flush=True)

    reporter = threading.Thread(target=report, daemon=True)
    reporter.start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_range, url, s, e, parts_dir / f"{i:05d}.part", progress)
                   for i, s, e in ranges]
        for f in concurrent.futures.as_completed(futures):
            f.result()
    stop.set()

    tmp = out.with_suffix(out.suffix + ".assembling")
    with tmp.open("wb") as dst:
        for i, _, _ in ranges:
            with (parts_dir / f"{i:05d}.part").open("rb") as src:
                shutil.copyfileobj(src, dst, 1 << 24)
    if tmp.stat().st_size != size or sha256_of(tmp) != sha:
        tmp.unlink()
        shutil.rmtree(parts_dir)
        raise SystemExit(f"{out} failed size or SHA 256 verification; parts removed, rerun to download again")
    tmp.replace(out)
    marker.touch()
    shutil.rmtree(parts_dir)
    print(f"  {out.name}: verified SHA 256 {sha}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=Path("data/external/models"))
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    for m in MODELS:
        root = args.dest / m["folder"]
        print(f"{m['repo']}@{m['revision'][:7]}", flush=True)
        for f in m["small"]:
            fetch_small(hub_url(m["repo"], m["revision"], f), root / f)
        path, size, sha = m["weights"]
        fetch_weights(hub_url(m["repo"], m["revision"], path), root / path, size, sha, args.workers)
    print("all model files downloaded and verified", flush=True)


if __name__ == "__main__":
    main()
