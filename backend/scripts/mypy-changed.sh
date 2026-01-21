#!/usr/bin/env bash
set -euo pipefail

base_ref="${MYPY_BASELINE_REF:-origin/main}"
if ! git rev-parse --verify "$base_ref" >/dev/null 2>&1; then
  mypy src
  exit 0
fi

files=$(git diff --name-only "$base_ref"...HEAD -- 'backend/src/**/*.py')
if [ -z "$files" ]; then
  echo "mypy: no changed python files"
  exit 0
fi

mypy $files
