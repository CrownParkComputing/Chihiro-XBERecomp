# Source provenance

The included SDK is exported from `CrownParkComputing/xbox-recomp-suite` at commit `9f957d6584a3e8f81d7410bcbd79ed342e52cc51`, with the six Chihiro patches listed in `UPSTREAM.json`. SDK templates, its sync tool, and a redundant cookbook copy are omitted. File checksums are recorded in `UPSTREAM.json`.

The Android SDL Java bridge and glslang/document-tree adapters are adapted from the same suite's existing Android support. The new import launcher accepts the supported `.7z` revision and installs it in app-private storage. Dependency coordinates, checksums and license notices live in `android/dependencies/java.json` and `android/licenses/`.

Retain the root and SDK licenses and `sdk/THIRD_PARTY.txt`. No proprietary game files or private signing keys are tracked.
