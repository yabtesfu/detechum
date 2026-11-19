import hashlib
import tempfile
import unittest
from pathlib import Path

from detechum.models import GPTTRACE, MODELS, ModelVerificationError, PinnedFile, PinnedModel, verify_model

CONTENT = {"weights.bin": b"weights " * 100, "code.py": b"x = 1\n", "sub/config.json": b"{}"}


def pinned(path: str) -> PinnedFile:
    data = CONTENT[path]
    return PinnedFile(path, len(data), hashlib.sha256(data).hexdigest())


MODEL = PinnedModel(repo="example/model", revision="0123456789abcdef", folder="example",
                    weights=pinned("weights.bin"), other_files=(pinned("code.py"), pinned("sub/config.json")))


class VerifyModelTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.folder = self.root / MODEL.folder
        for path, data in CONTENT.items():
            (self.folder / path).parent.mkdir(parents=True, exist_ok=True)
            (self.folder / path).write_bytes(data)

    def assert_rejected(self, fragment: str):
        with self.assertRaises(ModelVerificationError) as raised:
            verify_model(MODEL, self.root)
        self.assertIn(fragment, str(raised.exception))

    def test_intact_folder_is_returned(self):
        self.assertEqual(verify_model(MODEL, self.root), self.folder)

    def test_missing_folder_is_rejected(self):
        with self.assertRaises(ModelVerificationError) as raised:
            verify_model(MODEL, self.root / "elsewhere")
        self.assertIn("not found", str(raised.exception))

    def test_missing_file_is_rejected(self):
        (self.folder / "code.py").unlink()
        self.assert_rejected("code.py is missing")

    def test_incomplete_file_is_rejected_by_size(self):
        (self.folder / "weights.bin").write_bytes(CONTENT["weights.bin"][:-1])
        self.assert_rejected("expected 800")

    def test_altered_file_of_the_same_size_is_rejected(self):
        (self.folder / "code.py").write_bytes(b"x = 2\n")
        self.assert_rejected("code.py does not match the SHA 256")

    def test_file_outside_the_pinned_revision_is_rejected(self):
        (self.folder / "sub" / "added_tokens.json").write_bytes(b"{}")
        self.assert_rejected("sub/added_tokens.json, which is not a file of example/model")

    def test_download_markers_finder_metadata_and_bytecode_caches_are_ignored(self):
        (self.folder / "weights.bin.done").touch()
        (self.folder / ".DS_Store").write_bytes(b"\x00")
        (self.folder / "__pycache__").mkdir()
        (self.folder / "__pycache__" / "code.cpython-314.pyc").write_bytes(b"\x00")
        self.assertEqual(verify_model(MODEL, self.root), self.folder)


class PinnedModelsTest(unittest.TestCase):
    def test_every_pinned_file_has_a_well_formed_entry(self):
        for model in MODELS.values():
            paths = [f.path for f in model.files]
            self.assertEqual(len(paths), len(set(paths)), model.repo)
            self.assertRegex(model.revision, r"^[0-9a-f]{40}$")
            for f in model.files:
                self.assertRegex(f.sha256, r"^[0-9a-f]{64}$", f.path)
                self.assertGreater(f.size, 0, f.path)
                self.assertFalse(Path(f.path).is_absolute() or ".." in Path(f.path).parts, f.path)

    def test_the_code_file_that_the_gpttrace_scorer_executes_is_pinned(self):
        self.assertIn("normalize.py", [f.path for f in GPTTRACE.files])

    def test_record_identifies_repo_revision_and_weights(self):
        self.assertEqual(GPTTRACE.record(), {"repo": GPTTRACE.repo, "revision": GPTTRACE.revision,
                                             "weights_sha256": GPTTRACE.weights.sha256})


if __name__ == "__main__":
    unittest.main()
