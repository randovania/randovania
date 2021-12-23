#!/usr/bin/env bash

set -e -x -v

pip install --no-cache-dir -e .[test] -c requirements.txt
python -m pytest test/server -p no:pytest-qt --skip-gui-tests --skip-echo-tool