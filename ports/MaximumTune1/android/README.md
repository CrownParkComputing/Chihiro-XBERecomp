# Android ARM64 build

Run `python3 tools/build_android.py --jobs 3` from the repository root after importing the supported `.7z` and generating the native code. Requires Android SDK 35, build-tools 36.0.0, NDK 28.2.13676358 and JDK 17. Output is under `android/build/`.

This standalone package uses the common SDL3 Android bridge and a glslang HLSL-to-SPIR-V adapter. The launcher copies the chosen 7z into temporary app storage, validates paths and the exact XBE SHA-256, then atomically installs extracted files. The original archive remains at its chosen location. A failed extraction or wrong revision keeps the previous install.

The native libraries target Android 13+ / ARM64, and are aligned for 16 KiB pages. Game data is never packaged in the APK. Local signing keys and generated output are ignored by Git.
