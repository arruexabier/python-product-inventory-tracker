#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "Creating Python environment..."
    python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install -r requirements.txt
python main.py run "$@"
