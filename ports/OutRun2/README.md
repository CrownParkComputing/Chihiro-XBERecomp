# OutRun 2 — standalone Chihiro port

Native Linux x86-64 and Android ARM64 builds from the original Chihiro executable, using an included XBE recompilation SDK. This is an experimental port.

[Download Linux and Android builds](https://github.com/CrownParkComputing/Chihiro-XBERecomp/releases/tag/v0.1.0-preview.1). Game files are imported locally and are not included in the repository or release downloads.

## Download and play

- **Linux:** extract `OutRun2-Linux-x86_64.tar.gz`, open `Start.sh`, choose **Import Chihiro .7z**, select `Outrun 2.7z`, then choose **Play**. The prebuilt package needs Python 3.11+, Zenity, 7-Zip (`7z`), and a Vulkan-capable graphics driver. SDL and the C++ runtime are bundled. See `release.json` for the build's minimum glibc version. Use a writable folder so settings, imports and saves can be stored there.
- **Android:** install `OutRun2-Android-arm64.apk` on Android 13+ (ARM64, Vulkan 1.1+). Open it, select **Import Chihiro .7z**, choose the same archive, wait for verification, then tap **Start game**. Import needs room for the archive and extracted data. The APK has been cross-compiled and its signature/alignment checked; on-device gameplay validation is pending.

The launcher remembers imported files and keeps a previous working import if extraction or executable verification fails. Keep your original `.7z` archive as the source.

## Source archive

Use **`Outrun 2.7z`** from the [user-selected Chihiro archive source](https://archive.org/download/extracted-sega-chihiro-roms). These archives contain extracted Chihiro game files; the source link is also available in both launchers.

The importer accepts genuine `.7z` archives only and verifies `outrun2.xbe` against SHA-256 `d98a7efc0ee4ba48b6e938743fa309a9fc774c05713ef735e67d1b17b9bbbd1b`. Older ZIP/ISO/GDI import paths and automatic fallback to other revisions have been removed.

## Controls and players

Keyboard/controller driving uses the in-game settings (F10 / R3). Default keyboard: arrow keys steer, W accelerates, Q brakes, Enter starts and Backspace inserts a coin. Android includes touch driving buttons and controller support.

## Build from source

The SDK is included. You do not need a multi-game suite checkout. Dependencies are fetched at pinned revisions; an optional local cache can be supplied to the native build tools.

```sh
python3 tools/prepare_game.py "$HOME/Downloads/Outrun 2.7z"
python3 tools/build_native.py --jobs 3
./run.sh
```

`./run.sh --frontend` explicitly opens import/setup. For command-line import only:

```sh
python3 tools/frontend.py --import "$HOME/Downloads/Outrun 2.7z" --no-build
```

Native builds need Clang, CMake, Ninja, Python 3.11+, Vulkan headers/loader, and SDL3 development files (or the SDK's pinned dependency build).

After native code generation, build Android with Android SDK 35/build-tools 36.0.0, NDK 28.2.13676358 and JDK 17:

```sh
python3 tools/build_android.py --jobs 3
```

The Android builder fetches pinned SDL/glslang/SPIRV dependencies and checksum-pinned Java 7z libraries. It packages no game data. A persistent signing key is created under ignored `.local/keys/`; keep it to sign compatible updates. The optional `--deps-source` and `--deps-build` arguments reuse compatible dependency caches.

To create a Linux archive from the current source tree and local native build:

```sh
python3 tools/package_linux.py
```

## Validation and provenance

Run the importer/launcher checks with `python3 -m unittest discover -s tests -v`. Native GPU/input checks run through `ctest --preset linux-release` after building their targets. See [UPSTREAM.md](UPSTREAM.md) for the included SDK revision, patches and licenses.
