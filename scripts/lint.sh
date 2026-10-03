#!/bin/sh
# Lint e tipos: mesmos argv de loop.yaml (ruff check; mypy --pretty --show-error-codes --ignore-missing-imports).
set -eu

if [ "$#" -eq 0 ]; then
  ruff check .
  mypy --pretty --show-error-codes --ignore-missing-imports .
else
  ruff check "$@"
  mypy --pretty --show-error-codes --ignore-missing-imports "$@"
fi
