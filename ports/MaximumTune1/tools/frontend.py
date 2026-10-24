#!/usr/bin/env python3
"""Desktop import, setup and launch menu for an extracted Chihiro .7z port."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from chihiro_archive import SOURCE_URL, digest, import_archive

ROOT = Path(__file__).resolve().parents[1]


def profile():
    return json.loads((ROOT / "config/media.json").read_text())


def media_ready(info):
    image = ROOT / "assets" / info["executable"]
    try:
        return image.is_file() and digest(image) == info["sha256"]
    except OSError:
        return False


def ready(info):
    stamp = ROOT / ".local/setup-image.sha256"
    return (media_ready(info) and (ROOT / info["binary"]).is_file() and
            stamp.is_file() and stamp.read_text().strip() == info["sha256"])


def dialog(*args):
    result = subprocess.run(["zenity", *args], capture_output=True, text=True)
    if result.returncode == 1:
        return None
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Could not open the desktop menu")
    return result.stdout.strip()


def stop(child):
    if child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def work(command, title):
    """Keep setup output in a local log and let Cancel stop its whole process group."""
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    progress = None
    with (local / "setup.log").open("a") as log:
        log.write(f"\n{title}\n")
        log.flush()
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            if shutil.which("zenity") and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
                progress = subprocess.Popen(["zenity", "--progress", "--pulsate", "--auto-close",
                                             f"--title={title}", "--text=Please wait. You can cancel this operation.",
                                             "--width=560"], stdin=subprocess.PIPE, text=True)
            while child.poll() is None:
                if progress is not None and progress.poll() is not None:
                    return False
                time.sleep(0.1)
            if child.returncode:
                tail = (local / "setup.log").read_text(errors="replace")[-1600:]
                raise ValueError(f"{title} stopped. Details are in {local / 'setup.log'}\n\n{tail}")
            return True
        finally:
            stop(child)
            if progress is not None:
                if progress.poll() is None:
                    try:
                        progress.stdin.write("100\n")
                        progress.stdin.flush()
                    except BrokenPipeError:
                        pass
                    progress.terminate()
                progress.wait()


def setup(info):
    if not media_ready(info):
        raise ValueError(f"Import the matching {info['archive']} before setup")
    missing = [name for name in ("clang", "clang++", "cmake", "ninja") if not shutil.which(name)]
    if missing:
        raise ValueError("Install these required build tools, then run setup again: " + ", ".join(missing))
    if work([sys.executable, *info["build"]], f"Preparing {info['title']}"):
        if not (ROOT / info["binary"]).is_file():
            raise ValueError("Setup finished without a game executable; see .local/setup.log")
        (ROOT / ".local/setup-image.sha256").write_text(info["sha256"] + "\n")
        return True
    return False


def import_dialog(info):
    selected = dialog("--file-selection", f"--title=Import {info['title']} · Chihiro .7z",
                      "--file-filter=Chihiro game archives | *.7z",
                      "--filename=" + str(Path.home() / "Downloads" / info["archive"]))
    if selected is None:
        return False
    return work([sys.executable, str(Path(__file__).resolve()), "--import", selected, "--no-build"],
                f"Importing {info['title']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--import", dest="archive", type=Path, help="Import the matching extracted Chihiro .7z")
    parser.add_argument("--no-build", action="store_true", help="Import only; prepare the executable later")
    parser.add_argument("--setup", action="store_true", help="Prepare the imported game")
    args = parser.parse_args(argv)
    info = profile()
    (ROOT / ".local").mkdir(exist_ok=True)
    # A cancellation still unwinds the staged import and removes partial files.
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        if args.archive:
            import_archive(args.archive, ROOT, info)
            return 0 if args.no_build or ready(info) or setup(info) else 1
        if args.setup:
            return 0 if setup(info) else 1
        if not shutil.which("zenity"):
            parser.error("Install zenity for the desktop front end; command-line import and setup remain available")
        with (ROOT / ".local/frontend.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("The game front end is already open")
            while True:
                status = "Ready to play" if ready(info) else "Imported · run setup" if media_ready(info) else "Import a Chihiro .7z to begin"
                choice = dialog("--list", "--radiolist", f"--title={info['title']}",
                                f"--text={status}\n{info['summary']}", "--column=Select", "--column=Action",
                                "--width=680", "--height=410", "--ok-label=Continue", "--cancel-label=Close",
                                "TRUE", "Play", "FALSE", "Import Chihiro .7z", "FALSE", "Setup / rebuild",
                                "FALSE", "Launch options", "FALSE", "Chihiro dump source")
                if choice is None:
                    return 0
                try:
                    if choice == "Chihiro dump source":
                        subprocess.Popen(["xdg-open", SOURCE_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif choice == "Import Chihiro .7z":
                        if import_dialog(info) and not ready(info):
                            setup(info)
                    elif choice == "Setup / rebuild":
                        setup(info)
                    elif choice in ("Play", "Launch options"):
                        if not ready(info) and not setup(info):
                            continue
                        command = info["options"] if choice == "Launch options" else info["launch"]
                        subprocess.run([sys.executable, *command], cwd=ROOT, check=True)
                except (OSError, ValueError, subprocess.CalledProcessError) as error:
                    dialog("--error", f"--title={info['title']}", "--no-markup", f"--text={error}", "--width=680")
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Setup stopped: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
