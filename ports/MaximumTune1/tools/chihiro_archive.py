"""Import an extracted Chihiro .7z archive into a managed local game folder."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile

SOURCE_URL = "https://archive.org/download/extracted-sega-chihiro-roms"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def archive_entries(archive):
    if archive.suffix.lower() != ".7z":
        raise ValueError("Select the extracted Chihiro .7z archive")
    with archive.open("rb") as stream:
        if stream.read(6) != b"7z\xbc\xaf'\x1c":
            raise ValueError("The selected file is not a 7-Zip archive")
    if not shutil.which("7z"):
        raise ValueError("7-Zip is required; install the 7z command before importing")
    listing = subprocess.check_output(["7z", "l", "-slt", str(archive)], text=True)
    if "----------\n" not in listing:
        raise ValueError("Could not read the archive contents")
    entries, names = [], set()
    for block in listing.split("----------\n", 1)[1].split("\n\n"):
        row = dict(line.split(" = ", 1) for line in block.splitlines() if " = " in line)
        name = row.get("Path")
        if name is None:
            continue
        path = PurePosixPath(name)
        if (not path.parts or path.is_absolute() or ".." in path.parts or
                "\\" in name or ":" in name or any("Link" in key for key in row)):
            raise ValueError("Unsafe archive entry")
        if str(path).casefold() in names:
            raise ValueError("Duplicate archive entry")
        names.add(str(path).casefold())
        if row.get("Encrypted") == "+":
            raise ValueError("Encrypted archives are not supported")
        entries.append(row)
    if not entries:
        raise ValueError("The archive is empty")
    return entries


def import_archive(archive, root, profile):
    archive, root = Path(archive).resolve(), Path(root).resolve()
    entries = archive_entries(archive)
    executable = profile["executable"]
    candidates = [PurePosixPath(e["Path"]) for e in entries
                  if PurePosixPath(e["Path"]).name.casefold() == executable.casefold()]
    if len(candidates) != 1:
        raise ValueError(f"Expected one {executable} in the archive")
    local = root / ".local"
    local.mkdir(parents=True, exist_ok=True)
    output = local / "game-files"
    assets = root / "assets"
    if output.is_symlink():
        raise ValueError("The managed game directory must not be a symlink")
    if assets.is_symlink() and assets.resolve() != output:
        raise ValueError("assets points outside the managed game directory")
    with tempfile.TemporaryDirectory(prefix="import-", dir=local) as temporary:
        stage = Path(temporary)
        tree = stage / "tree"
        tree.mkdir()
        subprocess.run(["7z", "x", "-y", "-bso0", "-bsp0", "-o" + str(tree), str(archive)], check=True)
        image = tree.joinpath(*candidates[0].parts)
        if not image.is_file() or image.is_symlink() or digest(image) != profile["sha256"]:
            raise ValueError(f"{executable} does not match the supported {profile['title']} revision")
        game = tree if profile.get("archive_root", False) else image.parent
        boot_image = game / executable
        if image != boot_image:
            shutil.copy2(image, boot_image)
        files = []
        for path in sorted(game.rglob("*")):
            if path.is_symlink():
                raise ValueError("Extracted links are not supported")
            if path.is_file():
                files.append({"path": path.relative_to(game).as_posix(), "size": path.stat().st_size,
                              "sha256": digest(path)})
        for folder in profile.get("required_paths", ["media"]):
            if not any(e["path"].casefold().startswith(folder.casefold() + "/") for e in files):
                raise ValueError(f"The archive is missing its {folder} folder")
        report = {"archive": str(archive), "archive_sha256": digest(archive), "source_url": SOURCE_URL,
                  "title": profile["title"], "executable": executable, "files": files}
        previous = stage / "previous"
        if output.exists():
            os.replace(output, previous)
        try:
            os.replace(game, output)
        except BaseException:
            if previous.exists():
                os.replace(previous, output)
            raise
        if assets.exists() and not assets.is_symlink():
            # The archive is fully checked before retiring the old extraction.
            os.replace(assets, stage / "previous-assets")
        if not assets.is_symlink():
            assets.symlink_to(".local/game-files", target_is_directory=True)
        (local / "imported.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Imported {profile['title']}: {len(files)} verified files from {archive.name}", flush=True)
    return report
