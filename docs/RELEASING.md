# Release process

Build each title from its directory and run `python3 tools/package_linux.py`. The Linux packager snapshots the current source, excludes game data and signing keys, records per-file source hashes, and bundles the local executable. Keep the existing Android signing keys outside Git to preserve compatible updates. The Android build writes its APK under `android/build/`.

Create a preview release when compatibility is incomplete. Upload each game's Linux archive and APK, screenshots, `release-manifest.json`, and `SHA256SUMS`. Generate SHA-256 from the exact uploaded bytes. Keep known failures near the download links and use real game captures with platform/validation labels.

Run `python3 tools/check_sources.py` for checks that do not require game files. Renderer regression tests live in each SDK and require a suitable Vulkan test build.
