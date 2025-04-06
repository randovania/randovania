#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

export FLASK_DEBUG=1
uv run randovania --configuration tools/dev-server-configuration.json server flask
