#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

source venv/bin/activate
python setup.py build_ui
python -m randovania gui --preview main
