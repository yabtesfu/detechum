"""Pinned model files and the check that a local copy matches them.

Every file that determines a score is listed with its size and SHA 256: the weights, the tokenizer,
the configuration and, for GPTTrace, the `normalize.py` that the scorer executes.

Where the digests come from. Weights are stored on the hub as LFS objects, and their SHA 256 is the
object id the hub publishes for the pinned revision. The other files are stored in git, for which
the hub publishes a SHA 1 blob id and no SHA 256. Their digests below were computed on 2026-11-19
from copies whose blob ids matched the hub's listing for the pinned revision.

The check detects a wrong revision, an incomplete download, a corrupted file and a replaced or
added file. It gives no protection against someone who can also change this module or the Python
environment.

This module imports nothing outside the standard library, so `eval/fetch_models.py` and the command
line can use it before the model dependencies are loaded.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class PinnedFile:
    path: str      # relative to the model folder, with forward slashes
    size: int      # bytes
    sha256: str


@dataclass(frozen=True)
class PinnedModel:
    repo: str
    revision: str
    folder: str    # folder under the models directory, as written by eval/fetch_models.py
    weights: PinnedFile
    other_files: tuple[PinnedFile, ...]

    @property
    def files(self) -> tuple[PinnedFile, ...]:
        return (self.weights, *self.other_files)

    def record(self) -> dict:
        """The identity of this model as it is written into reports and metrics files."""
        return {"repo": self.repo, "revision": self.revision, "weights_sha256": self.weights.sha256}


GPTTRACE = PinnedModel(
    repo="nakas/gpttrace-v8s-1b", revision="ac748e32ca8c90bb8858fadc427757728e27b063", folder="gpttrace-v8s-1b",
    weights=PinnedFile("model/model.safetensors", 4125087720,
                       "379b154cadb0fd6a226badd2f745705f49c19461ef150ee6b97fec92e82ba538"),
    other_files=(
        PinnedFile("normalize.py", 2583, "25776816397bbb8d308b73463b3155d1d5f9e868f14d459f9da4261ac37fa49f"),
        PinnedFile("model/config.json", 2110, "c7d80853eb9055bc509e2c158e7f572536a423ddacd30a1837d303a036f7746e"),
        PinnedFile("model/tokenizer.json", 3583228,
                   "6c8aaa9a542084f2457eab775d4eeb51f92a70c0fd9de28d5edb0ddec3c08d30"),
        PinnedFile("model/tokenizer_config.json", 379,
                   "5926e6ec4294f80294bd98d9176defa9fbae7f140525d06a1da987488e74a973"),
    ),
)

# The two Qwen revisions ship identical merges.txt, vocab.json and tokenizer.json.
_QWEN_SHARED = (
    PinnedFile("merges.txt", 1671839, "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3"),
    PinnedFile("vocab.json", 2776833, "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
    PinnedFile("tokenizer.json", 7031645, "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"),
)

QWEN_BASE = PinnedModel(
    repo="Qwen/Qwen2.5-1.5B", revision="8faed761d45a263340a0528343f099c05c9a4323", folder="qwen2.5-1.5b",
    weights=PinnedFile("model.safetensors", 3087467144,
                       "a961db72e75d52b18e6b0c9d379e51a26973b233385e0e127fdda7d648aec796"),
    other_files=(
        PinnedFile("config.json", 684, "0e8c8aa86468aba09c9d32157ff4bc2301c7e6c50e4398960425b2ea71e66f77"),
        PinnedFile("generation_config.json", 138,
                   "8c970692323e3ea0e9b8b0a4dca79388d31226e41f83c9fd6014804280ebf6e8"),
        PinnedFile("tokenizer_config.json", 7228,
                   "c91efca15ceff6e9ee9424db58a6f59cd41294e550a86cbd07e3c1fb500b34f9"),
        *_QWEN_SHARED,
    ),
)

QWEN_INSTRUCT = PinnedModel(
    repo="Qwen/Qwen2.5-1.5B-Instruct", revision="989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
    folder="qwen2.5-1.5b-instruct",
    weights=PinnedFile("model.safetensors", 3087467144,
                       "dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee"),
    other_files=(
        PinnedFile("config.json", 660, "98d2ff8cc47488d08a2b0b3acf4eb99ef210779b42bd48605f6b8e36acdbf670"),
        PinnedFile("generation_config.json", 242,
                   "e558847a8b4402616f1273797b015104dc266fe4b520056fca88823ba8f8ebe6"),
        PinnedFile("tokenizer_config.json", 7305,
                   "5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583"),
        *_QWEN_SHARED,
    ),
)

# Download priority order: the primary scorer first.
MODELS = {"gpttrace": GPTTRACE, "qwen_base": QWEN_BASE, "qwen_instruct": QWEN_INSTRUCT}


class ModelVerificationError(Exception):
    """A model folder does not hold exactly the pinned files."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_inert(relative: PurePosixPath) -> bool:
    # Finder metadata, the download markers of eval/fetch_models.py, and bytecode caches, which no
    # loader in this package reads.
    return (relative.name.startswith(".") or relative.suffix == ".done"
            or "__pycache__" in relative.parts)


def verify_model(model: PinnedModel, models_root: Path) -> Path:
    """Return the folder of `model` under `models_root` after checking that it holds the pinned files.

    Every pinned file must be present with the pinned size and SHA 256. Any other file is an error,
    because a tokenizer or configuration file that the pinned revision does not have can change how
    the model loads. Reading the weights takes a few seconds.

    Raises ModelVerificationError naming the first file that fails.
    """
    root = Path(models_root) / model.folder
    if not root.is_dir():
        raise ModelVerificationError(f"model folder {root} not found")
    pinned = {f.path for f in model.files}
    for path in sorted(root.rglob("*")):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if path.is_dir() or _is_inert(relative) or str(relative) in pinned:
            continue
        raise ModelVerificationError(
            f"{root} holds {relative}, which is not a file of {model.repo} at revision {model.revision[:12]}")
    for f in model.files:
        path = root / f.path
        if not path.is_file():
            raise ModelVerificationError(f"{path} is missing")
        # The size is compared first so that an incomplete download fails without reading gigabytes.
        size = path.stat().st_size
        if size != f.size:
            raise ModelVerificationError(f"{path} has {size} bytes, expected {f.size}")
        if sha256_of(path) != f.sha256:
            raise ModelVerificationError(
                f"{path} does not match the SHA 256 pinned for {model.repo} at revision {model.revision[:12]}")
    return root
