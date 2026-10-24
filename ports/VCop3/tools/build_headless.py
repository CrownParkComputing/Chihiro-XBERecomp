#!/usr/bin/env python3
"""Build VC3 CPU diagnostics with the included Chihiro SDK."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
from build_support import ROOT, VARIANTS, verify_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=VARIANTS, default="chihiro")
    parser.add_argument("--recompiler", type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    try:
        xbe = verify_image(args.variant)
        variant = VARIANTS[args.variant]
        recompiler = (args.recompiler or ROOT / "out/native/xbe_recomp").resolve()
        if not recompiler.is_file():
            raise ValueError("Build the local tools first: python3 tools/build_native.py --tools-only")
        fingerprint = hashlib.sha256()
        for path in [ROOT / variant["config"], ROOT / variant["layout"], xbe, recompiler]:
            with path.open("rb") as source:
                fingerprint.update(hashlib.file_digest(source, "sha256").digest())
        stamp = ROOT / f".local/codegen-inputs-{args.variant}.sha256"
        current = fingerprint.hexdigest()
        generated = ROOT / variant["generated"]
        if (not (generated / "image_symbols.h").exists() or not (generated / "x86_func_mapping.cpp").exists()
                or not stamp.exists() or stamp.read_text().strip() != current):
            subprocess.run([str(recompiler), variant["config"], "--xdk", str(ROOT / "sdk/xdk")], cwd=ROOT, check=True)
            stamp.parent.mkdir(parents=True, exist_ok=True)
            stamp.write_text(current + "\n")
        if not args.generate_only:
            environment = os.environ.copy()
            environment["JOBS"] = str(args.jobs)
            subprocess.run(["bash", "sdk/harness/build.sh", "-r", str(ROOT), "-g", str(generated),
                            "-o", str(ROOT / variant["out"]), "-n", "VCop3", "-x",
                            "/gpu/vk_|/gpu/vulkan|/audio/sdl_audio.cpp|/core/keyboard_pad.cpp"],
                           cwd=ROOT, env=environment, check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Headless build stopped: {error}\n")


if __name__ == "__main__":
    main()
