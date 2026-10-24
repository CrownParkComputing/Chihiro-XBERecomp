#!/usr/bin/env python3
"""Build the standalone Virtua Cop 3 Linux SDL/Vulkan application."""
import argparse
from pathlib import Path
import subprocess
from build_support import ROOT, dependency_options, ensure_link, verify_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--tools-only", action="store_true")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("--renderer-tests", action="store_true")
    parser.add_argument("--deps-dir", type=Path, help="Optional dependency source cache")
    parser.add_argument("--dxc-dir", type=Path, help="Optional extracted Linux DXC distribution")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.tools_only and args.generate_only:
        parser.error("--tools-only and --generate-only are mutually exclusive")
    if (args.tests or args.renderer_tests) and (args.tools_only or args.generate_only):
        parser.error("--tests and --renderer-tests require a full native build")
    try:
        options = dependency_options(args)
        if not args.tools_only:
            image = verify_image()
            ensure_link(ROOT / "out/native/assets", image.parent)
        options.append(f"-DVCOP3_RENDERER_TESTS={'ON' if args.renderer_tests else 'OFF'}")
        subprocess.run(["cmake", "--preset", "linux-release", *options], cwd=ROOT, check=True)
        targets = ["xbe_recomp", "xbe_symbols", "iso_extract"] if args.tools_only else [
            "recompile_VCop3" if args.generate_only else "VCop3"]
        if args.tests:
            targets += ["VCop3MouseTests", "VCop3MouseSDLTests", "VCop3PlayersTests"]
        if args.renderer_tests:
            targets.append("VCop3RuntimeTests")
        subprocess.run(["cmake", "--build", "--preset", "linux-release", "--target", *targets,
                        "--parallel", str(args.jobs)], cwd=ROOT, check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Native build stopped: {error}\n")


if __name__ == "__main__":
    main()
