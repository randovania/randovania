#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

source venv/bin/activate
export FLASK_DEBUG=1
python -m randovania --configuration tools/dev-server-configuration.json server flask
