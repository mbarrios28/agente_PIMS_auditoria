#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    printf '%s\n' 'Prepara el entorno primero:' '  python3 -m venv .venv' '  .venv/bin/python -m pip install -r requirements.txt'
    exit 1
fi
exec .venv/bin/python web_app.py
