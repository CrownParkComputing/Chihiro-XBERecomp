#!/usr/bin/env python3
"""Build MaximumTune1's experimental CPU-only harness from the pinned Xbox SDK."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SUITE_COMMIT = "9f957d6584a3e8f81d7410bcbd79ed342e52cc51"
VARIANTS = {
    "arcade": {
        "xbe": "assets/V307.xbe", "config": "config/game.toml", "layout": "config/xdk-profile.toml",
        "generated": "generated/game", "out": "out/harness",
        "sha256": "2d74371e5a0bb83a6b5185350792f7e3a4242076b62306fab103936ddd2dd760",
    },
}


def run(args, cwd=ROOT, **kwargs):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, check=True, **kwargs)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=VARIANTS, default="arcade")
    parser.add_argument("--recompiler", type=Path, help="existing xbe_recomp built from that suite")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    try:
        variant = VARIANTS[args.variant]
        xbe = ROOT / variant["xbe"]
        with xbe.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != variant["sha256"]:
                raise ValueError(f"XBE differs from the executable used by the {args.variant} config")
        recompiler = (args.recompiler or ROOT / "out/native/xbe_recomp").resolve()
        if not recompiler.is_file():
            raise ValueError("Build the local recompiler first, or pass --recompiler")
        inputs = [ROOT / variant["config"], ROOT / variant["layout"], xbe, recompiler]
        generated = ROOT / variant["generated"] / "image_symbols.h"
        mapping = ROOT / variant["generated"] / "x86_func_mapping.cpp"
        fingerprint = hashlib.sha256()
        for path in inputs:
            with path.open("rb") as source:
                fingerprint.update(hashlib.file_digest(source, "sha256").digest())
        stamp = ROOT / f".local/codegen-inputs-{args.variant}.sha256"
        current = fingerprint.hexdigest()
        if not generated.exists() or not mapping.exists() or not stamp.exists() or stamp.read_text().strip() != current:
            run([recompiler, variant["config"]])
            stamp.write_text(current + "\n")
        if not args.generate_only:
            environment = os.environ.copy()
            environment["JOBS"] = str(max(1, args.jobs))
            run(["bash", "sdk/harness/build.sh", "-r", ROOT, "-g", ROOT / variant["generated"],
                 "-o", ROOT / variant["out"], "-n", "MaximumTune1", "-x",
                 "/gpu/vk_|/gpu/vulkan|/audio/sdl_audio.cpp|/core/keyboard_pad.cpp"], env=environment)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Headless build stopped: {error}\n")


if __name__ == "__main__":
    main()
