#!/usr/bin/env python3
"""Import the matching extracted Chihiro .7z archive."""
import argparse
import json
from pathlib import Path
from chihiro_archive import import_archive

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    try:
        import_archive(args.archive, ROOT, json.loads((ROOT / "config/media.json").read_text()))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Import stopped: {error}\n")
