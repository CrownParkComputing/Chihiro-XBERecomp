"""Paths, executable identities and dependency options for standalone builds."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "chihiro": {
        "xbe": "assets/vc3.xbe", "config": "config/game.toml", "layout": "config/xdk-5028.toml",
        "generated": "generated/game", "out": "out/harness",
        "sha256": "85fcc40d1653609d905906f15beb507057089d2be61eadc36fe369827580a7c8",
    },
}


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify_image(variant="chihiro"):
    info = VARIANTS[variant]
    image = ROOT / info["xbe"]
    if digest(image) != info["sha256"]:
        raise ValueError(f"XBE differs from the executable supported by the {variant} config")
    return image


def dependency_options(args):
    options = []
    if args.dxc_dir:
        directory = args.dxc_dir.resolve()
        if not (directory / "include/dxc/dxcapi.h").is_file():
            raise ValueError("--dxc-dir must contain include/dxc/dxcapi.h")
        options.append(f"-DFETCHCONTENT_SOURCE_DIR_DXC={directory}")
    if args.deps_dir:
        directory = args.deps_dir.resolve()
        if not directory.is_dir():
            raise ValueError("--deps-dir must be an existing dependency cache")
        for name in ("zydis", "tomlplusplus", "imgui", "sdl3", "vma"):
            source = directory / (name + "-src")
            if source.is_dir():
                options.append(f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}={source}")
    return options


def ensure_link(link, target):
    target = target.resolve()
    if link.exists() or link.is_symlink():
        if not link.is_symlink() or link.resolve() != target:
            raise ValueError(f"{link} exists and is not the managed asset link")
    else:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=target.is_dir())
