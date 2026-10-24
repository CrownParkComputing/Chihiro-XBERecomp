#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = "--frontend" ]; then
    shift
    exec python3 tools/frontend.py "$@"
fi
if [ "$#" -eq 0 ] && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && command -v zenity >/dev/null 2>&1; then
    exec python3 tools/frontend.py
fi
exec python3 tools/run_game.py "$@"
