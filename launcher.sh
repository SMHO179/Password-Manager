#!/usr/bin/env bash
# Personal launcher: run main_gui.py inside the project's .venv
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

if [ ! -x "$VENV/bin/python" ]; then
    echo "error: virtualenv not found at $VENV" >&2
    exit 1
fi

if [ ! -f "$DIR/main_gui.py" ]; then
    echo "error: main_gui.py not found in $DIR" >&2
    exit 1
fi

cd "$DIR"
exec "$VENV/bin/python" main_gui.py "$@"
