"""Download the pinned model files of `detechum.models` into data/external/models.

Weight files are fetched as fixed size byte ranges over several connections. Each range is stored as
its own part file, so an interrupted run loses at most the unfinished ranges and a rerun skips every
completed one. Every file is checked against the SHA 256 pinned in `detechum.models`.

Usage:
    .venv/bin/python eval/fetch_models.py [--dest data/external/models] [--workers 8] [--only desklib]
"""

import argparse
import concurrent.futures
import shutil
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from detechum.models import MODELS, sha256_of

USER_AGENT = "detechum-fetch/0.1"
CHUNK = 32 * 1024 * 1024
READ_TIMEOUT = 30  # seconds without data before a connection is abandoned and retried
MAX_ATTEMPTS = 200

def hub_url(repo: str, revision: str, path: str) -> str:
    return f"https://huggingface.co/{repo}/resolve/{revision}/{path}"


def resolve(url: str) -> str:
    # The hub answers with a redirect to a signed CDN URL that expires, so it is resolved again on every attempt.
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r:
        return r.url


def fetch_small(url: str, out: Path, sha: str) -> None:
    if out.exists() and sha256_of(out) == sha:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r:
                out.write_bytes(r.read())
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f"  retry {attempt} for {out.name}: {e}", flush=True)
            time.sleep(min(30, 2 * attempt))
    else:
        raise SystemExit(f"could not download {url}")
    if sha256_of(out) != sha:
        out.unlink()
        raise SystemExit(f"{out} failed SHA 256 verification and was removed; rerun to download again")


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
    ap.add_argument("--only", choices=MODELS, help="fetch this model only")
    args = ap.parse_args()
    for m in [MODELS[args.only]] if args.only else MODELS.values():
        root = args.dest / m.folder
        print(f"{m.repo}@{m.revision[:7]}", flush=True)
        for f in m.other_files:
            fetch_small(hub_url(m.repo, m.revision, f.path), root / f.path, f.sha256)
        w = m.weights
        fetch_weights(hub_url(m.repo, m.revision, w.path), root / w.path, w.size, w.sha256, args.workers)
    print("all model files downloaded and verified", flush=True)


if __name__ == "__main__":
    main()
