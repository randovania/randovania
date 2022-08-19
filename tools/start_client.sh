#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

source venv/Scripts/activate
python setup.py build_ui
python -m randovania gui --preview main
