#!/bin/sh
# Contrôle qualité en une commande : style (ruff) + tests (pytest) + vérif réseau (check.py).
set -e
cd "$(dirname "$0")"
.venv/bin/ruff check .
.venv/bin/pytest -q
.venv/bin/python check.py
