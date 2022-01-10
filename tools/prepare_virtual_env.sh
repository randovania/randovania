#!/usr/bin/env bash

set -e -x
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.."

python3.9 tools/test_py_version.py

python3.9 -m venv venv
source venv/bin/activate
python -m pip install --upgrade -r requirements-setuptools.txt
python -m pip install --upgrade -r requirements-small.txt
python -m pip install -e . -e ".[gui]"

echo "Setup finished successfully."
