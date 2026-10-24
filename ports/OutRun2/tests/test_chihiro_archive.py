import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location("chihiro_archive", Path(__file__).resolve().parents[1] / "tools/chihiro_archive.py")
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


@unittest.skipUnless(shutil.which("7z"), "Archive import requires 7-Zip")
class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="chihiro-import-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "port"
        self.root.mkdir()
        self.profile = {"title": "Test game", "executable": "game.xbe",
                        "sha256": hashlib.sha256(b"matching image").hexdigest()}

    def packed(self, name, image=b"matching image", media=True, nested=False):
        source = self.base / (name + "-files")
        source.mkdir()
        game = source / "Game" if nested else source
        game.mkdir(exist_ok=True)
        (game / "game.xbe").write_bytes(image)
        if media:
            (game / "media").mkdir()
            (game / "media/example.bin").write_bytes(b"game media")
        result = self.base / (name + ".7z")
        subprocess.run(["7z", "a", "-t7z", "-bso0", str(result), "."], cwd=source, check=True)
        return result

    def previous(self):
        assets = self.root / "assets"
        assets.mkdir()
        (assets / "game.xbe").write_bytes(b"previous image")
        return assets

    def test_nested_archive_replaces_old_extraction_after_verification(self):
        old = self.previous()
        source = self.packed("valid", nested=True)
        report = archive.import_archive(source, self.root, self.profile)
        self.assertTrue(old.is_symlink())
        self.assertEqual((old / "game.xbe").read_bytes(), b"matching image")
        self.assertEqual((old / "media/example.bin").read_bytes(), b"game media")
        self.assertEqual(report["archive_sha256"], archive.digest(source))
        self.assertEqual(len(report["files"]), 2)
        self.assertEqual(json.loads((self.root / ".local/imported.json").read_text()), report)
        self.assertEqual(list((self.root / ".local").glob("import-*")), [])

    def test_wrong_revision_preserves_the_previous_game(self):
        old = self.previous()
        with self.assertRaisesRegex(ValueError, "revision"):
            archive.import_archive(self.packed("wrong", image=b"wrong release"), self.root, self.profile)
        self.assertFalse(old.is_symlink())
        self.assertEqual((old / "game.xbe").read_bytes(), b"previous image")
        self.assertFalse((self.root / ".local/game-files").exists())

    def test_missing_media_preserves_the_previous_game(self):
        old = self.previous()
        with self.assertRaisesRegex(ValueError, "media"):
            archive.import_archive(self.packed("missing", media=False), self.root, self.profile)
        self.assertEqual((old / "game.xbe").read_bytes(), b"previous image")

    def test_existing_managed_game_is_replaced_without_leaving_a_fallback(self):
        archive.import_archive(self.packed("first"), self.root, self.profile)
        archive.import_archive(self.packed("second"), self.root, self.profile)
        self.assertEqual(list((self.root / ".local").glob("previous*")), [])
        self.assertEqual((self.root / "assets/game.xbe").read_bytes(), b"matching image")

    def test_zip_renamed_as_7z_is_rejected(self):
        source = self.base / "renamed.7z"
        with zipfile.ZipFile(source, "w") as packed:
            packed.writestr("game.xbe", b"matching image")
        with self.assertRaisesRegex(ValueError, "not a 7-Zip"):
            archive.import_archive(source, self.root, self.profile)


if __name__ == "__main__":
    unittest.main()
