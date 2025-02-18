#!/usr/bin/env bash

set -e -x -v

uv sync --extra test
uv run pytest test/server -p no:pytest-qt -p no:pytest-xdist --skip-gui-tests --skip-echo-tool
