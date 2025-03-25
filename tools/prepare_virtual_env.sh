#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

if ! which uv > /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
uv run tools/prepare_virtual_env.py "$@"
