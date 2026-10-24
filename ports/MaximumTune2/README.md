# Wangan Midnight Maximum Tune 2 — experimental standalone port

Linux passes media-board and controller discovery and reaches menu drawing without the former reset crash. The display is still black. Racing, graphics, sound and gameplay are not ready. Android archive import has been verified on the Retroid.

Import your matching `Maximum Tune 2 (Export).7z` with `python3 tools/prepare_game.py <archive>`. Build Linux with `python3 tools/build_native.py --jobs 3` or Android ARM64 with `python3 tools/build_android.py --jobs 3`. The original archive stays unchanged; game data is never included in the Linux package or APK.

A portable Linux package starts with `./Start.sh`; import your archive when prompted. Maximum Tune uses its original `A/` and `Data/` directories. Connect a controller; Back/Select inserts a coin and Start begins. Ghost Squad also accepts mouse/touch aiming. These controls still need gameplay validation.

See [port status](PORT_STATUS.md) and [renderer validation](docs/renderer-fix-2026-10-24.md).
