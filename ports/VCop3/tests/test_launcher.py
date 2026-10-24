import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vcop3-launcher-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        (self.root / "out/native").mkdir(parents=True)
        shutil.copyfile(ROOT / "tools/run_game.py", self.root / "tools/run_game.py")
        self.game = self.root / "out/native/VCop3"
        self.game.write_text("#!/usr/bin/env python3\nimport os\nfrom pathlib import Path\nPath('mode.txt').write_text(os.environ['VCOP3_CONTROLS'])\n")
        self.game.chmod(0o755)
        self.env = os.environ.copy()
        self.env.pop("VCOP3_CONTROLS", None)
        self.env.pop("DISPLAY", None)
        self.env.pop("WAYLAND_DISPLAY", None)

    def run_game(self, *args):
        return subprocess.run([sys.executable, str(self.root / "tools/run_game.py"), *args],
                              cwd=self.root, env=self.env, capture_output=True, text=True, timeout=10)

    def test_saved_mode_and_explicit_override(self):
        self.assertEqual(self.run_game("--controls", "controllers").returncode, 0)
        self.assertEqual((self.root / "mode.txt").read_text(), "controllers")
        self.assertEqual(self.run_game("--no-menu").returncode, 0)
        self.assertEqual((self.root / "mode.txt").read_text(), "controllers")
        self.env["VCOP3_CONTROLS"] = "mouse-controller"
        self.assertEqual(self.run_game("--controls", "controllers").returncode, 0)
        self.assertEqual((self.root / "mode.txt").read_text(), "controllers")
        self.assertEqual(self.run_game("--no-menu").returncode, 0)
        self.assertEqual((self.root / "mode.txt").read_text(), "mouse-controller")

    def test_invalid_environment_and_duration_do_not_launch(self):
        self.env["VCOP3_CONTROLS"] = "invalid"
        self.assertNotEqual(self.run_game("--no-menu").returncode, 0)
        self.env.pop("VCOP3_CONTROLS")
        for duration in ("0", "-1", "nan", "inf"):
            self.assertNotEqual(self.run_game("--seconds", duration).returncode, 0)
        self.assertFalse((self.root / "mode.txt").exists())

    def test_corrupt_preferences_use_default(self):
        (self.root / ".local").mkdir()
        (self.root / ".local/launcher.json").write_text('[]')
        self.assertEqual(self.run_game("--no-menu").returncode, 0)
        self.assertEqual((self.root / "mode.txt").read_text(), "mouse-controller")

    def test_cancel_keeps_preferences_and_does_not_start_game(self):
        (self.root / ".local").mkdir()
        prefs = self.root / ".local/launcher.json"
        prefs.write_text(json.dumps({"controls": "controllers"}))
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        zenity = bin_dir / "zenity"
        zenity.write_text("#!/bin/sh\nexit 1\n")
        zenity.chmod(0o755)
        self.env["PATH"] = str(bin_dir) + os.pathsep + self.env["PATH"]
        self.assertEqual(self.run_game("--menu").returncode, 0)
        self.assertEqual(json.loads(prefs.read_text()), {"controls": "controllers"})
        self.assertFalse((self.root / "mode.txt").exists())

    def test_bounded_launch_stops_the_child(self):
        self.game.write_text("#!/usr/bin/env python3\nimport os, time\nfrom pathlib import Path\nPath('pid.txt').write_text(str(os.getpid()))\ntime.sleep(30)\n")
        self.assertEqual(self.run_game("--seconds", "0.3").returncode, 0)
        pid = int((self.root / "pid.txt").read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)


if __name__ == "__main__":
    unittest.main()
