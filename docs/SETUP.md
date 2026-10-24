# Installation and supported files

Download one Linux package or APK per game from the preview release. The source ZIP from GitHub does not contain the ready-built applications. Keep your original archive; the importer checks the executable hash and required directories before replacing an existing import.

| Game | Supported archive | Verified executable SHA-256 |
| --- | --- | --- |
| The House of the Dead III | `House of The Dead 3.7z` | `89a0e7778002205c114a91bc1797291344b2afeea8b5c7d5085cce7e47dc71de` |
| OutRun 2 | `Outrun 2.7z` | `d98a7efc0ee4ba48b6e938743fa309a9fc774c05713ef735e67d1b17b9bbbd1b` |
| Virtua Cop 3 | `Virtua Cop 3.7z` | `85fcc40d1653609d905906f15beb507057089d2be61eadc36fe369827580a7c8` |
| Wangan Midnight Maximum Tune | `Maximum Tune 1 (Export).7z` | `2d74371e5a0bb83a6b5185350792f7e3a4242076b62306fab103936ddd2dd760` |
| Wangan Midnight Maximum Tune 2 | `Maximum Tune 2 (Export).7z` | `ee1e11529eb053f3a1416f3dead7aa64ab6d859a5143be700883596ca9d56d96` |
| Ghost Squad | `Ghost Squad.7z` | `e2f1b3d43eca6661880d81618519ff44f77a8cdafff825177041c8f0d699038e` |

Maximum Tune preserves the archive's `A/` and `Data/` layout; use the original full archive. The Linux importer and Android importer accept case variants of required folders. Unsupported executable revisions are rejected.

## Linux

Use a writable folder on x86-64 Linux with x86-64-v2 CPU support, Python 3.11+, Zenity, 7-Zip, and a Vulkan-capable graphics driver. Run `./Start.sh`, select Import, then Play. The package's `release.json` records minimum glibc; the GPU driver and Vulkan loader remain system dependencies. For command-line import, use `python3 tools/frontend.py --import '/path/to/archive.7z' --no-build`.

## Android and Retroid

Android 13+, ARM64, and Vulkan 1.1 are required. Install the APK, open its launcher, choose the matching `.7z`, and wait for verification. Leave room internally for both the temporary archive copy and extracted data. Reinstalling a compatible signed APK over the existing app preserves game files and saves; uninstalling removes app data.

## Controls

Back/Select or Backspace inserts a coin; Start or Enter starts. F10/R3 opens host settings. Gun games provide aiming/fire/reload controls; Ghost Squad's full input behavior still needs validation. HOTD3 uses mouse left/fire and right/reload. Virtua Cop 3 has a shared screen for local co-op and launcher selection for mouse/touch plus a second controller, or two controllers. Driving controls and mappings are adjustable in host settings. Maximum Tune remains unavailable for racing until the display problem is fixed.
