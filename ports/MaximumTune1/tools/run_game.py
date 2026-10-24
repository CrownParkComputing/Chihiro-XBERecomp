#!/usr/bin/env python3
"""Launch the imported Chihiro game."""
import json
from pathlib import Path
import subprocess
from chihiro_archive import digest
ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    info = json.loads((ROOT / "config/media.json").read_text())
    image = ROOT / "assets" / info["executable"]
    if not image.is_file() or digest(image) != info["sha256"]:
        raise SystemExit("Import the matching Chihiro .7z through run.sh first")
    executable = ROOT / info["binary"]
    if not executable.is_file():
        raise SystemExit("Run setup through run.sh first")
    raise SystemExit(subprocess.call([str(executable)], cwd=ROOT))
