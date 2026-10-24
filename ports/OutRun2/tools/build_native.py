#!/usr/bin/env python3
"""Build OutRun2 with the pinned SDL3/Vulkan Xbox runtime."""
import argparse
import hashlib
from pathlib import Path
import subprocess
from build_headless import ROOT, VARIANTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    try:
        xbe = ROOT / VARIANTS["arcade"]["xbe"]
        with xbe.open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != VARIANTS["arcade"]["sha256"]:
                raise ValueError("The executable does not match this OutRun2 config")
        output = ROOT / "out/native"
        output.mkdir(parents=True, exist_ok=True)
        media = output / "assets"
        assets = ROOT / "assets"
        if media.exists() or media.is_symlink():
            if not media.is_symlink() or media.resolve() != assets.resolve():
                raise ValueError("The native build's assets link points elsewhere")
        else:
            media.symlink_to(assets, target_is_directory=True)
        command = ["cmake", "-S", str(ROOT), "-B", str(output), "-G", "Ninja",
                   "-DCMAKE_C_COMPILER=clang", "-DCMAKE_CXX_COMPILER=clang++",
                   "-DCMAKE_BUILD_TYPE=RelWithDebInfo", "-DCMAKE_CXX_FLAGS=-march=x86-64-v2"]
        subprocess.run(command, cwd=ROOT, check=True)
        subprocess.run(["cmake", "--build", str(output), "--target", "recompile_OutRun2" if args.generate_only else "OutRun2", "--parallel", str(max(1, args.jobs))],
                       cwd=ROOT, check=True)
        print(f"Native executable: {output / 'OutRun2'}")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Native build stopped: {error}\n")


if __name__ == "__main__":
    main()
