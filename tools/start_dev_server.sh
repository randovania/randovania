#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

source .venv/bin/activate
python -m run randovania --configuration tools/dev-server-configuration.json server flask --mode dev
