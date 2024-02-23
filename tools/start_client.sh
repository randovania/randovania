#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

export RANDOVANIA_SKIP_COMPILE=1

source venv/bin/activate
python setup.py build_ui
python -m randovania gui main
