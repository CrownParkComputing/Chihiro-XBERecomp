#!/usr/bin/env python3
"""Launch Virtua Cop 3 with mouse/controller or two-controller local play."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHOICES = ("mouse-controller", "controllers")


def preferences():
    try:
        saved = json.loads((ROOT / ".local/launcher.json").read_text())
        if isinstance(saved, dict) and saved.get("controls") in CHOICES:
            return saved["controls"]
    except (OSError, ValueError):
        pass
    return "mouse-controller"


def choose_options(controls):
    if not shutil.which("zenity"):
        raise ValueError("Install zenity for launch options, or use --controls mouse-controller|controllers")
    rows = []
    for value, label in zip(CHOICES, ("Player 1 mouse + Player 2 controller", "Two controllers")):
        rows += [str(value == controls).upper(), value, label]
    result = subprocess.run([
        "zenity", "--list", "--radiolist", "--title=Virtua Cop 3 - Launch options",
        "--text=English · 1 or 2 players on one shared screen\nChoose the controls. Press each player's Start button to join.",
        "--column=Select", "--column=Mode", "--column=Controls", "--hide-column=2", "--print-column=2",
        "--width=640", "--height=280", "--ok-label=Start game", "--cancel-label=Cancel", *rows,
    ], capture_output=True, text=True)
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise ValueError(f"Could not open launch options: {result.stderr.strip()}")
    if result.stdout.strip() not in CHOICES:
        raise ValueError("Choose the controls before starting")
    return result.stdout.strip()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", choices=CHOICES, help="Saved choice, initially mouse-controller")
    parser.add_argument("--seconds", type=float, help="Stop after this many seconds (diagnostics)")
    menu = parser.add_mutually_exclusive_group()
    menu.add_argument("--menu", "--options", action="store_true", help="Show launch options")
    menu.add_argument("--no-menu", action="store_true", help="Start with the saved setup")
    args = parser.parse_args(argv)
    if args.seconds is not None and (not math.isfinite(args.seconds) or args.seconds <= 0):
        parser.error("--seconds must be positive and finite")
    controls = args.controls or os.environ.get("VCOP3_CONTROLS") or preferences()
    if controls not in CHOICES:
        parser.error("VCOP3_CONTROLS must be mouse-controller or controllers")
    executable = ROOT / "out/native/VCop3"
    if not executable.is_file():
        parser.error("Build VCop3 first: python3 tools/build_native.py --tests")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    try:
        with (local / "launcher.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("Virtua Cop 3 is already running through this launcher")
            desktop = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
            if args.menu or (not argv and desktop and shutil.which("zenity")):
                controls = choose_options(controls)
                if controls is None:
                    return 0
            (local / "launcher.json").write_text(json.dumps({"controls": controls}, indent=2) + "\n")
            environment = os.environ.copy()
            environment["VCOP3_CONTROLS"] = controls
            child = subprocess.Popen([str(executable)], cwd=ROOT, env=environment)
            try:
                try:
                    return child.wait(timeout=args.seconds)
                except (subprocess.TimeoutExpired, KeyboardInterrupt):
                    return 0
            finally:
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
    except (OSError, ValueError) as error:
        parser.exit(1, f"Launch stopped: {error}\n")


if __name__ == "__main__":
    sys.exit(main())
